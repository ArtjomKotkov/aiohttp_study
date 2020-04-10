import logging.config

from aiohttp import web
import aiohttp_jinja2
import jinja2
import yaml
import asyncpg

from main_app.views import routers
from setting import load_config, BASE_DIR

with open('loggers.yaml', 'r') as logger_file:
    logging.config.dictConfig(yaml.safe_load(logger_file))

console_logger = logging.getLogger('console_logger')


async def init_app():
    app = web.Application()

    app['config'] = load_config()

    app['db'] = await asyncpg.create_pool(app['config']['postgres']['DSN'].format(**load_config()['postgres']))
    app.add_routes(routers)
    app.router.add_static('/static/', BASE_DIR / 'main_app' / 'static', name='static')

    aiohttp_jinja2.setup(app, loader=jinja2.FileSystemLoader(BASE_DIR / 'main_app' / 'templates'))
    #app.on_cleanup.append(close_pg)
    return app


# async def close_pg(app):
#     console_logger.debug('Connection close')
#     app['db'].close()
#     await app['db'].wait_closed()

# Events


web.run_app(init_app())



