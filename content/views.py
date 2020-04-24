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

async def add_tags_to_art(conn, art_id, tags: list):
    """
    Add tags to post with id art_id.
    :param conn: Connection instance asyncpg
    :param art_id:
    :param tags: list og tags
    :return:
    """
    exp = [f'($1, ${i}' for tag, i in zip(tags, range(2, len(tags)+2))]
    conn.execute(f'INSERT INTO tag_art (art_id, tag_name) VALUES {", ".join(exp)};', art_id, *tags)

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
        datetime_ = datetime.datetime.now()
        dict_response = None
        while True:
            field = await reader.next()
            if not field:
                async with self.request.app['db'].acquire() as conn:
                    await conn.execute("""INSERT INTO art (name, description, path, date, owner, likes, views) 
                                          VALUES ($1, $2, $3, $4, $5, $6, $7);""", name, description, path, datetime_,
                                       self.request.user.name, 0, 0)
                    row = await conn.fetchrow('SELECT * FROM art WHERE path = $1;', path)
                    # Add taqs to art.
                    #await add_tags_to_art(conn, row['id'], )
                    await conn.close()
                    dict_response = dict(items=[dict(id=row['id'],
                                                     name=row['name'],
                                                     description=row['description'],
                                                     path=row['path'],
                                                     likes=row['likes'],
                                                     views=row['views'],
                                                     date=row['date'].strftime('%y-%m-%d-%H-%M-%S'),
                                                     owner=row['owner'])])
                break
            if field.name == 'file':
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
            if field.name == 'tags':
                description = (await field.read()).decode('utf-8')
        return web.Response(body=json.dumps(dict_response), status=200, content_type='application/json')

    async def get(self):
        """
        Get list of all arts.
        Special params:
            - user : name of user which arts need to return
            - limit : limit of arts in response | default = 40
            - offset : offset from start | default = 0
            - order: [date, views, likes] | default = date
        All arts sorted by datetime.
        :return:
        """
        data = self.request.query
        user = data.get('user', None)
        limit = data.get('limit', 40)
        offset = data.get('offset', 0)
        order = data.get('order', 'date')
        async with self.request.app['db'].acquire() as conn:
            if user:
                sql_request = await conn.fetch(
                    f'SELECT * FROM art WHERE owner = $1 ORDER BY {order} DESC LIMIT {limit} OFFSET {offset};', user)
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
                                         date=row['date'].strftime('%y-%m-%d-%H-%M-%S'),
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
                                             date=row['date'].strftime('%y-%m-%d-%H-%M-%S'),
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
                                    content_type='application/json'))

    async def put(self):
        """
        Update art instance, accept all params from art model.
        :return: Updated art instance.
        """
        expr = [f'{param} = ${i}' for param, i in zip(self.request.query.keys(), range(1, len(self.request.query) + 1))]
        async with self.request.app['db'].acquire() as conn:
            row = conn.fetchrow('SELECT * FROM art WHERE id = $1;', self.request.query['id'])
            if not row:
                await conn.close()
                return web.HTTPNotFound(
                    body=json.dumps(dict(message=f'No art with id {self.request.match_info["id"]}.')))
            await conn.execute(f'UPDATE art SET {", ".join(expr)} WHERE owner = ${len(self.request.query) + 2};',
                         *self.request.query.values(), self.request.match_info['id'])
            row = await conn.fetchrow('SELECT * FROM art WHERE id = %1;', self.request.match_info['id'])
            await conn.close()
        dict_response = dict(items=[dict(id=row['id'],
                                         name=row['name'],
                                         description=row['description'],
                                         path=row['path'],
                                         likes=row['likes'],
                                         views=row['views'],
                                         date=row['date'].strftime('%y-%m-%d-%H-%M-%S'),
                                         owner=row['owner'])])
        return web.Response(body=json.dumps(dict_response), status=200, content_type='application/json')

