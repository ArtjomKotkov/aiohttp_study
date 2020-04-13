import logging.config
import base64

from cryptography import fernet
from aiohttp_session import setup
from aiohttp_session.cookie_storage import EncryptedCookieStorage

from aiohttp import web
import aiohttp_jinja2
import jinja2
import yaml
import asyncpg

# Import all routers
from main_app.views import routers
from user_app.views import routers_user

from setting import load_config, BASE_DIR

with open('loggers.yaml', 'r') as logger_file:
    logging.config.dictConfig(yaml.safe_load(logger_file))

console_logger = logging.getLogger('console_logger')


def init_subapp(app, prefix: str, routers_):
    sub_app = web.Application()
    sub_app.add_routes(routers_)
    app.add_subapp(prefix, sub_app)
    return sub_app


async def init_app():
    # Create app
    app = web.Application()
    # Load config
    app['config'] = load_config()
    # Init db engine asyncpg
    app['db'] = await asyncpg.create_pool(app['config']['postgres']['DSN'].format(**load_config()['postgres']))
    # Add routers
    app.add_routes(routers)
    app.router.add_static('/static/', BASE_DIR / 'main_app' / 'static', name='static')
    # Init jinja2
    aiohttp_jinja2.setup(app, loader=jinja2.FileSystemLoader(BASE_DIR))

    # Init session
    fernet_key = fernet.Fernet.generate_key()
    secret_key = base64.urlsafe_b64decode(fernet_key)
    setup(app, EncryptedCookieStorage(secret_key))

    # SubApps
    user_app = init_subapp(app, prefix='/user/', routers_=routers_user)
    return app


# async def close_pg(app):
#     console_logger.debug('Connection close')
#     app['db'].close()
#     await app['db'].wait_closed()

# Events


web.run_app(init_app())
