import sqlalchemy as sa
import datetime

from settings import META_DATA

art = sa.Table('art', META_DATA,
               sa.Column('id', sa.Integer, primary_key=True),
               sa.Column('name', sa.String),
               sa.Column('description', sa.String(length=300), nullable=True),
               sa.Column('path', sa.String),
               sa.Column('likes', sa.Integer, default=0),
               sa.Column('views', sa.Integer, default=0),
               sa.Column('date', sa.DateTime, default=datetime.datetime.now()))

comment = sa.Table('comment', META_DATA,
                   sa.Column('id', sa.Integer, primary_key=True),
                   sa.Column('author', sa.String(length=30)),
                   sa.Column('art_id', sa.Integer, nullable=True),
                   sa.Column('comment_id', sa.Integer, nullable=True),
                   sa.Column('text', sa.String))

tag = sa.Table('tag', META_DATA,
               sa.Column('name', sa.String(30), primary_key=True))

tag_art = sa.Table('tag_art', META_DATA,
                   sa.Column('art_id', sa.Integer, sa.ForeignKey('art.id', ondelete='NO ACTION')),
                   sa.Column('tag_name', sa.String(30), sa.ForeignKey('tag.name', ondelete='NO ACTION')))