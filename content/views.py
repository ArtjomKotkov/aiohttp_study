import datetime
import os
import json
import pprint

from PIL import Image
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


# Easy way to check, which tags are in db, or add new to art

async def check_tags_existing(conn, tags: list):
    """
    Check which of tags are in db
    :param conn: connection to engine
    :param tags: list of tags
    :return: boolean, and ids of every tag, which are in database
    """
    expr = [f'name = ${tag_index}' for tag_index in range(1, len(tags) + 1)]
    sql_response = await conn.fetch(f'SELECT * FROM tag WHERE {" OR ".join(expr)};', *tags)
    if len(sql_response) == len(tags):
        return True, [tag['id'] for tag in sql_response]
    else:
        return False, [tag['id'] for tag in sql_response]


async def check_art_has_tags(conn, art_id, tags: list):
    """
    Check what tags art contain.
    :param conn:
    :param art_id:
    :param tags:
    :return:
    """
    exist, new_tags = await check_tags_existing(conn, tags)
    expr = [f'tag_id = ${tag_index}' for tag_index in range(2, len(new_tags) + 2)]
    sql_response = await conn.fetch(f'SELECT * FROM tag_art WHERE art_id = $1 AND ({" OR ".join(expr)})', art_id,
                                    *new_tags)
    if len(sql_response) == len(tags):
        return True, new_tags
    else:
        return False, new_tags


async def add_tags_to_art(conn, art_id, tags: list):
    """
    Add tags to post with id art_id.
    Gets only tags that exist in databases and that do not yet exist in the art.
    :param conn: Connection instance asyncpg
    :param art_id:
    :param tags: list og tags
    :return:
    """
    exist, new_tags = check_art_has_tags(conn, art_id, tags)
    new_tags = list(set(tags) - set(new_tags))
    if not new_tags:
        return 'Art already have all this tags.'
    exp = [f'($1, ${i}' for i in range(2, len(new_tags) + 2)]
    conn.execute(f'INSERT INTO tag_art (art_id, tag_name) VALUES {", ".join(exp)};', art_id, *new_tags)


async def delete_tags_from_art(conn, art_id, tags: list):
    exist, new_tags = check_art_has_tags(conn, art_id, tags)
    if not new_tags:
        return 'Art already doesn\'t have all this tags.'
    exp = [f'tag_id = ${i}' for i in range(2, len(new_tags) + 2)]
    conn.execute(f'DELETE FROM tag_art WHERE art_id = $1 AND ({" OR ".join(exp)});', art_id, *new_tags)


async def art_tags(conn, art_id):
    """
    :param conn:
    :param art_id:
    :param tags:
    :return: Dict of tags for art_id
    """

    sql_response = await conn.fetch(
        f'SELECT * FROM tag INNER JOIN tag_art ON tag.id = tag_art.tag_id WHERE art_id = $1;', int(art_id))
    if sql_response:
        return {tag['id']: tag['name'] for tag in sql_response}
    else:
        return None

async def art_comments(conn, art_id):
    sql_response = await conn.fetch(f'SELECT * FROM comment WHERE art_id = $1 ORDER BY date DESC;', int(art_id))
    if sql_response:
        return sql_response
    else:
        return None


