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

    where_condition, pos = milti_where("name", tags, 1, "OR")
    sql_response = await conn.fetch(f'SELECT * FROM tag WHERE {where_condition};', *tags)
    if len(sql_response) == len(tags):
        return True, [tag['id'] for tag in sql_response]
    else:
        return False, [tag['id'] for tag in sql_response]


async def check_art_has_tags(conn, art_id, tags: list, check_exist=True):
    """
    Check what tags art contain.
    If check exist = False, tags must be list of ids of tags, else it must be list of tags names.
    :param conn:
    :param art_id:
    :param tags:
    :return: list of not existent tags in the art and tags which art contain
    """
    if check_exist:
        exist, new_tags = await check_tags_existing(conn, tags)
    else:
        new_tags = tags
    expr = [f'tag_id = ${tag_index}' for tag_index in range(2, len(new_tags) + 2)]
    sql_response = await conn.fetch(f'SELECT * FROM tag_art WHERE art_id = $1 AND ({" OR ".join(expr)})',
                                    art_id, *new_tags)

    not_existent_tags = list(set(new_tags) - set([row['tag_id'] for row in sql_response]))
    if len(sql_response) == len(tags):
        return [], new_tags
    else:
        return not_existent_tags, [row['tag_id'] for row in sql_response]


async def add_tags_to_art(conn, art_id, tags: list):
    """
    Add tags to post with id art_id.
    Gets only tags that exist in databases and that do not yet exist in the art.
    :param conn: Connection instance asyncpg
    :param art_id:
    :param tags: list og tags
    :return:
    """
    not_existent_tags, ext_tags = await check_art_has_tags(conn, art_id, tags)
    if not not_existent_tags:
        return 'Art already have all this tags.'
    exp = [f'($1, ${i})' for i in range(2, len(not_existent_tags) + 2)]
    await conn.execute(f'INSERT INTO tag_art (art_id, tag_id) VALUES {", ".join(exp)};', art_id, *not_existent_tags)


async def delete_tags_from_art(conn, art_id, tags: list):
    not_ext_tags, ext_tags = await check_art_has_tags(conn, art_id, tags)
    if not ext_tags:
        return 'Art already doesn\'t have all this tags.'
    exp = [f'tag_id = ${i}' for i in range(2, len(ext_tags) + 2)]
    await conn.execute(f'DELETE FROM tag_art WHERE art_id = $1 AND ({" OR ".join(exp)});', art_id, *ext_tags)


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


def milti_where(field: str, list_, start: int, separator):
    """
    Create sql where condition.
    Return condition-str, and start + len(list_) + 1
    """
    pos = len(list_) + start
    return f" {separator} ".join([f'{field} = ${i}' for i in range(start, pos)]), pos


def sql_in(field: str, list_, start: int):
    """
    Create sql where condition.
    Return condition-str, and start + len(list_) + 1
    """
    pos = len(list_) + start

    return f"{field} IN ({', '.join([f'${i}' for i in range(start, pos)])})", pos


def record_to_dict(record):
    """ Convert record instance to dict"""
    print(record)
    if not isinstance(record, list):
        return [{key: value for key, value in record.items()}]
    else:
        return [{key: value for key, value in row.items()} for row in record]


