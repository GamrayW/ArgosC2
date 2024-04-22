import asyncio


def uncorrupt_data(data):
    final_string = ""
    for char in data:
        final_string += chr(char)

    return final_string


class ServerHandler(asyncio.Protocol):
    def connection_made(self, transport):
        """
        Called by asyncio on connection
        """
        self.transport = transport
        self.transport.write(b"powershell.exe ls C:/")

    def data_received(self, data):
        """
        Called by asyncio when data is received
        """
        message = uncorrupt_data(data)
        remote = self.transport.get_extra_info('peername')[0]
        print(f"{remote}: {message}")
        self.transport.close()


async def main():
    loop = asyncio.get_running_loop()

    server = await loop.create_server(ServerHandler, '0.0.0.0', 13337)
    async with server:
        await server.serve_forever()


asyncio.run(main())
