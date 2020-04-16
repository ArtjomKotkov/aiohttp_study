import logging.config
import base64

from cryptography import fernet
import aiohttp_session
from aiohttp_session.cookie_storage import EncryptedCookieStorage

from aiohttp import web
import aiohttp_jinja2
import jinja2
import yaml
import asyncpg

# Import all routers
from main_app.views import routers
from user_app.views import routers_user
from user_app.middlewares import Auth
from user_app.login_manager import user_jinja2_processor
from settings import load_config, BASE_DIR

with open('loggers.yaml', 'r') as logger_file:
    logging.config.dictConfig(yaml.safe_load(logger_file))

console_logger = logging.getLogger('console_logger')


def init_subapp(app, prefix: str, routers_, inherit_values: list):
    sub_app = web.Application()
    sub_app.add_routes(routers_)
    for value in inherit_values:
        sub_app[value] = app[value]
    app.add_subapp(f'/{prefix}/', sub_app)
    app[prefix] = sub_app
    sub_app['parent_app'] = app
    return sub_app


async def init_app():
    # Middlewares
    fernet_key = fernet.Fernet.generate_key()
    secret_key = base64.urlsafe_b64decode(fernet_key)
    storage = EncryptedCookieStorage(secret_key, max_age=10800)
    session_middleware = aiohttp_session.session_middleware(storage)
    middlewares = [session_middleware, Auth]
    # Create app
    app = web.Application(middlewares=middlewares)
    # Load config
    app['config'] = load_config()
    # Init db engine asyncpg
    app['db'] = await asyncpg.create_pool(app['config']['postgres']['DSN'].format(**load_config()['postgres']))
    # Add routers
    app.add_routes(routers)
    app.router.add_static('/static/', BASE_DIR / 'static', name='static')
    # Init jinja2
    aiohttp_jinja2.setup(app, context_processors=[user_jinja2_processor, aiohttp_jinja2.request_processor],
                         loader=jinja2.FileSystemLoader(BASE_DIR))
    # SubApps
    user_app = init_subapp(app, prefix='user', routers_=routers_user, inherit_values=['db'])
    return app


# async def close_pg(app):
#     console_logger.debug('Connection close')
#     app['db'].close()
#     await app['db'].wait_closed()

# Events


web.run_app(init_app())
