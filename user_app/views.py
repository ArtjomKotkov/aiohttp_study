import logging
import json

from aiohttp import web
import aiohttp_jinja2
from aiohttp_session import get_session

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

    async def post(self):
        form = Register(await self.request.post())
        if form.validate():
            async with self.request.app['db'].acquire() as conn:
                user = await conn.fetchrow('SELECT * FROM users WHERE name = $1;', form.data['name'])
                if user is None:
                    await conn.execute('INSERT INTO users (name, password) VALUES ($1, $2);', form.data['name'],
                                       hash_password(form.data['password']))
                    user = await conn.fetchrow('SELECT * FROM users WHERE name = $1;', form.data['name'])
                    await login(self.request, user, timeout=3600)
                    raise web.HTTPFound(self.request.app['parent_app'].router['main'].url_for())
                else:
                    form.name.errors.append('Пользователь с таким именем существует')
                    return aiohttp_jinja2.render_template('user_app/templates/register.html', self.request,
                                                          {'form': form})


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


@routers_user.view('/role')
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
            print(data)
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
                print('here1')
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
