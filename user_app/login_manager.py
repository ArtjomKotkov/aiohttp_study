import datetime
import json

import jwt
import bcrypt

from aiohttp_session import get_session
from settings import SECRET_KEY


class UserInfo:
    """
    Default user class for auth system.
    """

    def __init__(self, model=None):
        if model:
            self.model = model
            self.name = model['name']
            self.is_authenticated = True
        else:
            self.model = None
            self.name = 'Anonymous'
            self.is_authenticated = False

    def __dict__(self):
        if self.model:
            return_ = dict(is_authenticated=True)
            for field, value in self.model.items():
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


def create_user():
    pass


def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt(12)).decode("utf-8")


def check_password(password, hash_):
    return True if bcrypt.checkpw(password.encode('utf-8'), hash_.encode('utf-8')) else False
