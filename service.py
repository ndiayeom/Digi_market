import os
import jwt
from datetime import datetime, timedelta
from sqlalchemy.orm import sessionmaker,declarative_base
from werkzeug.security import generate_password_hash, check_password_hash
from orm import *

#if os.path.exists('digimarket.db'):
#  os.remove('digimarket.db')

# Création d'une connexion à la base de données SQLite
# Le prefix "sqlite:///" indique qu'on utilise SQLite et qu'il s'agit d'un chemin absolu
engine = create_engine('sqlite:///digimarket.db', echo=False)
Base.metadata.create_all(engine)

# Déclaration de la base qui servira à créer les modèles
Base = declarative_base()

# Session
Session = sessionmaker(bind=engine)
session = Session()


def add_user_to_db(user):
   # create Utilisateur instance from dict and insert
   if isinstance(user, dict):
      role_value = user.get('role')
      try:
         role_enum = RoleType(role_value)
      except Exception:
         role_enum = None
      # hash password before storing
      raw_pw = user.get('mot_de_passe')
      hashed_pw = generate_password_hash(raw_pw) if raw_pw is not None else None

      u = Utilisateur(
         email=user.get('email'),
         mot_de_passe=hashed_pw,
         nom=user.get('nom'),
         role=role_enum
      )
      session.add(u)
      session.commit()
      return u
   else:
      session.add(user)
      session.commit()
      return user

def load_users_from_db():
   users = session.query(Utilisateur).all()
   # convert ORM objects to serializable dicts
   result = []
   for u in users:
      result.append({
         'id': u.id,
         'email': u.email,
         'nom': u.nom,
         'role': u.role.value if u.role is not None else None,
         'date_creation': u.date_creation.isoformat() if getattr(u, 'date_creation', None) else None
      })
   return result


def authenticate_user(email, mot_de_passe):
   user = session.query(Utilisateur).filter_by(email=email).first()
   if not user:
      return None
   # First try verifying as hashed password
   try:
      if user.mot_de_passe and check_password_hash(user.mot_de_passe, mot_de_passe):
         pass
      else:
         # fallback: if stored password is plaintext, compare and migrate to hashed
         if user.mot_de_passe == mot_de_passe:
            user.mot_de_passe = generate_password_hash(mot_de_passe)
            session.add(user)
            session.commit()
         else:
            return None
   except Exception:
      # on any verification error, deny access
      return None
   return {
      'id': user.id,
      'email': user.email,
      'nom': user.nom,
      'role': user.role.value if user.role is not None else None,
      'date_creation': user.date_creation.isoformat() if getattr(user, 'date_creation', None) else None
   }


# JWT helpers
SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret')

def create_access_token(user_id, role, expires_minutes=60, secret=None):
   key = secret or SECRET_KEY
   now = datetime.utcnow()
   exp = now + timedelta(minutes=expires_minutes)
   payload = {
      'sub': str(user_id),
      'role': role,
      'iat': int(now.timestamp()),
      'exp': int(exp.timestamp())
   }
   token = jwt.encode(payload, key, algorithm='HS256')
   if isinstance(token, bytes):
      token = token.decode('utf-8')
   return token


def verify_access_token(token, secret=None):
   key = secret or SECRET_KEY
   try:
      # allow small clock skew (leeway) to tolerate minor time differences
      payload = jwt.decode(token, key, algorithms=['HS256'], leeway=30)
      return payload
   except jwt.ExpiredSignatureError:
      print('JWT verification failed: token expired')
      return None
   except jwt.InvalidTokenError as e:
      print('JWT verification failed:', str(e))
      return None


def create_refresh_token(user_id, role, expires_days=7, secret=None):
   key = secret or SECRET_KEY
   now = datetime.utcnow()
   exp = now + timedelta(days=expires_days)
   payload = {
      'sub': str(user_id),
      'role': role,
      'type': 'refresh',
      'iat': int(now.timestamp()),
      'exp': int(exp.timestamp())
   }
   token = jwt.encode(payload, key, algorithm='HS256')
   if isinstance(token, bytes):
      token = token.decode('utf-8')
   return token


def verify_refresh_token(token, secret=None):
   key = secret or SECRET_KEY
   try:
      payload = jwt.decode(token, key, algorithms=['HS256'], leeway=30)
      if payload.get('type') != 'refresh':
         print('JWT refresh verification failed: token type invalid')
         return None
      return payload
   except jwt.ExpiredSignatureError:
      print('JWT refresh verification failed: token expired')
      return None
   except jwt.InvalidTokenError as e:
      print('JWT refresh verification failed:', str(e))
      return None
