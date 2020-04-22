import datetime
import os
import json

from aiohttp import web
import aiohttp_jinja2

from settings import MEDIA_ROOT
from user_app.login_manager import Decorator
from .forms import UploadFiles

routers_content = web.RouteTableDef()


@routers_content.get('/')
@aiohttp_jinja2.template('content/templates/main.html')
async def main_page(request):
    return {'form': UploadFiles()}


@routers_content.view('/art', name='art')
class FilesManager(web.View):
    async def post(self):
        """
        Upload new file.
        Query string: name, description, file:multipart
        :return:
        """
        reader = await self.request.multipart()
        description = None
        name = None
        path = None
        dict_response = None
        while True:
            field = await reader.next()
            if not field:
                async with self.request.app['db'].acquire() as conn:
                    await conn.execute("""INSERT INTO art (name, description, path) 
                                          VALUES ($1, $2, $3);""", name, description, path)
                    row = await conn.fetchrow("""SELECT * FROM art
                                           ORDER BY id DESC
                                           LIMIT 1;""")
                    await conn.close()
                    dict_response = dict(items=[dict(id=row['id'],
                                                     name=row['name'],
                                                     description=row['description'],
                                                     path=row['path'],
                                                     likes=row['likes'],
                                                     views=row['views'],
                                                     date=row['date'],
                                                     owner=row['owner'])])
                break
            if field.name == 'file':
                datetime_ = datetime.datetime.now()
                source_name, source_extension = os.path.splitext(field.filename)
                new_name = source_name + datetime_.strftime('%y-%m-%d-%H-%M-%S') + source_extension
                path = os.path.join(self.request.user.name, new_name)
                try:
                    os.mkdir(MEDIA_ROOT / self.request.user.name)
                except FileExistsError:
                    pass
                with open(MEDIA_ROOT / self.request.user.name / new_name, 'wb') as file:
                    while True:
                        chunk = await field.read_chunk()
                        if not chunk:
                            break
                        file.write(chunk)
            if field.name == 'name':
                name = (await field.read()).decode('utf-8')
            if field.name == 'description':
                description = (await field.read()).decode('utf-8')
        return web.Response(body=json.dumps(dict_response), status=200, content_type='application/json')

    async def get(self):
        """
        Get list of all arts.
        Special params:
            - user : name of user which arts need to return
            - limit : limit of arts in response | default = 100
            - offset : offset from start | default = 0
        All arts sorted by datetime.
        :return:
        """
        data = self.request.query
        user = data.get('user', None)
        limit = data.get('limit', 100)
        offset = data.get('offset', 0)
        async with self.request.app['db'].acquire() as conn:
            if user:
                sql_request = await conn.fetch("""SELECT * FROM art
                                            WHERE owner = $1
                                            ORDER BY date DESC
                                            LIMIT $2 OFFSET $3;""", user, limit, offset)
            else:
                sql_request = await conn.fetch("""SELECT * FROM art
                                            ORDER BY date DESC
                                            LIMIT $1 OFFSET $2;""", limit, offset)
            await conn.close()
        dict_response = dict(items=[dict(id=row['id'],
                                         name=row['name'],
                                         description=row['description'],
                                         path=row['path'],
                                         likes=row['likes'],
                                         views=row['views'],
                                         date=row['date'],
                                         owner=row['owner']) for row in sql_request])
        return web.Response(body=json.dumps(dict_response), status=200, content_type='application/json')


@routers_content.view('/art/{id}')
class FileManager(web.View):

    async def get(self):
        """
        Return art with special id.

        :return: Json response.
        """
        async with self.request.app['db'].acquire() as conn:
            row = await conn.fetchrow("""SELECT * FROM art
                                                WHERE id = $1;""", self.request.match_info['id'])
            await conn.close()
        if not row:
            return web.HTTPNotFound(body=json.dumps(dict(message=f'No art with id {self.request.match_info["id"]}.')))
        else:
            dict_response = dict(items=[dict(id=row['id'],
                                             name=row['name'],
                                             description=row['description'],
                                             path=row['path'],
                                             likes=row['likes'],
                                             views=row['views'],
                                             date=row['date'],
                                             owner=row['owner'])])
            return web.Response(body=json.dumps(dict_response), status=200, content_type='application/json')

    async def delete(self):
        async with self.request.app['db'].acquire() as conn:
            row = await conn.fetchrow("""SELECT * FROM art
                                                WHERE id = $1;""", self.request.match_info['id'])

            if not row:
                await conn.close()
                return web.HTTPNotFound(
                    body=json.dumps(dict(message=f'No art with id {self.request.match_info["id"]}.')))
            else:
                await conn.execute("""DELETE FROM art
                                      WHERE id = $1""", self.request.match_info['id'])
                await conn.close()
                return web.Response(
                    body=json.dumps(dict(message=f'Successful delete art {self.request.match_info["id"]}'), status=200,
                                    content_type='application/json')