@routers_content.view('/art', name='art')
class FilesManager(web.View):
    async def post(self):
        """
        Upload new file.
        Request format:
            - file
            - name
            - description
            - onwer (user name)
            - tags
        :return:
        """
        reader = await self.request.multipart()
        description = None
        name = None
        path = None
        user = self.request.user.name
        tags = None
        datetime_ = datetime.datetime.now()
        dict_response = None
        width = None
        height = None
        while True:
            field = await reader.next()
            if not field:
                if not name or not user:
                    return web.HTTPBadRequest(
                        body=json.dumps(dict(message=f'No required fields!')))
                async with self.request.app['db'].acquire() as conn:
                    await conn.execute("""INSERT INTO art (name, description, path, date, owner, likes, views, width, height) 
                                          VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9);""", name, description, path, datetime_,
                                       self.request.user.name, 0, 0, width, height)
                    row = await conn.fetchrow('SELECT * FROM art WHERE path = $1;', path)
                    # Add taqs to art.
                    if tags:
                        await add_tags_to_art(conn, row['id'], tags)
                    await conn.close()
                    dict_response = dict(items=[dict(id=row['id'],
                                                     name=row['name'],
                                                     description=row['description'],
                                                     path=row['path'],
                                                     likes=row['likes'],
                                                     views=row['views'],
                                                     date=row['date'].strftime('%y-%m-%d-%H-%M-%S'),
                                                     owner=row['owner'],
                                                     width=row['width'],
                                                     height=row['height'])])
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
                with Image.open(MEDIA_ROOT / self.request.user.name / new_name) as image:
                    width = image.width
                    height = image.height
            if field.name == 'user':
                name = (await field.read()).decode('utf-8')
            if field.name == 'name':
                name = (await field.read()).decode('utf-8')
            if field.name == 'description':
                description = (await field.read()).decode('utf-8')
            if field.name == 'tags':
                tags = list((await field.read()).decode('utf-8'))
        return web.HTTPCreated(body=json.dumps(dict_response), content_type='application/json')

    async def get(self):
        """
        Get list of all arts.
        Special params:
            - user : name of user which arts need to return
            - limit : limit of arts in response | default = 40
            - offset : offset from start | default = 0
            - order: [date, views, likes] | default = date
            - tags: list of tags, which art have to contain
        All arts sorted by datetime.
        :return:
        """
        data = self.request.query
        user = data.get('user', None)
        limit = data.get('limit', 40)
        offset = data.get('offset', 0)
        order = data.get('order', 'date')
        tags = self.request.query.getall('tags', None)
        tags_ = None
        async with self.request.app['db'].acquire() as conn:
            if tags:
                tags_ids = await check_tags_existing(conn, tags)
            else:
                tags_ids = None
            if user and tags_ids:
                expr = [f'tag_art.tag_id = ${i}' for i in range(2, len(tags_ids + 2))]
                where = f'{" OR ".join(expr)}'
                sql_request = await conn.fetch(
                    f'SELECT * FROM art INNER JOIN tag_art ON tag_art.art_id = art.id WHERE art.owner = $1 AND {where} ORDER BY {order} DESC LIMIT {limit} OFFSET {offset};',
                    user)
                tags_ = [await art_tags(conn, art['id']) for art in sql_request]
            elif not user and tags_ids:
                expr = [f'tag_art.tag_id = ${i}' for i in range(1, len(tags_ids + 1))]
                where = f'AND {" OR ".join(expr)}'
                sql_request = await conn.fetch(
                    f'SELECT * FROM art INNER JOIN tag_art ON tag_art.art_id = art.id WHERE {where} ORDER BY {order} DESC LIMIT {limit} OFFSET {offset};',
                    user)
                tags_ = [await art_tags(conn, art['id']) for art in sql_request]
            elif user and not tags_ids:
                sql_request = await conn.fetch(
                    f'SELECT * FROM art WHERE art.owner = $1 ORDER BY {order} DESC LIMIT {limit} OFFSET {offset};',
                    user)
            else:
                sql_request = await conn.fetch(
                    f'SELECT * FROM art ORDER BY {order} DESC LIMIT {limit} OFFSET {offset};')
            await conn.close()
        if tags_:
            dict_response = dict(items=[dict(id=row['id'],
                                         name=row['name'],
                                         description=row['description'],
                                         path=row['path'],
                                         likes=row['likes'],
                                         views=row['views'],
                                         date=row['date'].strftime('%y-%m-%d-%H-%M-%S'),
                                         owner=row['owner'],
                                         width=row['width'],
                                         height=row['height'],
                                         tags=tags) for row, tags in zip(sql_request, tags_)])
        else:
            dict_response = dict(items=[dict(id=row['id'],
                                             name=row['name'],
                                             description=row['description'],
                                             path=row['path'],
                                             likes=row['likes'],
                                             views=row['views'],
                                             date=row['date'].strftime('%y-%m-%d-%H-%M-%S'),
                                             owner=row['owner'],
                                             width=row['width'],
                                             height=row['height']) for row in sql_request])
        return web.HTTPOk(body=json.dumps(dict_response), content_type='application/json')


