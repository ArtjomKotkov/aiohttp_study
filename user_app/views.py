import logging
import random

from aiohttp import web
import aiohttp_jinja2
from aiohttp_session import get_session

from .login_manager import hash_password, check_password, login, logout
from .forms import *
from .backend import SqlEngine
from .models import users

logger_console = logging.getLogger('console_logger')

routers_user = web.RouteTableDef()


@routers_user.view('/register', name='user_register')
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


@routers_user.view('/auth', name='user_auth')
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


@routers_user.get('/logout', name='user_logout')
async def user_logout(request):
    await logout(request)
    raise web.HTTPFound(request.app.router['user_auth'].url_for())
