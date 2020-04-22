import sqlalchemy as sa

from settings import META_DATA

users = sa.Table('users', META_DATA,
                 sa.Column('name', sa.String(length=30), primary_key=True),
                 sa.Column('password', sa.String),
                 sa.Column('grand', sa.BOOLEAN),
                 )


users_subscribers = sa.Table(
    'users_subscribers', META_DATA,
    sa.Column('owner_name', sa.String(length=30), sa.ForeignKey('users.name', ondelete='CASCADE')),
    sa.Column('subscriber_name', sa.String(length=30), sa.ForeignKey('users.name', ondelete='CASCADE'))
)

groups = sa.Table('role', META_DATA,
                  sa.Column('name', sa.String(length=40), primary_key=True),
                  sa.Column('level', sa.Integer)
                  )

groups_users = sa.Table(
    'role_users', META_DATA,
    sa.Column('role_name', sa.String(length=40), sa.ForeignKey('role.name', ondelete='CASCADE')),
    sa.Column('user_name', sa.String(length=30), sa.ForeignKey('users.name', ondelete='CASCADE'))
)