async def check_exist(conn, table: str, id):
    check = await conn.fetchrow(f'SELECT * FROM {table} WHERE id = $1', int(id))
    return True if check else False


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
                                          VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9);""", name, description, path,
                                       datetime_,
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
            - tags: list of tags, which art have to contain.
        All arts sorted by datetime.
        :return:
        """
        data = self.request.query
        user = data.get('user', None)
        limit = data.get('limit', 40)
        offset = data.get('offset', 0)
        order = data.get('order', 'date')
        albums = data.get('albums', None)
        tags = data.get('tags', None)
        tags_ = None
        fields = ", ".join(['id', 'name', 'description', 'path', 'likes', 'views', 'date', 'width', 'height', 'owner',
                            'album_id'])
        async with self.request.app['db'].acquire() as conn:
            if tags:
                exist, tags_ids = await check_tags_existing(conn, tags.split(','))
            else:
                tags_ids = None

            where = []
            params = []
            start = 1
            from_ = 'FROM art'
            group_by = ''
            if user:
                where.append('art.owner = $1')
                params.append(user)
                start = 2
            if tags_ids:
                expr1, start = sql_in('tag_art.tag_id', tags_ids, start)
                from_ = 'FROM art INNER JOIN tag_art ON tag_art.art_id = art.id'
                group_by = f'GROUP BY art.id HAVING COUNT(art.id) = {len(tags_ids)}'
                where.append(expr1)
                for tag in tags_ids:
                    params.append(int(tag))
            if albums:
                albums = albums.split(',')
                expr3, start = sql_in('art.album_id', albums, start)
                where.append(expr3)
                for album in albums:
                    params.append(int(album))
            if where:
                where[0] = 'WHERE ' + where[0]
            sql_expression = f'SELECT DISTINCT {fields} {from_} {" AND ".join(where)} {group_by} ORDER BY {order} DESC LIMIT {limit} OFFSET {offset};'
            sql_response = await conn.fetch(sql_expression, *params)
            if sql_response and tags_ids:
                tags_ = [await art_tags(conn, art['id']) for art in sql_response]

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
                                             tags=tags) for row, tags in zip(sql_response, tags_)])
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
                                             height=row['height'],
                                             tags=None) for row in sql_response])
        return web.HTTPOk(body=json.dumps(dict_response), content_type='application/json')


@routers_content.view('/art/{id}')
class FileManager(web.View):

    async def get(self):
        """
        Return art with special id.
        Special params:
            - fields: list of db field, which needs to return.
        :return: Json response.
        """
        fields = self.request.query.getall('fields', None)
        if fields:
            fields_ = ', '.join(fields)
        else:
            fields_ = '*'
        async with self.request.app['db'].acquire() as conn:
            row = await conn.fetchrow(f"SELECT {fields_} FROM art WHERE id = $1;", int(self.request.match_info['id']))
            if not row:
                return web.HTTPNotFound(
                    body=json.dumps(dict(message=f'No art with id {self.request.match_info["id"]}.')))
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
                                         width=row['width'],
                                         height=row['height'])])
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


@routers_content.view('/tag_id/{id}')
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
                    body=json.dumps(dict(message=f'No art with id {self.request.match_info["id"]}.')),
                    content_type='application/json')
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
                                                     width=row['width'],
                                                     height=row['height'])])
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
                                                     width=row['width'],
                                                     height=row['height'])])
                    return web.HTTPOk(body=json.dumps(dict_response), content_type='application/json')


