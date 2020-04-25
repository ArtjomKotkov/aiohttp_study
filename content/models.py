import sqlalchemy as sa
import datetime

from settings import META_DATA

art = sa.Table('art', META_DATA,
               sa.Column('id', sa.Integer, primary_key=True),
               sa.Column('name', sa.String, nullable=False),
               sa.Column('description', sa.String(length=300), nullable=True),
               sa.Column('path', sa.String, nullable=False),
               sa.Column('likes', sa.Integer, nullable=False),
               sa.Column('views', sa.Integer, nullable=False),
               sa.Column('date', sa.DateTime, nullable=False),
               sa.Column('owner', sa.String(length=30), sa.ForeignKey('users.name', ondelete='CASCADE'), nullable=False))

comment = sa.Table('comment', META_DATA,
                   sa.Column('id', sa.Integer, primary_key=True),
                   sa.Column('author', sa.String(length=30), nullable=False),
                   sa.Column('art_id', sa.Integer, sa.ForeignKey('art.id', ondelete='CASCADE'), nullable=False),
                   sa.Column('comment_id', sa.Integer, nullable=True),
                   sa.Column('text', sa.String, nullable=False))

tag = sa.Table('tag', META_DATA,
               sa.Column('id', sa.Integer, primary_key=True),
               sa.Column('name', sa.String(30)))

tag_art = sa.Table('tag_art', META_DATA,
                   sa.Column('art_id', sa.Integer, sa.ForeignKey('art.id', ondelete='CASCADE')),
                   sa.Column('tag_id', sa.Integer, sa.ForeignKey('tag.id', ondelete='CASCADE')))