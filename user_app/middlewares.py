import jwt
import datetime
import logging

from aiohttp.web import middleware
from aiohttp_session import get_session

from .login_manager import logout, UserInfo
from settings import SECRET_KEY

logger_console = logging.getLogger('console_logger')

@middleware
async def Auth(request, handler):
    session = await get_session(request)
    jwt_token = session.get('JWT', None)
    if jwt_token:
        user_credentials = jwt.decode(jwt_token, SECRET_KEY, algorithm='HS256')
        datetime_expires = datetime.datetime.strptime(user_credentials['expires'], '%Y-%m-%d-%H-%M')
        if datetime_expires < datetime.datetime.now():
            await logout(request)
            request.user = UserInfo()
        else:
            async with request.app['db'].acquire() as conn:
                request.user = UserInfo(await conn.fetchrow('SELECT * FROM users WHERE name = $1', user_credentials['name']))
                await conn.close()
    else:
        request.user = UserInfo()
    resp = await handler(request)
    print(resp)
    return resp
