import logging

from sqlalchemy import Table, Column, Integer, String, MetaData, ForeignKey, Boolean

meta = MetaData()

screenshots = Table(
    'screenshots', meta,
    Column('id', Integer, primary_key=True),
    Column('user_id', Integer, ForeignKey('users.id', ondelete='CASCADE')),
    Column('name', String)
)
