import json
import io
import datetime

import pytest
import asyncpg
from aiohttp import web, MultipartWriter
from sqlalchemy import create_engine, MetaData

from user_app.models import users, groups, users_subscribers, groups_users
from content.models import art, comment, tag, tag_art

from user_app.views import Roles, Role, RoleMembers
from content.views import FileManager, FilesManager, Tag, Tags


# Creating tables in test database.
@pytest.fixture
def create_tables():
    engine = create_engine('postgresql://saint:190898@localhost:5432/tests')
    MetaData().create_all(bind=engine,
                          tables=[users, groups, users_subscribers, groups_users, art, comment, tag, tag_art])


# Creating client instance in test database, and 'db' port for connection to database.
@pytest.yield_fixture
async def app(create_tables, aiohttp_server, aiohttp_client):
    app = web.Application()
    app.router.add_view('/role', Roles)
    app.router.add_view('/role/{id}', Role)
    app.router.add_view('/role/member/{id}', RoleMembers)
    app.router.add_view('/art', FilesManager)
    app.router.add_view('/art/{id}', FileManager)
    app.router.add_view('/tag', Tags)
    app.router.add_view('/tag/{id}', Tag)
    app['db'] = await asyncpg.create_pool('postgresql://saint:190898@localhost:5432/tests')
    server = await aiohttp_server(app)
    client = await aiohttp_client(server)
    try:
        yield dict(client=client, db=app['db'])
    finally:
        engine = create_engine('postgresql://saint:190898@localhost:5432/tests')
        MetaData().drop_all(bind=engine,
                            tables=[users, groups, users_subscribers, groups_users, art, comment, tag, tag_art])


# Roles tests.

@pytest.fixture
async def role_test_data(app):
    test_data = [{"name": 'admin', 'level': 10}, {"name": 'moderator', 'level': 9}]
    async with app['db'].acquire() as conn:
        await conn.execute('INSERT INTO role (name, level) VALUES ($1, $2), ($3, $4);', test_data[0]['name'],
                           test_data[0]['level'], test_data[1]['name'], test_data[1]['level'])
        await conn.close()
    return test_data


# URL /role tests:
async def test_roles_post(app):
    test_data = {"name": 'admin', 'level': 10}
    response = await app['client'].post('/role', data=test_data)
    assert response.status == 201
    async with app['db'].acquire() as conn:
        check_row = await conn.fetchrow('SELECT * FROM role WHERE name = $1;', test_data['name'])
        await conn.close()
    assert check_row is not None
    assert check_row['level'] == test_data['level']


async def test_roles_get(app, role_test_data):
    response = await app['client'].get('/role')
    data = await response.json()
    assert len(data['items']) == 2


# URL /role/{id} tests:
async def test_role_get(app, role_test_data):
    response = await app['client'].get('/role/5')
    assert response.status == 404
    response = await app['client'].get('/role/1')
    assert response.status == 200
    data = await response.json()
    assert data['items'][0]['name'] == 'admin'


async def test_role_put(app, role_test_data):
    # Update all fields.
    new_data = {"name": 'admins', 'level': 11}
    response = await app['client'].put('/role/1', json=new_data)
    assert response.status == 200
    data = await response.json()
    assert data['items'][0]['name'] == new_data['name']
    assert data['items'][0]['level'] == new_data['level']
    async with app['db'].acquire() as conn:
        check_row = await conn.fetchrow('SELECT * FROM role WHERE id = $1;', 1)
        await conn.close()
    assert check_row is not None
    # Update only level.
    new_data = {'level': 7}
    response = await app['client'].put('/role/2', json=new_data)
    assert response.status == 200
    data = await response.json()
    assert data['items'][0]['name'] == 'moderator'
    assert data['items'][0]['level'] == new_data['level']
    async with app['db'].acquire() as conn:
        check_row = await conn.fetchrow('SELECT * FROM role WHERE id = $1;', 2)
        await conn.close()
    assert check_row is not None
    assert check_row['name'] == 'moderator'
    assert check_row['level'] == 7


