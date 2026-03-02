import os

from sqlalchemy import create_engine, Column, Integer, String, Float, Text, ForeignKey, Enum, DateTime
from sqlalchemy.orm import declarative_base, relationship
from enum import Enum as PyEnum
from datetime import datetime


# Déclaration de la base qui servira à créer les modèles
Base = declarative_base()

class RoleType(PyEnum):
   CLIENT = "client"
   ADMIN = "admin"

class StatutType(PyEnum):
   EN_ATTENTE = "en_attente"
   VALIDEE = "validee"
   EXPEDIEE = "expédiee"
   ANNULEE = "annulee"


# Définition des modèles
class Utilisateur(Base):
   __tablename__ = 'utilisateur'
 
   id = Column(Integer, primary_key=True)
   email = Column(String, nullable=False, unique=True)
   mot_de_passe = Column(String, nullable=False)
   nom = Column(String, nullable=False)
   role = Column(Enum(RoleType, name='role'), nullable=False)
   adresse_livraison = Column(String, nullable=True)
   date_creation = Column(DateTime, default=datetime.now)


   def __repr__(self):
       return f"<Utilisateur(id='{self.id}', email='{self.email}'email='{self.email}', nom='{self.nom}'), role='{self.role}')>"


class Produit(Base):
   __tablename__ = 'produit'
  
   id = Column(Integer, primary_key=True)
   nom = Column(String, nullable=False)
   description = Column(Text)
   categorie = Column(String, nullable=False)
   prix = Column(Float, nullable=False)
   quantite_stock = Column(Integer, default=0)
   date_creation = Column(DateTime, default=datetime.now)


   def __repr__(self):
       return f"<Produit(id='{self.id}', nom='{self.nom}', description='{self.description}', categorie='{self.categorie}', prix='{self.prix}', quantite_stock='{self.quantite_stock}')>"

class Commande(Base):
   __tablename__ = 'commande'
  
   id = Column(Integer, primary_key=True)
   utilisateur_id = Column(Integer,ForeignKey("utilisateur.id"),nullable=False)
   adresse_livraison = Column(String, nullable=False)
   date_commande = Column(DateTime, default=datetime.now)
   statut = Column(Enum(StatutType, name='statut'), nullable=False)


   def __repr__(self):
       return f"<Commande(id='{self.id}', utilisateur='{self.utilisateur_id}', adresse de livraison='{self.adresse_livraison}', statut='{self.statut}')>"


class LigneCommande(Base):
   __tablename__ = 'ligne_commande'
  
   id = Column(Integer, primary_key=True)
   commande_id = Column(Integer,ForeignKey("commande.id"), nullable=False)
   produit_id = Column(Integer,ForeignKey("produit.id"), nullable=False)
   quantite = Column(Integer, nullable=False)
   prix_unitaire = Column(Float, nullable=False)


   def __repr__(self):
       return f"<LigneCommande(id='{self.id}', commande_id='{self.commande_id}',produit_id='{self.produit_id}', quantite='{self.quantite}', prix_unitaire='{self.prix_unitaire}')>"


# top-level cart models for convenience (duplicate of nested definitions)
class Panier(Base):
   __tablename__ = 'panier'

   id = Column(Integer, primary_key=True)
   utilisateur_id = Column(Integer, ForeignKey('utilisateur.id'), nullable=False)
   date_creation = Column(DateTime, default=datetime.now)

   def __repr__(self):
      return f"<Panier(id='{self.id}', utilisateur_id='{self.utilisateur_id}', date_creation='{self.date_creation}')>"


class LignePanier(Base):
   __tablename__ = 'ligne_panier'

   id = Column(Integer, primary_key=True)
   panier_id = Column(Integer, ForeignKey('panier.id'), nullable=False)
   produit_id = Column(Integer, ForeignKey('produit.id'), nullable=False)
   quantite = Column(Integer, nullable=False)

   def __repr__(self):
      return f"<LignePanier(id='{self.id}', panier_id='{self.panier_id}', produit_id='{self.produit_id}', quantite='{self.quantite}')>"