from sqlalchemy.orm import declarative_base
from sqlalchemy import create_engine

engine = create_engine('sqlite:///digimarket.db')
Base = declarative_base()

# Avant create_all()
Base.metadata.drop_all(engine)
Base.metadata.create_all(engine)