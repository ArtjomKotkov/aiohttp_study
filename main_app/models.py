import logging

from sqlalchemy import Table, Column, Integer, String, MetaData, ForeignKey, Boolean

meta = MetaData()

users = Table(
    'users', meta,
    Column('id', Integer, primary_key=True),
    Column('name', String),
    Column('is_admin', Boolean, default=False)
)

screenshot = Table(
    'screenshots', meta,
    Column('id', Integer, primary_key=True),
    Column('user_id', Integer, ForeignKey('users.id', ondelete='CASCADE')),
    Column('name', String)
)
