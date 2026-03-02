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


# product/catalog helpers --------------------------------------------------

def _product_to_dict(p):
    """serialize a Produit ORM instance to a plain dict"""
    return {
        'id': p.id,
        'nom': p.nom,
        'description': p.description,
        'categorie': p.categorie,
        'prix': p.prix,
        'quantite_stock': p.quantite_stock,
        'date_creation': p.date_creation.isoformat() if getattr(p, 'date_creation', None) else None
    }


def load_products_from_db(category=None, search=None):
    """Return a list of products optionally filtered by category or search term.

    Visitors and clients will call this to browse the full catalogue.
    """
    query = session.query(Produit)
    if category:
        query = query.filter_by(categorie=category)
    if search:
        # simple case‑insensitive substring search on name/description
        like_term = f"%{search}%"
        query = query.filter(
            Produit.nom.ilike(like_term) | Produit.description.ilike(like_term)
        )
    prods = query.all()
    return [_product_to_dict(p) for p in prods]


def get_product_by_id(product_id):
    p = session.query(Produit).filter_by(id=product_id).first()
    if not p:
        return None
    return _product_to_dict(p)


def add_product_to_db(data):
    """Create a new product entry from a dict and return its serialized form.

    Expected keys: nom, description, categorie, prix, quantite_stock
    """
    # basic field check
    required = {'nom', 'description', 'categorie', 'prix', 'quantite_stock'}
    if not isinstance(data, dict) or not required <= set(data.keys()):
        raise ValueError("Missing product fields")

    # coerce types
    prix = float(data.get('prix'))
    quant = int(data.get('quantite_stock'))

    p = Produit(
        nom=data.get('nom'),
        description=data.get('description'),
        categorie=data.get('categorie'),
        prix=prix,
        quantite_stock=quant
    )
    session.add(p)
    session.commit()
    return _product_to_dict(p)


def update_product_in_db(product_id, data):
    """Update fields of an existing product.

    `data` may contain any of nom, description, categorie, prix, quantite_stock.
    Returns serialized product or None if not found.
    Raises ValueError if payload is invalid.
    """
    if not isinstance(data, dict):
        raise ValueError("Invalid payload")
    p = session.query(Produit).filter_by(id=product_id).first()
    if not p:
        return None
    # update allowed attributes
    if 'nom' in data:
        p.nom = data['nom']
    if 'description' in data:
        p.description = data['description']
    if 'categorie' in data:
        p.categorie = data['categorie']
    if 'prix' in data:
        p.prix = float(data['prix'])
    if 'quantite_stock' in data:
        p.quantite_stock = int(data['quantite_stock'])
    session.add(p)
    session.commit()
    return _product_to_dict(p)


def delete_product_in_db(product_id):
    """Remove a product by id. Returns True if deleted, False if not found."""
    p = session.query(Produit).filter_by(id=product_id).first()
    if not p:
        return False
    session.delete(p)
    session.commit()
    return True


# cart helpers -------------------------------------------------------------

def cart_to_dict(cart):
    lignes = session.query(LignePanier).filter_by(panier_id=cart.id).all()
    return {
        'id': cart.id,
        'utilisateur_id': cart.utilisateur_id,
        'date_creation': cart.date_creation.isoformat() if getattr(cart, 'date_creation', None) else None,
        'lignes': [
            {'id': l.id, 'produit_id': l.produit_id, 'quantite': l.quantite}
            for l in lignes
        ]
    }


def get_or_create_cart(user_id):
    c = session.query(Panier).filter_by(utilisateur_id=user_id).first()
    if c:
        return c
    c = Panier(utilisateur_id=user_id)
    session.add(c)
    session.commit()
    return c


def add_to_cart(user_id, produit_id, quantite):
    if quantite <= 0:
        raise ValueError("Quantity must be positive")
    prod = session.query(Produit).filter_by(id=produit_id).first()
    if not prod:
        raise ValueError("Produit not found")
    cart = get_or_create_cart(user_id)
    line = session.query(LignePanier).filter_by(panier_id=cart.id, produit_id=produit_id).first()
    if line:
        line.quantite += quantite
    else:
        line = LignePanier(panier_id=cart.id, produit_id=produit_id, quantite=quantite)
        session.add(line)
    session.commit()
    return cart_to_dict(cart)