async def test_role_delete(app, role_test_data):
    response = await app['client'].delete('/role/1')
    assert response.status == 200
    async with app['db'].acquire() as conn:
        check_rows = await conn.fetch("SELECT * FROM role;")
        await conn.close()
    assert len(check_rows) == 1


# URL /role/member/{id} tests:

@pytest.fixture
async def role_members_test_data(app):
    role_test_data = [{"name": 'admin', 'level': 10}, {"name": 'moderator', 'level': 9}]
    user_test_data = {'name': 'test', 'password': 'test_password'}
    async with app['db'].acquire() as conn:
        await conn.execute('INSERT INTO role (name, level) VALUES ($1, $2), ($3, $4);', role_test_data[0]['name'],
                           role_test_data[0]['level'], role_test_data[1]['name'], role_test_data[1]['level'])
        await conn.execute('INSERT INTO users (name, password) VALUES ($1, $2);', user_test_data['name'],
                           user_test_data['password'])
        await conn.execute('INSERT INTO role_users (role_id, user_name) VALUES ($1, $2);', 1, user_test_data['name'])
        await conn.close()
    test_data = dict(
        role=role_test_data,
        user=user_test_data
    )
    return test_data


async def test_role_members_post(app, role_members_test_data):
    test_data = dict(name=role_members_test_data['user']['name'])
    response = await app['client'].post('/role/member/2', json=test_data)
    assert response.status == 201
    async with app['db'].acquire() as conn:
        check_row = await conn.fetch('SELECT * FROM role_users WHERE user_name = $1;',
                                     role_members_test_data['user']['name'])
        await conn.close()
    assert len(check_row) == 2
    response = await app['client'].post('/role/member/1', json=test_data)
    assert response.status == 409


async def test_role_members_delete(app, role_members_test_data):
    test_data = dict(name=role_members_test_data['user']['name'])
    response = await app['client'].delete('/role/member/1', json=test_data)
    assert response.status == 200
    async with app['db'].acquire() as conn:
        check_row = await conn.fetch('SELECT * FROM role_users WHERE user_name = $1;',
                                     role_members_test_data['user']['name'])
        await conn.close()
    assert len(check_row) == 0


# Arts tests.

@pytest.fixture
async def art_test_data(app):
    test_data = {"name": 'test', 'path': 'testing', 'user': 'Gold'}
    async with app['db'].acquire() as conn:
        await conn.execute('INSERT INTO users (name, password) VALUES ($1, $2);', 'Gold', 'Test')
        await conn.execute('INSERT INTO users (name, password) VALUES ($1, $2);', 'Artem', 'Test')
        for i in range(40):
            datetime_ = datetime.datetime.now()
            await conn.execute("""INSERT INTO art (name, description, path, date, owner, likes, views) 
                                      VALUES ($1, $2, $3, $4, $5, $6, $7);""", test_data['name'], None,
                               test_data['path'], datetime_,
                               test_data['user'], 0, 0)
        for i in range(3):
            await conn.execute('INSERT INTO tag (name) VALUES ($1);', f'test_tag{i+1}')
        for i in range(5):
            await conn.execute("INSERT INTO tag_art (art_id, tag_id) VALUES ($1, $2);", i+1, 1)
        for i in range(6):
            await conn.execute("INSERT INTO tag_art (art_id, tag_id) VALUES ($1, $2);", i+1, 2)
        for i in range(7):
            await conn.execute("INSERT INTO tag_art (art_id, tag_id) VALUES ($1, $2);", i+1, 3)
        await conn.close()
    return test_data


# async def test_arts_post(app):
#
#     with open('test.png', 'rb') as file:
#         with MultipartWriter('mixed') as mpwriter:
#             test_data_form = [('name', 'test'), ('description', 'test2'), ('user', 'Artem')]
#             mpwriter.append_form(test_data_form)
#             part = mpwriter.append(file)
#             part.set_content_disposition('file', filename=file.name)
#             print(mpwriter)
#         print(mpwriter)
#         response = await app['client'].post('/art', data=mpwriter)
#         assert response.status == 201

