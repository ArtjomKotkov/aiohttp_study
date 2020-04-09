from sqlalchemy import create_engine, MetaData
import pprint

from setting import load_config
from main_app.models import user, screenshot

engine_ = create_engine('postgresql://{user}:{password}@{host}:{port}/{database}'.format(**load_config()['postgres']),
                        echo=True)


def create_tables(engine):
    MetaData().create_all(bind=engine, tables=[user, screenshot])


def put_some_data(engine):
    conn = engine.connect()
    conn.execute(user.insert(), {'name': 'test1'}, {'name': 'test2'}, {'name': 'test3'})
    conn.close()


if __name__ == '__main__':
    create_tables(engine_)
    put_some_data(engine_)
