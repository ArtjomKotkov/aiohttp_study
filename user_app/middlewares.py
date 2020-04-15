from aiohttp.web import middleware


@middleware
async def Auth(request, handler):
    request.user = 'asf'
    return await handler(request)