@routers_content.view('/comment')
class Comments(web.View):

    async def get(self):
        """
        Need art_id param in request query str.
        :return:
        """
        art_id = self.request.query.get('art', None)
        if not art_id:
            return web.HTTPBadRequest(body=json.dumps(dict(message='Не передано поле art_id')),
                                      content_type='application/json')
        async with self.request.app['db'].acquire() as conn:
            row = await conn.fetchrow("SELECT * FROM art WHERE id = $1;", int(art_id))
            if not row:
                return web.HTTPNotFound(
                    body=json.dumps(dict(message=f'No art with id {art_id}.')))
            comments = await art_comments(conn, int(art_id))
            if comments:
                response = dict(items=[dict(id=comment['id'],
                                            author=comment['author'],
                                            art_id=comment['art_id'],
                                            comment_id=comment['comment_id'],
                                            text=comment['text'],
                                            date=comment['date'].strftime('%y-%m-%d-%H-%M-%S')) for comment in
                                       comments])
                return web.HTTPOk(body=json.dumps(response), content_type='application/json')
            else:
                return web.HTTPOk(body=json.dumps(dict(message=None)), content_type='application/json')

    async def post(self):
        data = await self.request.json()
        async with self.request.app['db'].acquire() as conn:
            datetime_ = datetime.datetime.now()
            if 'art' in data and 'comment' not in data:
                await conn.execute('INSERT INTO comment (author, art_id, text, date) VALUES ($1, $2, $3, $4)',
                                   self.request.user.name, int(self.request.match_info['id']), data['text'])
            elif 'art' in data and 'comment' in data:
                await conn.execute(
                    'INSERT INTO comment (author, art_id, comment_id, text, date) VALUES ($1, $2, $3, $4, $5)',
                    self.request.user.name, data['art_id'], data['comment_id'], data, data['text'])
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

    async def put(self):
        """
        Update comment info
        Json args:
            - author
            - art_id
            - comment_id
            - text
            - date
        :return:
        """
        if self.request.can_read_body:
            data = await self.request.json()
        else:
            return web.HTTPBadRequest(body=json.dumps(dict(name='Неправильный запрос')),
                                      content_type='application/json')
        expr = [f'{param} = ${i}' for param, i in zip(data.keys(), range(1, len(data) + 1))]
        async with self.request.app['db'].acquire() as conn:
            sql_response = await conn.fetchrow(f"SELECT * FROM comment WHERE id = $1;",
                                               int(self.request.match_info['id']))
            if not sql_response:
                await conn.close()
                return web.HTTPNotFound(
                    body=json.dumps(dict(message=f'No comment {self.request.match_info["id"]} in database')),
                    content_type='application/json')
            await conn.execute(f'UPDATE comment SET {", ".join(expr)} WHERE id = ${len(data) + 1};',
                               *data.values(), int(self.request.match_info['id']))
            comment = await conn.fetchrow('SELECT * FROM comment WHERE id = $1;', int(self.request.match_info['id']))
            await conn.close()
            dict_response = dict(items=[dict(id=comment['id'],
                                             author=comment['author'],
                                             art_id=comment['art_id'],
                                             comment_id=comment['comment_id'],
                                             text=comment['text'],
                                             date=comment['date'].strftime('%y-%m-%d-%H-%M-%S'))])
            return web.HTTPOk(body=json.dumps(dict_response), content_type='application/json')


def dict_by_fields(fields, data):
    dict_ = {}
    for field in fields:
        dict_.update({field: data[field]})
    return dict_


@routers_content.view('/album')
class Albums(web.View):

    async def get(self):
        """
        Return list of albums in json format.

        Accept query string with params:
        limit: Limit of string in response.
        offset: Offset of rows in request.
        fields: Fields which have to be included in response.
        arts: How many arts needs to return with album, default 0, return only art name,path and id
        user: Filter bu user.

        :return: Json dict with items dict which contain list of albums.
        """
        data = self.request.query
        user = data.get('user', None)
        limit = data.get('limit', 40)
        offset = data.get('offset', 0)
        fields = data.get('fields', None)
        arts = data.get('arts', 0)
        fields = fields.split(',') if fields else fields
        # Create where condition and save params for searching.
        where = []
        params = []
        start = 1
        if user:
            where.append(f'owner = ${start}')
            params.append(user)
        if where:
            where[0] = 'WHERE ' + where[0]
        async with self.request.app['db'].acquire() as conn:
            sql_response = await conn.fetch(
                f'SELECT * FROM album {" AND ".join(where)} LIMIT {limit} OFFSET {offset};', *params)
            if fields:
                response = dict(
                    items=[dict_by_fields(fields, album) for album in sql_response]
                )
            else:
                response = dict(
                    items=[dict(
                        id=album['id'],
                        name=album['name'],
                        description=album['description'],
                        owner=album['owner'],
                    ) for album in sql_response]
                )
            return web.HTTPOk(body=json.dumps(response), content_type='application/json')

    async def post(self):
        """
        Create new album.
        Accept json type body with params:
        owner, description, owner
        :return: New album object.
        """
        data = await self.request.json()
        if not 'name' in data or not 'owner' in data:
            response = dict(message='No name or owner field in request body.')
            return web.HTTPBadRequest(body=json.dumps(response), content_type='application/json')
        async with self.request.app['db'].acquire() as conn:
            # Check owner exist.
            owner = await conn.fetchrow('SELECT * FROM users WHERE name = $1;', data['owner'])
            if not owner:
                response = dict(message=f'No user with name {data["owner"]}.')
                print(response)
                return web.HTTPNotFound(body=json.dumps(response), content_type='application/json')
            indexes = (f'${i}' for i in range(1, len(data.keys()) + 1))
            str_ = f'INSERT INTO album ({", ".join(data.keys())}) VALUES ({", ".join(indexes)});'
            await conn.execute(str_, *data.values())
            sql_response = await conn.fetchrow('SELECT * FROM album ORDER BY id DESC LIMIT 1;')
            response = dict(
                items=[dict(
                    id=sql_response['id'],
                    name=sql_response['name'],
                    description=sql_response['description'],
                    owner=sql_response['owner'],
                )]
            )
            return web.HTTPCreated(body=json.dumps(response), content_type='application/json')


