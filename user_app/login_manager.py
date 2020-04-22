import datetime
from aiohttp.web import HTTPUnauthorized, HTTPFound, HTTPNotFound

import jwt
import bcrypt

from aiohttp_session import get_session
from settings import SECRET_KEY


class Decorator:

    @staticmethod
    def cl_login_required(func):
        def wrap(self):
            if not self.request.user.is_authenticated():
                raise HTTPUnauthorized
            else:
                func(self)

        return wrap

    @staticmethod
    def method_login_required(func):
        def wrap(request):
            if not request.user.is_authenticated():
                raise HTTPUnauthorized
            else:
                func(request)

        return wrap

    @staticmethod
    async def group_required(request, group: str):
        with request.app['db'].acquire() as conn:
            group_ = await conn.fetchrow('SELECT level FROM role WHERE name = $1;', group)
            if not group:
                raise HTTPNotFound
            coincidences = await conn.fetch('SELECT * FROM groups_users INNER JOIN role ON groups_users.role_name = group.name WHERE groups_users.user_name = $1;', request.user.name)
            if not coincidences:
                raise HTTPUnauthorized
            conn.close()
            if all(coincidence['level'] < group_['level'] for coincidence in coincidences):
                raise HTTPUnauthorized
            else:
                pass


class UserInfo:
    """
    Default user class for auth system.
    """

    def __init__(self, model=None, groups=None):
        self.model = model
        self.name = model['name'] if model else 'Anonymous'
        self.is_authenticated = True if model else False
        self.groups = {group['name']: group['level'] for group in groups} if groups else None

    def is_authenticated(self):
        return self.is_authenticated

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
