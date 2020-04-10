import logging

from sqlalchemy import create_engine, MetaData

from setting import load_config
from main_app.models import users, screenshot

DSN = create_engine(load_config()['postgres']['DSN'].format(**load_config()['postgres']),
                    echo=True)


def create_tables(engine):
    MetaData().create_all(bind=engine, tables=[users, screenshot])


def put_some_data(engine):
    conn = engine.connect()
    conn.execute(screenshot.insert(), dict(name='test_photo1', user_id='1'), dict(name='test_photo2', user_id='1'))
    conn.close()


if __name__ == '__main__':
    create_tables(DSN)
    put_some_data(DSN)