# order helpers ------------------------------------------------------------

def _commande_to_dict(c):
    """serialize a Commande instance, including its lignes."""
    lignes = session.query(LigneCommande).filter_by(commande_id=c.id).all()
    return {
        'id': c.id,
        'utilisateur_id': c.utilisateur_id,
        'adresse_livraison': c.adresse_livraison,
        'date_commande': c.date_commande.isoformat() if getattr(c, 'date_commande', None) else None,
        'statut': c.statut.value if c.statut is not None else None,
        'lignes': [
            {
                'id': l.id,
                'produit_id': l.produit_id,
                'quantite': l.quantite,
                'prix_unitaire': l.prix_unitaire
            } for l in lignes
        ]
    }


def create_order(user_id, adresse_livraison, lignes):
    """Create a Commande and associated LigneCommande records.

    `user_id` should be a string or int; `lignes` is a list of dicts with
    produit_id and quantite.  Returns serialized commande.
    Raises ValueError on bad payload or if the user cannot be found.
    """
    # verify target user exists
    try:
        uid_int = int(user_id)
    except Exception:
        raise ValueError("Invalid utilisateur_id")
    user = session.query(Utilisateur).filter_by(id=uid_int).first()
    if not user:
        raise ValueError("Utilisateur not found")

    if not adresse_livraison or not isinstance(lignes, list) or len(lignes) == 0:
        raise ValueError("Invalid order data")
    c = Commande(
        utilisateur_id=uid_int,
        adresse_livraison=adresse_livraison,
        statut=StatutType.EN_ATTENTE
    )
    session.add(c)
    session.commit()  # flush to get c.id

    for item in lignes:
        if not isinstance(item, dict) or 'produit_id' not in item or 'quantite' not in item:
            raise ValueError("Invalid ligne")
        prod = session.query(Produit).filter_by(id=item['produit_id']).first()
        if not prod:
            raise ValueError(f"Produit {item['produit_id']} not found")
        quant = int(item['quantite'])
        lc = LigneCommande(
            commande_id=c.id,
            produit_id=prod.id,
            quantite=quant,
            prix_unitaire=prod.prix
        )
        session.add(lc)
    session.commit()
    return _commande_to_dict(c)


def update_user_address(user_id, adresse):
    """Set the delivery address for a user, return serialized user or None."""
    if not adresse or not isinstance(adresse, str):
        raise ValueError("Invalid address")
    u = session.query(Utilisateur).filter_by(id=user_id).first()
    if not u:
        return None
    u.adresse_livraison = adresse
    session.add(u)
    session.commit()
    return {
        'id': u.id,
        'email': u.email,
        'nom': u.nom,
        'role': u.role.value if u.role is not None else None,
        'adresse_livraison': u.adresse_livraison,
        'date_creation': u.date_creation.isoformat() if getattr(u, 'date_creation', None) else None
    }


def load_orders_for_user(user_id):
    """Return list of orders belonging to given user."""
    cmds = session.query(Commande).filter_by(utilisateur_id=user_id).all()
    return [_commande_to_dict(c) for c in cmds]


def load_all_orders():
    """Return all orders in the system."""
    cmds = session.query(Commande).all()
    return [_commande_to_dict(c) for c in cmds]


def get_order_by_id(order_id):
    """Return serialized order or None if not found."""
    c = session.query(Commande).filter_by(id=order_id).first()
    if not c:
        return None
    return _commande_to_dict(c)


def update_order_status(order_id, statut_value):
    """Change the statut of a command and return serialized order.

    `statut_value` should be one of the StatutType values (string or enum).
    Returns None if order not found; raises ValueError for invalid statut.
    """
    c = session.query(Commande).filter_by(id=order_id).first()
    if not c:
        return None
    try:
        if isinstance(statut_value, StatutType):
            new_stat = statut_value
        else:
            new_stat = StatutType(statut_value)
    except Exception:
        raise ValueError("Invalid statut")
    c.statut = new_stat
    session.add(c)
    session.commit()
    return _commande_to_dict(c)
