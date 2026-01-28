from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

ENGINE = create_engine("sqlite:///gameserver.db")

def make_session():
    return sessionmaker(bind=ENGINE)()