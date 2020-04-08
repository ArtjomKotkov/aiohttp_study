
from aiohttp import web

from main_app.routers import setup_routers
from .setting import load_config


app = web.Application()
app['config'] = load_config()
setup_routers(app)
web.run_app(app)