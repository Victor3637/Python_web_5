import asyncio
from datetime import datetime
import logging
import re

from aiofile import async_open
import names
import websockets
from websockets import WebSocketServerProtocol
from websockets.exceptions import ConnectionClosedOK

from exchange import RequestHandler

logging.basicConfig(level=logging.INFO)


class Server:
    clients = set()

    async def register(self, ws: WebSocketServerProtocol):
        ws.name = names.get_full_name()
        self.clients.add(ws)
        logging.info(f'{ws.remote_address} connects')

    async def unregister(self, ws: WebSocketServerProtocol):
        self.clients.remove(ws)
        logging.info(f'{ws.remote_address} disconnects')

    async def exchange_message_handler(self, message: str):
        request_handler = RequestHandler(['EUR', 'USD'])
        try:
            days_amount = int(re.findall(r"\d+", message)[0])
        except (ValueError, IndexError):
            days_amount = 1
        data = await request_handler.get_exchange_rates(days_amount)
        msg = "Exchange rates:\n"
        for date, rates in data.items():
            msg += f"""{date}
    EUR:
        Sale: {rates['EUR']['sale']}
        Purchase: {rates['EUR']['purchase']}
    USD:
        Sale: {rates['USD']['sale']}
        Purchase: {rates['USD']['purchase']}\n"""

        if self.clients:
            [await client.send(msg) for client in self.clients]

    async def send_to_clients(self, message: str):
        if "exchange" in message:
            await self.exchange_message_handler(message)

        if self.clients:
            [await client.send(message) for client in self.clients]

    async def ws_handler(self, ws: WebSocketServerProtocol):
        await self.register(ws)
        try:
            await self.distrubute(ws)
        except ConnectionClosedOK:
            pass
        finally:
            await self.unregister(ws)

    async def distrubute(self, ws: WebSocketServerProtocol):
        async for message in ws:
            await self.send_to_clients(f"{ws.name}: {message}")


async def main():
    server = Server()
    async with websockets.serve(server.ws_handler, 'localhost', 8080):
        await asyncio.Future()

if __name__ == '__main__':
    asyncio.run(main())
