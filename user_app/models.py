import sqlalchemy as sa

from settings import META_DATA

users = sa.Table('users', META_DATA,
                 sa.Column('name', sa.String(length=30), primary_key=True),
                 sa.Column('password', sa.String)
                 )