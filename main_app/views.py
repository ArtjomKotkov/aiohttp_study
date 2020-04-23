import logging

from aiohttp import web
import aiohttp_jinja2

from user_app.login_manager import Decorator

logger_console = logging.getLogger('console_logger')

routers = web.RouteTableDef()


@routers.view('/', name='main')
class MainView(web.View):
    @aiohttp_jinja2.template('main_app/templates/main.html')
    @Decorator.cl_login_required
    async def get(self):
        pass
