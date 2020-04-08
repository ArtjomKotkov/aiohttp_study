from aiohttp import web

async def main_view(request):
    return web.Response(text='Hello!')