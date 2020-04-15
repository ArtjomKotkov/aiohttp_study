import logging

from aiohttp import web
import aiohttp_jinja2

logger_console = logging.getLogger('console_logger')

routers = web.RouteTableDef()


@routers.view('/')
class MainView(web.View):
    @aiohttp_jinja2.template('main_app/templates/main.html')
    async def get(self):
        pass
