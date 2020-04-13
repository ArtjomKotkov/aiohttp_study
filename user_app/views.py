import logging
import random

from aiohttp import web
import aiohttp_jinja2
from aiohttp_session import get_session

from .forms import *
from .backend import SqlEngine
from .models import users

logger_console = logging.getLogger('console_logger')

routers_user = web.RouteTableDef()


@routers_user.view('/')
class Authentication(web.View):
    @aiohttp_jinja2.template('user_app/templates/hello_page.html')
    async def get(self):
        session = await get_session(self.request)


    async def post(self):
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


