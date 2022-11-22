import asyncio
from asyncio import transports
import logging


class ChainLink(asyncio.Protocol):
    """ peer
    
    """
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

    @staticmethod
    def _parse_header(data: bytes) -> None:
        # Header = f"NP={host}:{port}\n"
        if data[:2] == b"NP=" and data[-1] == b"\n":
            host, port = data[3:-1].split(b":")
            port = int(port, 10)
            return host, port

    def _new_connection(self, data):
        peer_finished = self.loop.create_future()

        addr = self._parse_header(data)
        if addr:
            host, port = addr
        else: 
            return

        task = self.loop.create_task(self.loop.create_connection(
            RingManager.factory(peer_finished), host, port
        ))
        print(task)

        task.add_done_callback(partial(self._peer_connected, peer_finished))

    def _peer_connected(self, future: asyncio.Future) -> None:    
        logging.debug("Peer connected")
        self.peers.append(future)

    
    def _peer_finished(self, future: asyncio.Future) -> None:
        logging.debug("Peer finished")
        self.peers.remove(future)