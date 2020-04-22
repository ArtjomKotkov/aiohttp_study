import aiohttp
from aiohttp import web
from aiohttp_session import get_session

routers_chat = web.RouteTableDef()

async def close_all(app):
    for owner_username in app['chat']['user_web_sockets']:
        for ws in owner_username.values():
            ws.close()
    for owner_username in app['chat']['anon_web_sockets']:
        for ws in owner_username:
            ws.close()



@routers_chat.view('/{user_name}')
class UserChat(web.View):

    async def broadcast(self, message):
        """
        Send message to all users of current chat
        """
        owner_username = self.request.match_info['user_name']
        # Send fo all authorized peers
        if owner_username in self.request.app['chat']['user_web_sockets']:
            for ws in self.request.app['chat']['user_web_sockets'][owner_username].values():
                response = dict(username=self.request.user.name, message=message)
                await ws.send_json(response)
        # Send fo all unauthorized peers
        if owner_username in self.request.app['chat']['anon_web_sockets']:
            for ws in self.request.app['chat']['anon_web_sockets'][owner_username]:
                response = dict(username=self.request.user.name, message=message)
                await ws.send_json(response)

    async def get(self):
        # Init WebSockets
        ws = web.WebSocketResponse()
        await ws.prepare(self.request)
        # Get owner of page name
        owner_username = self.request.match_info['user_name']
        # Check peer authentication
        if self.request.user.is_authenticated:
            # Init user non anon webSocket
            owner_wsdict = self.request.app['chat']['user_web_sockets']
            # Collect webSocket
            if owner_username not in owner_wsdict:
                owner_wsdict[owner_username] = {self.request.user.name: ws}
            else:
                owner_wsdict[owner_username].update({self.request.user.name: ws})
            # Send message
            async for msg in ws:
                if msg.type == aiohttp.WSMsgType.TEXT:
                    await self.broadcast(msg.data)
            # Close connection
            owner_wsdict[owner_username].pop(self.request.user.name)
            if len(owner_wsdict[owner_username]) == 0:
                del owner_wsdict[owner_username]
            return ws
        else:
            # Init user anon webSocket
            owner_wsdict = self.request.app['chat']['anon_web_sockets']
            # Collect websocket
            if owner_username not in owner_wsdict:
                owner_wsdict[owner_username] = [ws]
            else:
                owner_wsdict[owner_username].append(ws)
            # Send error response
            async for msg in ws:
                if msg.type == aiohttp.WSMsgType.TEXT:
                    response = dict(username='SERVER', message='You must be authorize!')
                    await ws.send_json(response)
            # Close connection
            owner_wsdict[owner_username].remove(ws)
            if len(owner_wsdict[owner_username]) == 0:
                del owner_wsdict[owner_username]
            return ws
