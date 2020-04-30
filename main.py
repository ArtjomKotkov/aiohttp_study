import logging.config
import pprint

import aiohttp_session
from aiohttp_session.redis_storage import RedisStorage
from aiohttp import web
import aiohttp_jinja2
import jinja2
import yaml
import asyncpg
import aioredis

from main_app.views import routers
from user_app.views import routers_user
from content.views import routers_content
from user_app.middlewares import Auth
from user_app.login_manager import user_jinja2_processor
from chat.views import routers_chat, close_all
from settings import load_config, BASE_DIR, MEDIA_ROOT

with open('loggers.yaml', 'r') as logger_file:
    logging.config.dictConfig(yaml.safe_load(logger_file))

console_logger = logging.getLogger('console_logger')


def init_subapp(app, prefix: str, routers_, inherit_values: list, oncleanup: list=None, onstartup: list=None):
    sub_app = web.Application()
    sub_app.add_routes(routers_)
    for value in inherit_values:
        sub_app[value] = app[value]
    if oncleanup:
        sub_app.on_cleanup.extend(oncleanup)
    if onstartup:
        sub_app.on_cleanup.extend(onstartup)
    app.add_subapp(f'/{prefix}/', sub_app)
    app[prefix] = sub_app
    sub_app['parent_app'] = app
    return sub_app


async def init_app():
    # Middlewares
    redis = await aioredis.create_pool(('localhost', '6379'))
    storage = RedisStorage(redis)
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
    app.router.add_static('/media/', MEDIA_ROOT, name='media')
    # Init jinja2
    aiohttp_jinja2.setup(app, context_processors=[user_jinja2_processor, aiohttp_jinja2.request_processor],
                         loader=jinja2.FileSystemLoader(BASE_DIR))
    # SubApps
    user_app = init_subapp(app, prefix='user', routers_=routers_user, inherit_values=['db'])
    # Init chat app
    chat_app = init_subapp(app, prefix='chat', routers_=routers_chat, inherit_values=['db'], oncleanup=[close_all])
    chat_app['chat'] = {
        'anon_web_sockets': dict(),
        'user_web_sockets': dict()
    }
    user_app['chat_app'] = chat_app
    content_app = init_subapp(app, prefix='content', routers_=routers_content, inherit_values=['db'])
    return app


# async def close_pg(app):
#     console_logger.debug('Connection close')
#     app['db'].close()
#     await app['db'].wait_closed()

# Events


web.run_app(init_app())
