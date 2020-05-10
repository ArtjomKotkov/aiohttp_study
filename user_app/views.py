import logging
import json

from aiohttp import web
import aiohttp_jinja2
from aiohttp_session import get_session

from .login_manager import hash_password, check_password, login, logout
from .forms import *
from chat.forms import Chat

logger_console = logging.getLogger('console_logger')

routers_user = web.RouteTableDef()


# Main page views

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
async def gallary_page(request):
    return {'owner':request.match_info['user_name']}



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
