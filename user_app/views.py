import logging
import json
import os
import datetime

from aiohttp import web
import aiohttp_jinja2
from aiohttp_session import get_session

from settings import MEDIA_ROOT
from .login_manager import hash_password, check_password, login, logout
from .forms import *
from chat.forms import Chat
from .login_manager import Decorator

logger_console = logging.getLogger('console_logger')

routers_user = web.RouteTableDef()


# Main page views

@routers_user.get('/options/')
@aiohttp_jinja2.template('user_app/templates/user_options.html')
@Decorator.method_login_required
async def gallery_page(request):
    pass


@routers_user.get('/{user_name}')
async def user_page(request):
    async with request.app['db'].acquire() as conn:
        user = await conn.fetchrow('SELECT * FROM users WHERE name = $1', request.match_info['user_name'])
        if user is None:
            return web.HTTPNotFound()
        else:
            context = {
                'form': Chat()
            }
            return aiohttp_jinja2.render_template('user_app/templates/user_page.html', request, context)


@routers_user.get('/{user_name}/art/{id}', name='art_instance')
@aiohttp_jinja2.template('user_app/templates/art_instance.html')
async def user_page(request):
    pass


@routers_user.get('/{user_name}/gallery/')
@aiohttp_jinja2.template('user_app/templates/art_gallery.html')
async def gallery_page(request):
    async with request.app['db'].acquire() as conn:
        sql_row = await conn.fetchrow('SELECT * FROM users WHERE name = $1;', request.match_info['user_name'])
    return {'owner': dict(
        name=sql_row['name'],
        photo=sql_row['photo'],
        description=sql_row['description'],
    )}


@routers_user.get('/{user_name}/gallery/{album_id}')
@aiohttp_jinja2.template('user_app/templates/art_gallery_album.html')
async def gallery_album_page(request):
    async with request.app['db'].acquire() as conn:
        sql_row = await conn.fetchrow('SELECT * FROM users WHERE name = $1;', request.match_info['user_name'])
    return {'owner': dict(
        name=sql_row['name'],
        # photo=sql_row['photo']
        # subscribers
        # decription
    ), 'album': request.match_info['album_id']}


@routers_user.view('/register/', name='user_register')
class RegisterView(web.View):
    @aiohttp_jinja2.template('user_app/templates/register.html')
    async def get(self):
        form = Register()
        return {'form': form}

    # async def post(self):
    #     form = Register(await self.request.post())
    #     if form.validate():
    #         async with self.request.app['db'].acquire() as conn:
    #             user = await conn.fetchrow('SELECT * FROM users WHERE name = $1;', form.data['name'])
    #             if user is None:
    #                 await conn.execute('INSERT INTO users (name, password) VALUES ($1, $2);', form.data['name'],
    #                                    hash_password(form.data['password']))
    #                 user = await conn.fetchrow('SELECT * FROM users WHERE name = $1;', form.data['name'])
    #                 await login(self.request, user, timeout=3600)
    #                 raise web.HTTPFound(self.request.app['parent_app'].router['main'].url_for())
    #             else:
    #                 form.name.errors.append('Пользователь с таким именем существует')
    #                 return aiohttp_jinja2.render_template('user_app/templates/register.html', self.request,
    #                                                       {'form': form})


@routers_user.view('/auth/', name='user_auth')
class AuthView(web.View):
    @aiohttp_jinja2.template('user_app/templates/auth.html')
    async def get(self):
        form = Auth()
        return {'form': form}

    async def post(self):
        data = await self.request.post()
        form = Auth(data)
        if form.validate():
            async with self.request.app['db'].acquire() as conn:
                user = await conn.fetchrow('SELECT * FROM users WHERE name = $1;', form.data['name'])
                if user is not None:
                    if check_password(form.data['password'], user['password']):
                        await login(self.request, user, timeout=7200)
                        raise web.HTTPOk(body=json.dumps(dict(message='Успешная авторизация')),
                                         content_type='application/json')
                    else:
                        return web.HTTPUnauthorized(body=json.dumps(dict(message='Неправильный пароль')),
                                                    content_type='application/json')
                else:
                    return web.HTTPNotFound(body=json.dumps(dict(message='Такого пользователя не существует')),
                                            content_type='application/json')


