import logging

from sqlalchemy import create_engine, MetaData

from settings import load_config
from user_app.models import *
from content.models import *

DSN = create_engine(load_config()['postgres']['DSN'].format(**load_config()['postgres']),
                    echo=True)


def create_tables(engine):
    MetaData().drop_all(bind=engine,
                          tables=[groups, users_subscribers, groups_users, art, comment, tag, tag_art])
    MetaData().create_all(bind=engine,
                          tables=[users, groups, users_subscribers, groups_users, art, comment, tag, tag_art])


def put_some_data(engine):
    conn = engine.connect()
    conn.execute(users.insert(), [
        dict(name='Artem', password='190898'),
        dict(name='Sonya', password='190898')
    ])
    conn.close()


if __name__ == '__main__':

    create_tables(DSN)
