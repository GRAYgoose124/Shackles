import asyncio
import logging
from functools import partial

from .client import ChainLink


class RingManager:
    factory = lambda fut: partial(ChainLink, config={}, future=fut)

    def __init__(self, loop=None) -> None:
        if loop is None:
            self.loop = asyncio.get_event_loop()
        else:
            self.loop=loop
        
        self.reset()

    def reset(self):
        self.peers = {}

    def cancel_all(self):
        for peer, future in zip(self.peers.values(), self.futures.values()):
            peer.close()
            future.cancel()

        self.reset()

    def add_peer(self, future, peer, addr) -> None:
        logging.debug("Adding peer %s", addr)
        self.peers[addr] = (peer, future)

    async def build(self, hosts):
        for addr in hosts:
            server_finished = self.loop.create_future()
            peer = await self.loop.create_server(
                RingManager.factory(server_finished), addr[0], addr[1], ssl=None
            )

            self.add_peer(server_finished, peer, addr)

    async def connect(self, a1, a2):
        transport, _ = await self.loop.create_connection(
            RingManager.factory(None), a1[0], a1[1]
        )

        transport.write(f"NP={a2[0]}:{a2[1]}\n".encode())
        transport.close()

    async def connect_peers(self):
        logging.debug("Connecting peers")
        for a1, a2 in zip(self.peers.keys(), list(self.peers.keys())[1:]):
            if a1 == a2:
                continue
            # Loopback
            if a2 is None:
                a2 = self.peers[0][0]

            logging.debug("Connecting %s to %s", a1, a2)
            await self.connect(a1, a2)

    async def run(self):
        logging.debug("Starting ring manager")
        await self.connect_peers()

        futures = asyncio.gather(*[peer[1] for peer in self.peers.values()])
        await futures