from sqlalchemy import create_engine, sessionmaker, MetaData()

from .setting import load_config
from main_app.models import user, screenshot


engine = create_engine('postgresql://{user}:{password}@{host}:{port}/{database}', echo=True)

def create_tables(engine):
    MetaData().create_all(bind=engine, tables=[user, screenshot])
