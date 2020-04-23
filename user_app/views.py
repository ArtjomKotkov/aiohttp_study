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


# User Auth views

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
        form = Auth(await self.request.post())
        if form.validate():
            async with self.request.app['db'].acquire() as conn:
                user = await conn.fetchrow('SELECT * FROM users WHERE name = $1;', form.data['name'])
                await conn.close()
                if user is not None:
                    if check_password(form.data['password'], user['password']):
                        await login(self.request, user, timeout=3600)
                        raise web.HTTPFound(self.request.app['parent_app'].router['main'].url_for())
                    else:
                        form.password.errors.append('Неправильный пароль!')
                        return aiohttp_jinja2.render_template('user_app/templates/auth.html', self.request,
                                                              {'form': form})
                else:
                    form.name.errors.append('Пользователь с таким именем не существует')
                    return aiohttp_jinja2.render_template('user_app/templates/auth.html', self.request,
                                                          {'form': form})


@routers_user.get('/logout/', name='user_logout')
async def user_logout(request):
    await logout(request)
    raise web.HTTPFound(request.app.router['user_auth'].url_for())


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
            dict_response = dict(items=[dict(name=row['name'], level=row['level']) for row in sql_response])
            return web.HTTPOk(body=json.dumps(dict_response), content_type='application/json')

    async def post(self):
        """
        Create new role.
        Query args:
            - name
            - level
        :return: New group info.
        """
        if (not 'name' or not 'level') in self.request.query:
            return web.HTTPBadRequest(body=dict(message='Invalid request!'))
        async with self.request.app['db'].acquire() as conn:
            sql_response = await conn.fetchrow('SELECT * FROM role WHERE name = $1;',self.request.query['name'])
            if not sql_response:
                await conn.execute("INSERT INTO role (name, level) VALUES ($1, $2)",
                                   self.request.query['name'],self.request.query['level'])
                sql_response = await conn.fetchrow('SELECT * FROM role WHERE name = $1;',self.request.query['name'])
                await conn.close()
                dict_response = dict(items=[dict(name=sql_response['name'], level=sql_response['level'])])
                return web.HTTPCreated(body=json.dumps(dict_response), content_type='application/json')
            else:
                await conn.close()
                return web.HTTPConflict(
                    body=dict(message=f'Group with name {self.request.query["name"]} already exist'),
                    content_type='application/json')


@routers_user.view('/role/{name}')
class Role(web.View):

    async def get(self):
        async with self.request.app['db'].acquire() as conn:
            sql_response = await conn.fetchrow('SELECT * FROM role WHERE name = $1;', self.request.query['name'])
            await conn.close()
            if not sql_response:
                return web.HTTPNotFound(
                    body=dict(message=f'No group with name {self.request.match_info["name"]}'),
                    content_type='application/json')
            else:
                dict_response = dict(items=[dict(name=sql_response['name'], level=sql_response['level'])])
                return web.HTTPOk(body=json.dumps(dict_response), content_type='application/json')
