import logging
import random

from aiohttp import web
import aiohttp_jinja2
from aiohttp_session import get_session

from .login_manager import hash_password, check_password, login
from .forms import *
from .backend import SqlEngine
from .models import users

logger_console = logging.getLogger('console_logger')

routers_user = web.RouteTableDef()


@routers_user.view('/', name='user_view')
class Authentication(web.View):
    @aiohttp_jinja2.template('user_app/templates/hello_page.html')
    async def get(self):
        async with self.request.app['db'].acquire() as conn:
            user = await conn.fetchrow('SELECT * FROM users WHERE users.name = $1', 'Artem')
            await login(self.request, user, 3600)

    async def post(self):
        form = Auth(self.request.post)
        if form.validate():
            async with self.request.app['db'].acquire() as conn:
                user = conn.fetchrow('SELECT user, password FROM users WHERE name = $1;', form.name)
            if check_password(form.password, user['password']):
                await login(self.request, user, timeout=3600)
            else:
                return web.HTTPFound(self.request.app.router['user_view'].url_for())
        else:
            return web.HTTPFound(self.request.app.router['user_view'].url_for())

    async def put(self):
        form = Register(self.request.post)
        s = "abcdefghijklmnopqrstuvwxyz01234567890ABCDEFGHIJKLMNOPQRSTUVWXYZ!@#$%^&*()?"
        passlen = 8
        password = "".join(random.sample(s, passlen))
        if form.validate():
            async with self.request.app['db'].acquire() as conn:
                SqlEngine(conn, users).insert((
                    dict(name=form.name, password=password),
                ))
                await conn.close()
