import asyncio


class ServerHandler(asyncio.Protocol):
    def connection_made(self, transport):
        """
        Called by asyncio on connection
        """
        self.transport = transport
        self.transport.write(b"agbhnj,kfvtgbyhnurftgyhuj")

    def data_received(self, data):
        """
        Called by asyncio when data is received
        """
        message = data.decode()
        remote = self.transport.get_extra_info('peername')[0]
        print(f"{remote}: {message}")
        self.transport.close()


async def main():
    loop = asyncio.get_running_loop()

    server = await loop.create_server(ServerHandler, '0.0.0.0', 13337)
    async with server:
        await server.serve_forever()


asyncio.run(main())