@routers_content.view('/art/{id}')
class FileManager(web.View):

    async def get(self):
        """
        Return art with special id.

        :return: Json response.
        """
        async with self.request.app['db'].acquire() as conn:
            row = await conn.fetchrow("""SELECT * FROM art
                                                WHERE id = $1;""", int(self.request.match_info['id']))
        if not row:
            return web.HTTPNotFound(body=json.dumps(dict(message=f'No art with id {self.request.match_info["id"]}.')))
        else:
            tags = await art_tags(conn, row['id'])
            comments = await art_comments(conn, int(self.request.match_info["id"]))
            dict_response = dict(items=[dict(id=row['id'],
                                             name=row['name'],
                                             description=row['description'],
                                             path=row['path'],
                                             likes=row['likes'],
                                             views=row['views'],
                                             date=row['date'].strftime('%y-%m-%d-%H-%M-%S'),
                                             owner=row['owner'],
                                             tags=tags,
                                             commets=comments,
                                             width=row['width'],
                                             height=row['height'])])
            return web.HTTPOk(body=json.dumps(dict_response), content_type='application/json')

    async def delete(self):
        async with self.request.app['db'].acquire() as conn:
            row = await conn.fetchrow("""SELECT * FROM art
                                                WHERE id = $1;""", int(self.request.match_info['id']))
            if not row:
                await conn.close()
                return web.HTTPNotFound(
                    body=json.dumps(dict(message=f'No art with id {self.request.match_info["id"]}.')))
            else:
                await conn.execute("""DELETE FROM art
                                      WHERE id = $1""", int(self.request.match_info['id']))
                await conn.close()
                return web.HTTPOk(
                    body=json.dumps(dict(message=f'Successful delete art {self.request.match_info["id"]}')),
                    content_type='application/json')

    async def put(self):
        """
        Update art instance, accept all params from art model.
        :return: Updated art instance.
        """
        data = await self.request.json()
        expr = [f'{param} = ${i}' for param, i in zip(data.keys(), range(1, len(data) + 1))]
        async with self.request.app['db'].acquire() as conn:
            row = await conn.fetchrow('SELECT * FROM art WHERE id = $1;', int(self.request.match_info['id']))
            if not row:
                await conn.close()
                return web.HTTPNotFound(
                    body=json.dumps(dict(message=f'No art with id {self.request.match_info["id"]}.')))
            await conn.execute(f'UPDATE art SET {", ".join(expr)} WHERE id = ${len(data) + 1};',
                               *data.values(), int(self.request.match_info['id']))
            row = await conn.fetchrow('SELECT * FROM art WHERE id = $1;', int(self.request.match_info['id']))
            if 'tags' in data:
                await add_tags_to_art(conn, int(self.request.match_info['id']), list(data['tags']))
        tags = await art_tags(conn, row['id'])
        dict_response = dict(items=[dict(id=row['id'],
                                         name=row['name'],
                                         description=row['description'],
                                         path=row['path'],
                                         likes=row['likes'],
                                         views=row['views'],
                                         date=row['date'].strftime('%y-%m-%d-%H-%M-%S'),
                                         owner=row['owner'],
                                         tags=tags,
                                         width = row['width'],
                                         height = row['height'])])
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
            return web.HTTPNotFound(body=json.dumps(dict(message='No tags in database')),
                                    content_type='application/json')
        return web.Response(body=json.dumps(dict_response), status=200, content_type='application/json')

    async def post(self):
        """
        Create new tag.
        Query args:
            - name
        :return:
        """
        if self.request.can_read_body:
            data = await self.request.json()
        else:
            data = {}
        name = data.get('name', None)
        if not name:
            return web.HTTPBadRequest(body=json.dumps(dict(name='Не передано поле name')),
                                      content_type='application/json')
        async with self.request.app['db'].acquire() as conn:
            tag = await conn.fetchrow('SELECT * FROM tag WHERE name = $1;', name)
            if not tag:
                await conn.execute('INSERT INTO tag (name) VALUES ($1);', name)
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
            sql_response = await conn.fetchrow(f"SELECT * FROM tag WHERE id = $1;",
                                               int(self.request.match_info['id']))
            await conn.close()
        if not sql_response:
            return web.HTTPNotFound(body=json.dumps(dict(message='No tags in database')),
                                    content_type='application/json')
        dict_response = dict(items=[dict(id=sql_response['id'], name=sql_response['name'])])
        return web.Response(body=json.dumps(dict_response), status=200, content_type='application/json')

    async def put(self):
        """
        Update tag info
        Json args:
            - name
        :return:
        """
        if self.request.can_read_body:
            data = await self.request.json()
        else:
            return web.HTTPBadRequest(body=json.dumps(dict(name='Неправильный запрос')),
                                      content_type='application/json')
        expr = [f'{param} = ${i}' for param, i in zip(data.keys(), range(1, len(data) + 1))]
        async with self.request.app['db'].acquire() as conn:
            sql_response = await conn.fetchrow(f"SELECT * FROM tag WHERE id = $1;",
                                               int(self.request.match_info['id']))
            if not sql_response:
                await conn.close()
                return web.HTTPNotFound(
                    body=json.dumps(dict(message=f'No tag {self.request.match_info["id"]} database')),
                    content_type='application/json')
            await conn.execute(f'UPDATE tag SET {", ".join(expr)} WHERE id = ${len(data) + 1};',
                               *data.values(), int(self.request.match_info['id']))
            sql_response = await conn.fetchrow('SELECT * FROM tag WHERE id = $1;', int(self.request.match_info['id']))
            await conn.close()
            dict_response = dict(items=[dict(id=sql_response['id'], name=sql_response['name'])])
            return web.HTTPOk(body=json.dumps(dict_response), content_type='application/json')

    async def delete(self):
        async with self.request.app['db'].acquire() as conn:
            sql_response = await conn.fetchrow(f"SELECT * FROM tag WHERE id = $1;",
                                               int(self.request.match_info['id']))
            if not sql_response:
                await conn.close()
                return web.HTTPNotFound(
                    body=json.dumps(dict(message=f'No tag {self.request.match_info["id"]} database')),
                    content_type='application/json')
            await conn.execute('DELETE FROM tag WHERE id = $1;', int(self.request.match_info['id']))
            await conn.close()
            return web.HTTPOk(body=json.dumps(dict(message=f'Successful delete tag {self.request.match_info["id"]}')),
                              content_type='application/json')


