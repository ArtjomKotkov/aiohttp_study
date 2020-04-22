import datetime
import os

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
class FileManager(web.View):
    async def post(self):
        reader = await self.request.multipart()
        description = None
        name = None
        path = None
        while True:
            field = await reader.next()
            if not field:
                async with self.request.app['db'].acquire() as conn:
                    await conn.execute('INSERT INTO art (name, description, path)'
                              'VALUES ($1, $2, $3)', name, description, path)
                    await conn.close()
                break
            if field.name == 'file':
                datetime_ = datetime.datetime.now()
                source_name, source_extension = os.path.splitext(field.filename)
                new_name = source_name+datetime_.strftime('%y-%m-%d-%H-%M-%S')+source_extension
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
        raise web.HTTPOk(text='Success')