@routers_content.view('/album/{id}')
class Album(web.View):

    async def get(self):
        """
        Return items list with only one album.

        Accept query string with params:
        fields: Fields which have to be included in response.

        :return: Json dict with items dict which contain list with album.
        """
        fields = self.request.query.get('fields', '*')
        fields = fields.split(',') if fields != '*' else fields
        async with self.request.app['db'].acquire() as conn:
            sql_response = await conn.fetchrow(f'SELECT {", ".join(fields)} FROM album WHERE id = $1;',
                                               int(self.request.match_info['id']))
            if not sql_response:
                response = dict(message=f'No album with id {self.request.match_info["id"]}.')
                return web.HTTPNotFound(body=json.dumps(response), content_type='application/json')
            response = dict(items=record_to_dict(sql_response))
        return web.HTTPOk(body=json.dumps(response), content_type='application/json')

    async def delete(self):
        """Delete album by id."""
        async with self.request.app['db'].acquire() as conn:
            if not await check_exist(conn, 'album', self.request.match_info['id']):
                response = dict(message=f'No album with id {self.request.match_info["id"]}.')
                return web.HTTPNotFound(body=json.dumps(response), content_type='application/json')
            await conn.fetchrow("DELETE FROM album WHERE id = $1;", int(self.request.match_info['id']))
        response = dict(message='Album successfuly deleted.')
        return web.HTTPOk(body=json.dumps(response), content_type='application/json')

    async def put(self):
        """Update data about album"""
        if not self.request.can_read_body:
            response = dict(message='Empty request body.')
            return web.HTTPBadRequest(body=json.dumps(response), content_type='application/json')
        data = await self.request.json()
        expr = [f'{param} = ${i}' for param, i in zip(data.keys(), range(1, len(data) + 1))]
        async with self.request.app['db'].acquire() as conn:
            await conn.execute(f"UPDATE album SET {', '.join(expr)} WHERE id = ${len(data) + 1};", *data.values(),
                               int(self.request.match_info['id']))
            sql_response = await conn.fetchrow('SELECT * FROM album WHERE id = $1;', int(self.request.match_info['id']))
            response = dict(
                items=[dict(
                    id=sql_response['id'],
                    name=sql_response['name'],
                    description=sql_response['description'],
                    owner=sql_response['owner'],
                )]
            )
            return web.HTTPOk(body=json.dumps(response), content_type='application/json')

    async def post(self):
        """Add art with id in body to album."""
        if not self.request.can_read_body:
            response = dict(message='Empty request body.')
            return web.HTTPBadRequest(body=json.dumps(response), content_type='application/json')
        data = await self.request.json()
        async with self.request.app['db'].acquire() as conn:
            if not await check_exist(conn, 'album', self.request.match_info['id']):
                response = dict(message=f'No album with id {self.request.match_info["id"]}.')
                return web.HTTPNotFound(body=json.dumps(response), content_type='application/json')
            if not await check_exist(conn, 'art', int(data['id'])):
                response = dict(message=f'No art with id {int(data["id"])}.')
                return web.HTTPNotFound(body=json.dumps(response), content_type='application/json')
            await conn.execute('UPDATE art SET album_id=$1 WHERE id = $2;', int(self.request.match_info['id']),
                               int(data['id']))
            response = dict(message='Successful update.')
            return web.HTTPOk(body=json.dumps(response), content_type='application/json')