@routers_user.get('/logout/', name='user_logout')
async def user_logout(request):
    await logout(request)
    raise web.HTTPFound(request.app.router['user_auth'].url_for())


@routers_user.view('/manage/{user}')
class UserManager(web.View):
    async def get(self):
        async with self.request.app['db'].acquire() as conn:
            sql_response = await conn.fetchrow('SELECT * FROM users WHERE name = $1;', self.request.match_info['user'])
            if self.request.query.get('exist', 'false').lower() == 'true':
                return web.HTTPOk(body=json.dumps(dict(exist=True if sql_response else False)),
                                  content_type='application/json')
            else:
                return web.HTTPOk(body=json.dumps(dict(name=sql_response['name'], grand=sql_response['grand'])),
                                  content_type='application/json')


def dict_by_fields(data, fields=None):
    return [{field: row[field] for field in fields} if fields else {key: value for key, value in row.items()} for row in
            data]


def record_to_dict(record):
    """ Convert record instance to dict"""
    if not isinstance(record, list):
        return [{key: value for key, value in record.items()}]
    else:
        return [{key: value for key, value in row.items()} for row in record]


@routers_user.view('/user_api/')
class Users(web.View):

    async def get(self):
        """
        Method allow to get information about users, by their ids.

        Query string params:
            - names: list of names, of users which need to return, if names param didn't pass, return all users;
            - limit;
            - offset;
            - fields, if not pass return only name, and photo for every user;

        :return: json with items fields, which contain list of users dictionaries.
        """
        limit = self.request.query.get('limit', 40)
        offset = self.request.query.get('offset', 0)
        names = self.request.query.get('names', None)
        fields = self.request.query.get('fields', 'name, photo')
        async with self.request.app['db'].acquire() as conn:
            users_row_data = None
            if names:
                names = names.split(',')
                names_indexes = ", ".join([f'${i}' for i in range(1, len(names) + 1)])
                users_row_data = await conn.fetch(
                    f'SELECT {fields} FROM users WHERE name IN ({names_indexes}) LIMIT {limit} OFFSET {offset};',
                    *names)
            else:
                users_row_data = await conn.fetch(f'SELECT {fields} FROM users LIMIT {limit} OFFSET {offset};')
        response = dict(items=dict_by_fields(data=users_row_data))
        return web.HTTPOk(body=json.dumps(response), content_type='application/json')

    async def post(self):
        reader = await self.request.multipart()
        async with self.request.app['db'].acquire() as conn:
            data = {}
            while True:
                field = await reader.next()
                # Read common fields
                if not field:
                    # If not fields were read

                    if not data:
                        response = dict(message='No data in post request.')
                        return web.HTTPBadRequest(body=json.dumps(response), content_type='application/json')
                    # Check to user existing
                    user_name = data['name']
                    user = await conn.fetchrow('SELECT name FROM users WHERE name = $1;', user_name)
                    if user:
                        response = dict(message=f'User {user_name} already exist.')
                        return web.HTTPConflict(body=json.dumps(response), content_type='application/json')
                    if 'photo' in data:
                        # If files was loaded.
                        source_name, source_extension = os.path.splitext(data['photo']['filename'])
                        new_file_name = 'user_photo' + source_extension
                        # Photo path for saving in model.
                        path = os.path.join(user_name, new_file_name)

                        try:
                            os.mkdir(MEDIA_ROOT / user_name)
                        except FileExistsError:
                            pass

                        # Save photo.
                        with open(MEDIA_ROOT / user_name / new_file_name, 'wb') as file:
                            file.write(data['photo']['file'])
                            data['photo'] = path

                    fields = ', '.join([field for field in data.keys()])
                    fields_indexes = ', '.join([f'${i}' for i in range(1, len(data) + 1)])
                    await conn.execute(f'INSERT INTO users ({fields}) VALUES ({fields_indexes});',
                                       *data.values())

                    # Return new or updated user
                    user = await conn.fetchrow('SELECT name, photo FROM users WHERE name = $1;', user_name)
                    response = dict(items=record_to_dict(user))
                    return web.HTTPCreated(body=json.dumps(response), content_type='application/json')
                if field.name == 'grand':
                    data.update({
                        field.name: True if (await field.read()).decode('utf-8').lower() == 'true' else False
                    })
                if field.name == 'password':
                    password = (await field.read()).decode('utf-8')
                    if len(password) < 8:
                        response = dict(message='Password len must be greater or equal to 8.')
                        return web.HTTPConflict(body=json.dumps(response), content_type='application/json')
                    data.update({
                        field.name: hash_password((await field.read()).decode('utf-8'))
                    })
                if field.name in ['name', 'email', 'description']:
                    data.update({
                        field.name: (await field.read()).decode('utf-8')
                    })
                # Read file field
                if field.name == 'photo':
                    data['photo'] = dict(file=b'', filename=None)
                    while True:
                        chunk = await field.read_chunk()
                        if not chunk:
                            break
                        # Collect bytes
                        data['photo']['file'] += chunk
                    data['photo']['filename'] = field.filename

    async def delete(self):
        """
        Method delete users, which names were passed to query str as (names=...).
        Query string params:
            - names: list of users names.
        :return:
        """
        names = self.request.query.get('names', None)
        if not names:
            response = dict(message=f'"names" param isn\'t passed.')
            return web.HTTPBadRequest(body=json.dumps(response), content_type='application/json')
        async with self.request.app['db'].acquire() as conn:
            names = names.split(',')
            names_indexes = [f'${i}' for i in range(1, len(names) + 1)]
            await conn.execute(f"DELETE FROM users WHERE name IN ({','.join(names_indexes)});", *names)
            response = dict(message=f'Users ({", ".join(names)}) successfuly deleted.')
            return web.HTTPOk(body=json.dumps(response), content_type='application/json')


