import logging

from sqlalchemy import create_engine, MetaData

from setting import load_config
from main_app.models import *
from user_app.models import *

DSN = create_engine(load_config()['postgres']['DSN'].format(**load_config()['postgres']),
                    echo=True)


def create_tables(engine):
    MetaData().create_all(bind=engine, tables=[users, screenshots])


def put_some_data(engine):
    conn = engine.connect()
    conn.close()


if __name__ == '__main__':
    create_tables(DSN)
