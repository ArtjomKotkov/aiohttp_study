import datetime
from aiohttp.web import HTTPUnauthorized, HTTPFound, HTTPNotFound

import jwt
import bcrypt

from aiohttp_session import get_session
from settings import SECRET_KEY


class Decorator:

    @staticmethod
    def cl_login_required(func):
        async def wrap(self, *args, **kwargs):
            if not self.request.user.is_authenticated:
                raise HTTPUnauthorized
            else:
                await func(self, *args, **kwargs)

        return wrap

    @staticmethod
    def method_login_required(func):
        async def wrap(request, *args, **kwargs):
            if not request.user.is_authenticated:
                raise HTTPUnauthorized
            else:
                await func(request, *args, **kwargs)

        return wrap

    @staticmethod
    def method_group_required(group: str):
        async def wrap_outside(func):
            async def wrap(request, *args, **kwargs):
                with request.app['db'].acquire() as conn:
                    group_ = await conn.fetchrow('SELECT level FROM role WHERE name = $1;', group)
                    await conn.close()
                    if not group:
                        raise HTTPNotFound
                    if group_['name'] in request.user.groups:
                        return await func(request, *args, **kwargs)
                    else:
                        raise HTTPUnauthorized
            return wrap
        return wrap_outside

class UserInfo:
    """
    Default user class for auth system.
    """

    def __init__(self, model=None, groups=None):
        self.model = model
        self.name = model['name'] if model else None
        self.is_authenticated = True if model else False
        self.groups = {group['name']: group['level'] for group in groups} if groups else None

    @property
    def is_grand(self):
        return self.model['grand'] if self.model else False

    def __dict__(self):
        if self.model:
            return_ = dict(is_authenticated=True)
            for field, value in self.model.items():
                if field == 'password':
                    continue
                return_.update({field: value})
        else:
            return_ = dict(is_authenticated=False, name=self.name)
        return return_


async def user_jinja2_processor(request):
    return {'user': request.user.__dict__()}


async def login(request, user, timeout):
    """
    Login user, pass JWT token to web session.

    :param request: request instance
    :param user: user instance
    :param timeout: time in seconds when user will be logout
    :return:
    """
    datetime_expires = datetime.datetime.now() + datetime.timedelta(seconds=timeout)
    session = await get_session(request)
    payload = dict(
        name=user['name'],
        expires=datetime_expires.strftime('%Y-%m-%d-%H-%M')
    )
    token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')
    session['JWT'] = token.decode("utf-8")


async def logout(request):
    session = await get_session(request)
    del session['JWT']


def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt(12)).decode("utf-8")


def check_password(password, hash_):
    return True if bcrypt.checkpw(password.encode('utf-8'), hash_.encode('utf-8')) else False