@routers_content.view('/tag/add/{art_id}')
class ForeignTag(web.View):

    async def post(self):
        """
        Add tags to art.
        :return:
        """
        data = await self.request.json()
        async with self.request.app['db'].acquire() as conn:
            row = await conn.fetchrow("SELECT * FROM art WHERE id = $1;", int(self.request.match_info['id']))
            if not row:
                return web.HTTPNotFound(
                    body=json.dumps(dict(message=f'No art with id {self.request.match_info["id"]}.')))
            else:
                error = await add_tags_to_art(conn, int(self.request.match_info['id']), data['tags'])
                if error:
                    return web.HTTPConflict(body=json.dumps(dict(message=error)), content_type='application/json')
                else:
                    row = await conn.fetchrow("SELECT * FROM art WHERE id = $1;", int(self.request.match_info['id']))
                    tags = await art_tags(conn, row['id'])
                    dict_response = dict(items=[dict(id=row['id'],
                                                     name=row['name'],
                                                     description=row['description'],
                                                     path=row['path'],
                                                     likes=row['likes'],
                                                     views=row['views'],
                                                     date=row['date'].strftime('%y-%m-%d-%H-%M-%S'),
                                                     owner=row['owner'],
                                                     tags=tags,
                                                     width = row['width'],
                                                     height = row['height'])])
                    return web.HTTPOk(body=json.dumps(dict_response), content_type='application/json')

    async def delete(self):

        data = await self.request.json()
        async with self.request.app['db'].acquire() as conn:
            row = await conn.fetchrow("SELECT * FROM art WHERE id = $1;", int(self.request.match_info['id']))
            if not row:
                return web.HTTPNotFound(
                    body=json.dumps(dict(message=f'No art with id {self.request.match_info["id"]}.')))
            else:
                error = await delete_tags_from_art(conn, int(self.request.match_info['id']), data['tags'])
                if error:
                    return web.HTTPConflict(body=json.dumps(dict(message=error)), content_type='application/json')
                else:
                    row = await conn.fetchrow("SELECT * FROM art WHERE id = $1;", int(self.request.match_info['id']))
                    tags = await art_tags(conn, row['id'])
                    dict_response = dict(items=[dict(id=row['id'],
                                                     name=row['name'],
                                                     description=row['description'],
                                                     path=row['path'],
                                                     likes=row['likes'],
                                                     views=row['views'],
                                                     date=row['date'].strftime('%y-%m-%d-%H-%M-%S'),
                                                     owner=row['owner'],
                                                     tags=tags,
                                                     width = row['width'],
                                                     height = row['height'])])
                    return web.HTTPOk(body=json.dumps(dict_response), content_type='application/json')


