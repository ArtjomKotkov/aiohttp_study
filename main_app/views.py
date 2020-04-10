import logging

from aiohttp import web
import aiohttp_jinja2
from .models import users

routers = web.RouteTableDef()

logger_console = logging.getLogger('console_logger')

@routers.view('/')
class MainView(web.View):
    @aiohttp_jinja2.template('main.html')
    async def get(self):
        async with self.request.app['db'].acquire() as conn:
            users_ = await conn.fetch('SELECT * FROM users')
            logger_console.info(users_)
            return {'users': users_}