async def test_arts_get(app, art_test_data):
    response = await app['client'].get('/art?limit=20')
    data = await response.json()
    assert len(data['items']) == 20

async def extended_test_arts_get(app, art_test_data):
    response = await app['client'].get('/art?limit=20&tags=test_tag1,test_tag2')
    data = await response.json()
    assert len(data['items']) == 6

async def test_art_get(app, art_test_data):
    response = await app['client'].get('/art/1')
    assert response.status == 200
    data = await response.json()
    async with app['db'].acquire() as conn:
        sql_check = await conn.fetchrow('SELECT * FROM art WHERE id = 1;')
        assert data['items'][0]['name'] == sql_check['name']
        await conn.close()

async def test_art_delete(app, art_test_data):
    response = await app['client'].delete('/art/1')
    assert response.status == 200
    async with app['db'].acquire() as conn:
        sql_check = await conn.fetch('SELECT * from art;')
        assert len(sql_check) == 39
        await conn.close()

async def test_art_put(app, art_test_data):
    new_data = dict(
        name='test2',
        path='tetingasfa'
    )
    response = await app['client'].put('/art/1', json=new_data)
    assert response.status == 200
    async with app['db'].acquire() as conn:
        sql_check = await conn.fetchrow('SELECT * from art WHERE id = 1;')
        assert sql_check['name'] == new_data['name']
        assert sql_check['path'] == new_data['path']
        await conn.close()

# Tag api tests

@pytest.fixture
async def tags_test_data(app):
    test_data = {"name": 'test', 'path': 'testing', 'user': 'Gold'}
    async with app['db'].acquire() as conn:
        await conn.execute('INSERT INTO tag (name) VALUES ($1);', 'test_tag1')
        await conn.execute('INSERT INTO tag (name) VALUES ($1);', 'test_tag2')
        await conn.close()
    return test_data

async def test_tags_get(app, tags_test_data):
    response = await app['client'].get('/tag')
    data = await response.json()
    assert len(data['items']) == 2

async def test_tags_post(app, tags_test_data):
    test_data = dict(name='test3')
    response = await app['client'].post('/tag', json=test_data)
    data = await response.json()
    async with app['db'].acquire() as conn:
        sql_check = await conn.fetch('SELECT * FROM tag;')
        assert len(sql_check) == 3
        sql_check = await conn.fetchrow('SELECT * FROM tag WHERE id = 3;')
        assert sql_check['name'] == 'test3'


async def test_tag_get(app, tags_test_data):
    response = await app['client'].get('/tag/1')
    data = await response.json()
    assert data['items'][0]['name'] == 'test_tag1'

async def test_tag_put(app, tags_test_data):
    new_data = dict(name='new_name')
    response = await app['client'].put('/tag/1', json=new_data)
    assert response.status == 200
    data = await response.json()
    assert data['items'][0]['name'] == new_data['name']

async def test_tag_delete(app, tags_test_data):
    response = await app['client'].delete('/tag/1')
    assert response.status == 200
    async with app['db'].acquire() as conn:
        sql_check = await conn.fetch('SELECT * FROM tag;')
        assert len(sql_check) == 1

@pytest.fixture
async def tag_test_data(app):
    test_data = {"name": 'test', 'path': 'testing', 'user': 'Gold'}
    async with app['db'].acquire() as conn:
        await conn.execute('INSERT INTO users (name, password) VALUES ($1, $2);', 'Gold', 'Test')
        await conn.execute('INSERT INTO users (name, password) VALUES ($1, $2);', 'Artem', 'Test')
        await conn.execute('INSERT INTO tag (name) VALUES ($1);', 'test_tag1')
        await conn.execute('INSERT INTO tag (name) VALUES ($1);', 'test_tag2')
        for i in range(40):
            datetime_ = datetime.datetime.now()
            await conn.execute("""INSERT INTO art (name, description, path, date, owner, likes, views) 
                                      VALUES ($1, $2, $3, $4, $5, $6, $7);""", test_data['name'], None,
                               test_data['path'], datetime_,
                               test_data['user'], 0, 0)
        await conn.close()
    return test_data