@routers_user.view('/user_api/{name}')
class User(web.View):

    async def get(self):
        """
        Query string params:
            - fields:
                - all common fields default: (name, photo);
            - subsribers [count]
            - subscriptions [count]
            - email: if was determined will look for user by email passed by {name}. (True of False)
        :return: information about user which name is {name}
        """
        fields = self.request.query.get('fields', 'name, photo')
        subsribers = self.request.query.get('subscribers', None)
        subscriptions = self.request.query.get('subscriptions', None)
        email = self.request.query.get('email', False)
        email = True if email.lower() == 'true' else False
        async with self.request.app['db'].acquire() as conn:
            subsribers_count = f", (SELECT COUNT(*) FROM users_subscribers WHERE owner_name = '{self.request.match_info['name']}') as subscribers" if subsribers == 'True' else ''
            subscriptions_count = f", (SELECT COUNT(*) FROM users_subscribers WHERE subscriber_name = '{self.request.match_info['name']}') as subscriptions" if subscriptions == 'True' else ''
            where_expression = 'email' if email else 'name'
            user = await conn.fetchrow(
                f"SELECT {fields}{subsribers_count}{subscriptions_count} FROM users WHERE {where_expression} = $1;",
                self.request.match_info['name'])
            if not user:
                response = dict(message=f'User {self.request.match_info["name"]} doesn\'t exist.')
                return web.HTTPNotFound(body=json.dumps(response), content_type='application/json')
            response = dict(items=record_to_dict(user))
            return web.HTTPOk(body=json.dumps(response), content_type='application/json')

    async def post(self):
        """
        Update user instance.
        :return:
        """
        reader = await self.request.multipart()
        async with self.request.app['db'].acquire() as conn:
            data = {}
            while True:
                field = await reader.next()
                # Read common fields
                if not field:
                    # If not fields were read

                    if not data:
                        response = dict(message='No data in post request.')
                        return web.HTTPBadRequest(body=json.dumps(response), content_type='application/json')
                    # Check to user existing
                    user = await conn.fetchrow('SELECT name, password FROM users WHERE name = $1;',
                                               self.request.match_info['name'])
                    if not user:
                        response = dict(message=f'User {self.request.match_info["name"]} doesn\'t exist.')
                        return web.HTTPNotFound(body=json.dumps(response), content_type='application/json')
                    if 'password' in data:
                        if not 'check_password' in data:
                            response = dict(message=f'Request with field password also must contain check_password field.')
                            return web.HTTPBadRequest(body=json.dumps(response), content_type='application/json')
                        if check_password(data['check_password'], user['password']) == False:
                            response = dict(
                            message=f'Check password is invalid.')
                            return web.HTTPConflict(body=json.dumps(response), content_type='application/json')

                    user_name = data['name'] if 'name' in data else self.request.match_info['name']
                    # Check if user with user_name existing, if user_name != match_info['name'],
                    if user_name != self.request.match_info['name']:
                        user = await conn.fetchrow('SELECT name FROM users WHERE name = $1;',
                                                   user_name)
                        if user:
                            response = dict(message=f'User {self.request.match_info["name"]} already exist.')
                            return web.HTTPConflict(body=json.dumps(response), content_type='application/json')

                    if 'photo' in data:
                        # If files was loaded.
                        source_name, source_extension = os.path.splitext(data['photo']['filename'])
                        new_file_name = 'user_photo' + source_extension
                        # Photo path for saving in model.
                        path = os.path.join(user_name, new_file_name)
                        try:
                            if self.request.match_info['name'] != user_name:
                                os.rename(MEDIA_ROOT / self.request.match_info['name'], MEDIA_ROOT / user_name)
                        except FileExistsError:
                            os.mkdir(MEDIA_ROOT / user_name)
                        except OSError:
                            for root, dirs, files in os.walk(MEDIA_ROOT / user_name):
                                for name in files:
                                    os.remove(os.path.join(root, name))
                        # Save photo.
                        with open(MEDIA_ROOT / user_name / new_file_name, 'wb') as file:
                            file.write(data['photo']['file'])
                            data['photo'] = path

                    fields = ', '.join(
                        [f'{key} = ${index}' for key, index in zip(data.keys(), range(1, len(data.keys())+1))])
                    await conn.execute(f"UPDATE users SET {fields} WHERE name = '{self.request.match_info['name']}';",
                                       *data.values())
                    # Return new or updated user
                    user = await conn.fetchrow('SELECT name, photo FROM users WHERE name = $1;', user_name)
                    response = dict(items=record_to_dict(user))
                    return web.HTTPOk(body=json.dumps(response), content_type='application/json')

                if field.name == 'grand':
                    data.update({
                        field.name: True if (await field.read()).decode('utf-8').lower() == 'true' else False
                    })
                if field.name == 'password':
                    data.update({
                        field.name: hash_password((await field.read()).decode('utf-8'))
                    })
                if field.name in ['name', 'email', 'description', 'check_password']:
                    data.update({
                        field.name: (await field.read()).decode('utf-8')
                    })
                # Read file field
                if field.name == 'photo':
                    data['photo'] = dict(file=b'', filename=None)
                    while True:
                        chunk = await field.read_chunk()
                        if not chunk:
                            break
                        # Collect bytes
                        data['photo']['file'] += chunk
                    data['photo']['filename'] = field.filename