@routers_content.view('/comment')
class Comment(web.View):

    async def get(self):
        """
        Need art_id param in request body.
        :return:
        """
        data = await self.request.json()
        if not data['art_id']:
            return web.HTTPBadRequest(body=json.dumps(dict(name='Не передано поле art_id')),
                                      content_type='application/json')
        async with self.request.app['db'].acquire() as conn:
            row = await conn.fetchrow("SELECT * FROM art WHERE id = $1;", int(data['art_id']))
            if not row:
                return web.HTTPNotFound(
                    body=json.dumps(dict(message=f'No art with id {data["art_id"]}.')))
            comments = await art_comments(conn, data['art_id'])
            return web.HTTPOk(body=json.dumps(comments), content_type='application/json')


    async def post(self):
        data = await self.request.json()
        async with self.request.app['db'].acquire() as conn:
            if 'art' in data and 'comment' not in data:
                conn.execute('INSERT INTO comment (author, art_id, text) VALUES ($1, $2, $3)', self.request.user.name,
                             int(self.request.match_info['id']), data['text'])
            elif 'art' in data and 'comment' in data:
                conn.execute('INSERT INTO comment (author, art_id, comment_id, text) VALUES ($1, $2, $3, $4)',
                             self.request.user.name,
                             data['art_id'], data['comment_id'], data, data['text'])
            return web.HTTPOk(body=json.dumps(data), content_type='application/json')


@routers_content.view('/comment/{id}')
class Comment(web.View):

    async def delete(self):
        async with self.request.app['db'].acquire() as conn:
            sql_check = await conn.fetchrow('SELECT * FROM comment WHERE id = $1;', int(self.request.match_info['id']))
            if not sql_check:
                return web.HTTPNotFound(
                    body=json.dumps(dict(message=f'No comment with id {self.request.match_info["id"]}.')))
            else:
                await conn.execute('DELETE FROM comment WHERE id = $1;', int(self.request.match_info['id']))
                return web.HTTPOk(body=json.dumps(dict(message='Comment successfuly deleted')),
                                  content_type='application/json')
