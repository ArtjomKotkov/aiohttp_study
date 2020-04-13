import sqlalchemy as sa

metadata = sa.MetaData()

users = sa.Table('users', metadata,
                 sa.Column('name', sa.String(length=30), primary_key=True),
                 sa.Column('password', sa.String)
                 )