@routers_user.view('/role/')
class Roles(web.View):

    async def get(self):
        """
        :return: List of all groups.
        """
        async with self.request.app['db'].acquire() as conn:
            sql_response = await conn.fetch('SELECT * FROM role;')
            if not sql_response:
                await conn.close()
                return web.HTTPOk(body=dict(message='No groups!'))
            await conn.close()
            dict_response = dict(
                items=[dict(id=row['id'], name=row['name'], level=row['level']) for row in sql_response])
            return web.HTTPOk(body=json.dumps(dict_response), content_type='application/json')

    async def post(self):
        """
        Create new role.
        Query args:
            - name
            - level
        :return: New group info.
        """
        data = await self.request.post()
        if not 'name' in data or not 'level' in data:
            return web.HTTPBadRequest(body=json.dumps(dict(message='Invalid request!')))
        async with self.request.app['db'].acquire() as conn:
            sql_response = await conn.fetchrow('SELECT * FROM role WHERE name = $1;', data['name'])
            if not sql_response:
                await conn.execute("INSERT INTO role (name, level) VALUES ($1, $2)",
                                   data['name'], int(data['level']))
                sql_response = await conn.fetchrow('SELECT * FROM role WHERE name = $1;', data['name'])
                await conn.close()
                dict_response = dict(
                    items=[dict(id=sql_response['id'], name=sql_response['name'], level=sql_response['level'])])
                return web.HTTPCreated(body=json.dumps(dict_response), content_type='application/json')
            else:
                await conn.close()
                return web.HTTPConflict(
                    body=dict(message=f'Group with name {data["name"]} already exist'),
                    content_type='application/json')


