import asyncio
from asyncio import transports
from functools import partial
import logging

from .utils import parse_header

class ChainLink(asyncio.Protocol):
    """ A peer in a web of peers.
    
    """
    factory = lambda fut: partial(ChainLink, config={}, future=fut)

    def __init__(self, future: asyncio.Future, config: dict = None) -> None:
        self.loop = asyncio.get_event_loop()
        self.future = future
        self.transports = {}

        self.config = config
        
        self.peers = []
        self.log = []

    def connection_made(self, transport: transports.BaseTransport) -> None:
        addr = transport.get_extra_info("peername")
        logging.debug("Connection made to %s", addr)

        self.transports[addr] = transport
        
    def connection_lost(self, exc: Exception | None) -> None:
        logging.debug("Connection lost %s", exc)

    def data_received(self, data: bytes) -> None:
        logging.debug("Data received: %s", data.decode())
        self.log.append(data)

        self._new_connection(data)

    def _new_connection(self, data):
        peer_finished = self.loop.create_future()

        addr = parse_header(data)
        if addr:
            host, port = addr
        else: 
            return

        task = self.loop.create_task(self.loop.create_connection(
            ChainLink.factory(peer_finished), host, port
        ))

        task.add_done_callback(self._peer_connected)

    def _peer_connected(self, future: asyncio.Future) -> None:    
        logging.debug("Peer connected")
        self.peers.append(future)

    
    def _peer_finished(self, future: asyncio.Future) -> None:
        logging.debug("Peer finished")
        self.peers.remove(future)