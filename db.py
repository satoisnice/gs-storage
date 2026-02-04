import yaml
import logging
import logging.config
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# ENGINE = create_engine("sqlite:///gameserver.db")
# ENGINE = create_engine("mysql+mysqldb://gs_user:computer@127.0.0.1:3306/gameserver")

with open("app_conf.yml", "r") as f:
    app_config = yaml.safe_load(f.read())

ds = app_config["datastore"]
DB_USER = ds["user"]
DB_PASS = ds["password"]
DB_HOST = ds["hostname"]
DB_PORT = ds["port"]
DB_NAME = ds["db"]

DB_URL = f"mysql+mysqldb://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

ENGINE = create_engine(DB_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=ENGINE)

print("DB URL:", ENGINE.url)

def make_session():
    return sessionmaker(bind=ENGINE)()