import os
from sqlalchemy.orm import sessionmaker,declarative_base
from orm import *

if os.path.exists('digimarket.db'):
   os.remove('digimarket.db')

# Création d'une connexion à la base de données SQLite
# Le prefix "sqlite:///" indique qu'on utilise SQLite et qu'il s'agit d'un chemin absolu
engine = create_engine('sqlite:///digimarket.db', echo=False)
Base.metadata.create_all(engine)

# Déclaration de la base qui servira à créer les modèles
Base = declarative_base()

# Session
Session = sessionmaker(bind=engine)
session = Session()


def run_data():
   # insertion users
   user1 = Utilisateur(email="j@doe.com", mot_de_passe="jdoe", nom="john doe", role=RoleType.CLIENT)
   user2 = Utilisateur(email="l@messi.com", mot_de_passe="lmessi", nom="Lionel Messi", role=RoleType.CLIENT)
   session.add_all([user1, user2])
   session.commit()

   users = session.query(Utilisateur).all()
   print("\n Tous les users:")
   for user in users:
       print(user)
 
   # Récupérer un user spécifique
   specific_user = session.query(Utilisateur).filter_by(email='l@messi.com').first()
   print("\n Utilisateur spécifique:")
   print(specific_user)

   # insertion produits
   produit1 = Produit(nom="derby", description="ceci est une chaussure", categorie="chaussure", prix=24.99, quantite_stock=12)
   produit2 = Produit(nom="huile", description="ceci est une huile", categorie="alimentaire", prix=2.99, quantite_stock=23)

   session.add_all([produit1, produit2])
   session.commit()

   # Récupérer tous les produits
   produits = session.query(Produit).all()
   print("\n Tous les produits:")
   for item in produits:
       print(item)

   # insertion commandes
   commande1 = Commande(utilisateur_id=user1.id, adresse_livraison="Lyon", statut=StatutType.EN_ATTENTE)
   commande2 = Commande(utilisateur_id=user2.id, adresse_livraison="Marseille", statut=StatutType.VALIDEE)
   session.add_all([commande1, commande2])
   session.commit()

   # Récupérer commande
   commandes = session.query(Commande).all()
   print("\n Toutes les commandes:")
   for item in commandes:
       print(item)

   # insertion de lignes commandes
   lc1 = LigneCommande(commande_id=commande1.id, produit_id=produit1.id, quantite=133, prix_unitaire=12.8)
   lc2 = LigneCommande(commande_id=commande2.id, produit_id=produit2.id, quantite=673, prix_unitaire=12.99)
   session.add_all([lc1, lc2])
   session.commit()

   # Récupérer commande
   lignes_commandes = session.query(LigneCommande).all()
   print("\n Toutes les commandes:")
   for item in lignes_commandes:
       print(item)

run_data()