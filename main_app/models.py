import logging

from sqlalchemy import Table, Column, Integer, String, MetaData, ForeignKey, Boolean

from settings import META_DATA

meta = MetaData()

screenshots = Table(
    'screenshots', META_DATA,
    Column('id', Integer, primary_key=True),
    Column('user', String(length=30), ForeignKey('users.name', ondelete='CASCADE')),
    Column('name', String)
)
