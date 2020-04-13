import logging

from aiohttp import web
import aiohttp_jinja2

logger_console = logging.getLogger('console_logger')

routers = web.RouteTableDef()


@routers.view('/')
class MainView(web.View):
    @aiohttp_jinja2.template('main_app/templates/main.html')
    async def get(self):
        async with self.request.app['db'].acquire() as conn:
            users_ = await conn.fetch('SELECT * FROM users')
            logger_console.info(users_)
            await conn.close()
            return {'users': users_}


@routers.get('/{user_url}')
@aiohttp_jinja2.template('main_app/templates/user_page.html')
async def userpage():
    pass
