from sqlalchemy import Table, Column, Integer, String, MetaData, ForeignKey

user = Table(
    'user', MetaData(),
     Column('id', Integer, primary_key=True),
     Column('name', String)
)

screenshot = Table(
    'screenshot', MetaData(),
    Column('id', Integer, primary_key=True),
    Column('user_id', ForeignKey('user.id', ondelete='CASCADE'))
)