@routers_user.view('/role/{id}')
class Role(web.View):

    async def get(self):
        async with self.request.app['db'].acquire() as conn:
            sql_response = await conn.fetchrow('SELECT * FROM role WHERE id = $1;', int(self.request.match_info['id']))
            await conn.close()
            if not sql_response:
                return web.HTTPNotFound(
                    body=json.dumps(dict(message=f'No group with id {self.request.match_info["id"]}')),
                    content_type='application/json')
            else:
                dict_response = dict(items=[dict(name=sql_response['name'], level=sql_response['level'])])
                return web.HTTPOk(body=json.dumps(dict_response), content_type='application/json')

    async def put(self):
        """
        Request body content-type must be application/json.
        Update role by id.
        :return:
        """
        data = await self.request.json()
        id = int(self.request.match_info['id'])
        if not self.request.body_exists:
            return web.HTTPBadRequest(body=json.dumps(dict(name='Неправильный запрос')),
                                      content_type='application/json')
        expr = [f'{param} = ${i}' for param, i in zip(data.keys(), range(1, len(data) + 1))]
        async with self.request.app['db'].acquire() as conn:
            sql_response = await conn.fetchrow(f"SELECT * FROM role WHERE id = $1;", id)
            if not sql_response:
                await conn.close()
                return web.HTTPNotFound(
                    body=json.dumps(dict(message=f'No role {int(self.request.match_info["id"])} in database')),
                    content_type='application/json')
            await conn.execute(f'UPDATE role SET {", ".join(expr)} WHERE id = ${len(data) + 1};',
                               *data.values(), id)
            sql_response = await conn.fetchrow('SELECT * FROM role WHERE id = $1;', id)
            await conn.close()
        dict_response = dict(
            items=[dict(id=sql_response['id'], name=sql_response['name'], level=sql_response['level'])])
        return web.Response(body=json.dumps(dict_response), status=200, content_type='application/json')

    async def delete(self):
        id = int(self.request.match_info['id'])
        async with self.request.app['db'].acquire() as conn:
            sql_response = await conn.fetchrow(f"SELECT * FROM role WHERE id = $1;", id)
            if not sql_response:
                await conn.close()
                return web.HTTPNotFound(
                    body=json.dumps(dict(message=f'No role {id} in database')),
                    content_type='application/json')
            await conn.execute('DELETE FROM role WHERE id = $1;', id)
            await conn.close()
            return web.HTTPOk(body=json.dumps(dict(message=f'Successful delete role {id}')),
                              content_type='application/json')