@routers_content.view('/tag')
class Tags(web.View):
    async def get(self):
        """
        Get list of all tags.
        Special params:
            - limit : limit of arts in response | default = 40
            - offset : offset from start | default = 0
        All arts sorted by name.
        :return:List of all tags.
        """
        limit = self.request.query.get('limit', 40)
        offset = self.request.query.get('offset', 0)
        async with self.request.app['db'].acquire() as conn:
            sql_response = await conn.fetch(f"SELECT * FROM tag ORDER BY name ASC LIMIT {limit} OFFSET {offset};")
            await conn.close()
        dict_response = dict(items=[dict(id=row['id'], name=row['name']) for row in sql_response])
        if not sql_response:
            return web.HTTPNotFound(body=json.dumps(dict(message='No tags in database')), content_type='application/json')
        return web.Response(body=json.dumps(dict_response), status=200, content_type='application/json')

    async def post(self):
        """
        Create new tag.
        Query args:
            - name
        :return:
        """
        name = self.request.query.get('name', None)
        if not name:
            return web.HTTPBadRequest(body=json.dumps(dict(name='Не передано поле name')),  content_type='application/json')
        async with self.request.app['db'].acquire() as conn:
            tag = await conn.fetchrow('SELECT * FROM tag WHERE name = $1;', name)
            if not tag:
                await conn.execute('INSERT INTO tag (name) VALUES %1;', name)
                tag = await conn.fetchrow('SELECT * FROM tag ORDER BY id DESC LIMIT 1;')
                dict_response = dict(items=[dict(id=tag['id'], name=tag['name'])])
                return web.Response(body=json.dumps(dict_response), status=200, content_type='application/json')

@routers_content.view('/tag/{id}')
class Tag(web.View):
    async def get(self):
        """
        :return: list with only one tag info.
        """
        async with self.request.app['db'].acquire() as conn:
            sql_response = await conn.fetchrow(f"SELECT * FROM tag ORDER BY name WHERE id = $1;", self.request.match_info['id'])
            await conn.close()
        if not sql_response:
            return web.HTTPNotFound(body=json.dumps(dict(message='No tags in database')), content_type='application/json')
        dict_response = dict(items=[dict(id=sql_response['id'], name=sql_response['name'])])
        return web.Response(body=json.dumps(dict_response), status=200, content_type='application/json')

    async def put(self):
        """
        Update tag info
        Query args:
            - name
        :return:
        """
        if not self.request.query:
                return web.HTTPBadRequest(body=json.dumps(dict(name='Неправильный запрос')),
                                          content_type='application/json')
        expr = [f'{param} = ${i}' for param, i in zip(self.request.query.keys(), range(1, len(self.request.query) + 1))]
        async with self.request.app['db'].acquire() as conn:
            sql_response = await conn.fetchrow(f"SELECT * FROM tag WHERE id = $1;",
                                               self.request.match_info['id'])
            if not sql_response:
                await conn.close()
                return web.HTTPNotFound(body=json.dumps(dict(message=f'No tag {self.request.match_info["id"]} database')),
                                    content_type='application/json')
            await conn.execute(f'UPDATE tag SET {", ".join(expr)} WHERE id = ${len(self.request.query) + 2};',
                               *self.request.query.values(), self.request.match_info['id'])
            sql_response = await conn.fetchrow('SELECT * FROM tag WHERE id = %1;', self.request.match_info['id'])
            await conn.close()
        dict_response = dict(items=[dict(id=sql_response['id'], name=sql_response['name'])])
        return web.Response(body=json.dumps(dict_response), status=200, content_type='application/json')

    async def delete(self):
        async with self.request.app['db'].acquire() as conn:
            sql_response = await conn.fetchrow(f"SELECT * FROM tag ORDER BY name WHERE id = $1;",
                                               self.request.match_info['id'])
            if not sql_response:
                await conn.close()
                return web.HTTPNotFound(body=json.dumps(dict(message=f'No tag {self.request.match_info["id"]} database')),
                                        content_type='application/json')
            conn.execute('DELETE FROM tag WHERE id = $1', self.request.query['id'])
            await conn.close()
            return web.Response(
                body=json.dumps(dict(message=f'Successful delete tag {self.request.match_info["id"]}'), status=200,
                                content_type='application/json'))