@routers_user.view('/role/member/{id}')
class RoleMembers(web.View):

    async def post(self):
        """
        Add user with 'name' to group with 'id'.
        :return: Status of request.
        """
        data = await self.request.json()
        id = int(self.request.match_info['id'])
        if not self.request.body_exists:
            return web.HTTPBadRequest(body=json.dumps(dict(message=f'No request body!')),
                                      content_type='application/json')
        async with self.request.app['db'].acquire() as conn:
            sql_response = await conn.fetchrow(f"SELECT * FROM role WHERE id = $1;", id)
            if not sql_response:
                await conn.close()
                return web.HTTPNotFound(
                    body=json.dumps(dict(message=f'No role {self.request.match_info["id"]} in database')),
                    content_type='application/json')
            exist_check = await conn.fetchrow('SELECT * FROM role_users WHERE user_name = $1 AND role_id = $2;',
                                              data['name'], id)
            if not exist_check:
                await conn.execute('INSERT INTO role_users (role_id, user_name) VALUES ($1, $2);', id, data['name'])
                await conn.close()
                return web.HTTPCreated(
                    body=json.dumps(dict(message=f'User successfuly added to group {self.request.match_info["id"]}')),
                    content_type='application/json')
            else:
                await conn.close()
                return web.HTTPConflict(
                    body=json.dumps(dict(message=f'User already in group {self.request.match_info["id"]}')),
                    content_type='application/json')

    async def delete(self):
        """
        Delete member from role.
        :return: Status of request.
        """
        data = await self.request.json()
        id = int(self.request.match_info['id'])
        if not self.request.body_exists:
            return web.HTTPBadRequest(body='Need name field!')
        async with self.request.app['db'].acquire() as conn:
            sql_response = await conn.fetchrow(f"SELECT * FROM role WHERE id = $1;", id)
            if not sql_response:
                await conn.close()
                return web.HTTPNotFound(
                    body=json.dumps(dict(message=f'No role {self.request.match_info["id"]} in database')),
                    content_type='application/json')
            exist_check = await conn.fetchrow('SELECT * FROM role_users WHERE user_name = $1 AND role_id = $2;',
                                              data['name'], id)
            if not exist_check:
                await conn.close()
                return web.HTTPNotFound(
                    body=json.dumps(
                        dict(message=f'No user {data["name"]} in role  {self.request.match_info["id"]}')),
                    content_type='application/json')
            else:
                await conn.execute('DELETE FROM role_users WHERE user_name = $1 AND role_id = $2;', data['name'], id)
                await conn.close()
                return web.HTTPOk(
                    body=json.dumps(
                        dict(message=f'User {data["name"]} is '
                                     f'successfuly deleted from role {self.request.match_info["id"]}')),
                    content_type='application/json')


@routers_user.view('/subscriber/')
class SubscribeControl(web.View):
    async def get(self):
        """
        Query str args:
            - mode (subscriptions, subscribers or check) (subscriptions is standart mode)
            - limit
            - offset
            - user
            - fields
            - owner (if mode is 'check', will check that user subscribed on owner)
        :return: List of subscribers or subscriptions of user (owner).
        """
        user = self.request.query.get('user', None)
        mode = self.request.query.get('mode', 'subscriptions')
        limit = self.request.query.get('limit', 40)
        offset = self.request.query.get('offset', 0)
        owner = self.request.query.get('owner', None)
        if mode not in ('subscriptions', 'subscribers', 'check'):
            response = dict(message=f'Mode {mode} doesn\'t exist')
            return web.HTTPBadRequest(body=json.dumps(response), content_type='application/json')
        if not user:
            response = dict(message=f'Query string must contain user')
            return web.HTTPBadRequest(body=json.dumps(response), content_type='application/json')
        async with self.request.app['db'].acquire() as conn:
            user_check = await conn.fetchrow('SELECT name FROM users WHERE name = $1;', user)
            if not user_check:
                response = dict(message=f'User with name {user} doesn\'t exist')
                return web.HTTPNotFound(body=json.dumps(response), content_type='application/json')
            users = None
            count = None
            if mode == 'subscriptions':
                count = await conn.fetchval(
                    'SELECT COUNT(*) FROM users INNER JOIN users_subscribers ON users.name = users_subscribers.subscriber_name WHERE users.name = $1',
                    user)
                users = await conn.fetch(
                    f'SELECT users.name, users.photo FROM users INNER JOIN users_subscribers ON users.name = users_subscribers.subscriber_name WHERE users.name = $1 LIMIT {limit} OFFSET {offset};',
                    user)
            elif mode == 'subscribers':
                count = await conn.fetchval(
                    'SELECT COUNT(*) FROM users INNER JOIN users_subscribers ON users.name = users_subscribers.owner_name WHERE users.name = $1',
                    user)
                users = await conn.fetch(
                    f'SELECT users.name, users.photo FROM users INNER JOIN users_subscribers ON users.name = users_subscribers.owner_name WHERE users.name = $1 LIMIT {limit} OFFSET {offset};',
                    user)
            elif mode == 'check':
                if not owner:
                    response = dict(message=f'Query string must contain owner if check mode selected')
                    return web.HTTPBadRequest(body=json.dumps(response), content_type='application/json')
                owner_check = await conn.fetchrow('SELECT name FROM users WHERE name = $1;', owner)
                if not owner_check:
                    response = dict(message=f'Onwer with name {owner} doesn\'t exist')
                    return web.HTTPNotFound(body=json.dumps(response), content_type='application/json')
                # Check subscribe
                check = await conn.fetchval(
                    "SELECT COUNT(*) FROM users_subscribers WHERE owner_name = $1 AND subscriber_name = $2;", owner,
                    user)
                response = dict(status=True if check == 1 else False)
                return web.HTTPOk(body=json.dumps(response), content_type='application/json')
            response = dict(items=[dict(name=row['name'], path=row['photo']) for row in users], count=count)
            return web.HTTPOk(body=json.dumps(response), content_type='application/json')

    async def delete(self):
        """
        Unsubscribe user (user) from user (owner).
        If pass only user or owner, will delete all subscribers or all subscriptions.

        No user or owner existing check.

        Query str args:
            - user (person which needs to unsubscribe)
            - owner
        :return:
        """
        user = self.request.query.get('user', None)
        owner = self.request.query.get('owner', None)
        if not user and not owner:
            response = dict(message=f'Request must contain one or more arguments (user, owner)')
            return web.HTTPBadRequest(body=json.dumps(response), content_type='application/json')
        async with self.request.app['db'].acquire() as conn:
            if user and not owner:
                # Delete all subscriptions
                await conn.execute('DELETE FROM users_subscribers WHERE subscriber_name = $1;', user)
            elif not user and owner:
                # Delete all subscribers
                await conn.execute('DELETE FROM users_subscribers WHERE owner_name = $1;', owner)
            else:
                # Delete subscriber of owner
                await conn.execute("DELETE FROM users_subscribers WHERE subscriber_name = $1 AND owner_name = $2;",
                                   user, owner)
            response = dict(message='Success')
            return web.HTTPOk(body=json.dumps(response), content_type='application/json')

    async def post(self):
        """
        Subscribe user (user) to user (owner).

        Query str args:
            - user (person which needs to subscribe)
            - owner
        :return:
        """
        user = self.request.query.get('user', None)
        owner = self.request.query.get('owner', None)
        if user == owner:
            response = dict(message=f'User and owner must be different values')
            return web.HTTPBadRequest(body=json.dumps(response), content_type='application/json')
        if not user or not owner:
            response = dict(message=f'Request must contain arguments (user, owner)')
            return web.HTTPBadRequest(body=json.dumps(response), content_type='application/json')
        async with self.request.app['db'].acquire() as conn:
            # Check if already subscribe
            check_subscribe = await conn.fetchval(
                'SELECT COUNT(*) FROM users_subscribers WHERE subscriber_name = $1 AND owner_name = $2;', user, owner)
            if check_subscribe == 1:
                response = dict(message=f'{user} already subscriber of {owner}.')
                return web.HTTPConflict(body=json.dumps(response), content_type='application/json')
            # User exist check
            user_check = await conn.fetchrow('SELECT name FROM users WHERE name = $1;', user)
            owner_check = await conn.fetchrow('SELECT name FROM users WHERE name = $1;', owner)
            if not user_check or not owner_check:
                response = dict(
                    message=f'Someone of users not found user:{user_check.name if user_check else None} '
                            f'owner:{owner_check.name if owner_check else None}')
                return web.HTTPNotFound(body=json.dumps(response), content_type='application/json')
            await conn.execute('INSERT INTO users_subscribers (owner_name, subscriber_name) VALUES ($1, $2)', owner,
                               user)
            response = dict(message='Success')
            return web.HTTPOk(body=json.dumps(response), content_type='application/json')
