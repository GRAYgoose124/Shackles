import asyncio
from asyncio import transports
from functools import partial
import logging
from time import sleep

from .utils import make_header, parse_header


logger = logging.getLogger(__name__)


def phoenix_task(func, restart_delay=60):
    """ Returns a task which restarts on completion."""
    async def task():
        while True:
            func()
            await asyncio.sleep(restart_delay)


    return task()


class ChainLink(asyncio.Protocol):
    """ A peer in a web of peers.
    
    """
    factory = lambda fut, conf: partial(ChainLink, config=conf, future=fut)

    def __init__(self, future: asyncio.Future, config: dict = None) -> None:
        self.loop = asyncio.get_event_loop()
        self.future = future

        self.config = config
        
        self.peers = {}

        
    def connection_made(self, transport: transports.BaseTransport) -> None:
        pass
            
    def connection_lost(self, exc: Exception | None) -> None:
        if exc is not None:
            logger.error("Connection lost: %s", exc)

    def data_received(self, data: bytes) -> None:
        logger.debug("Data received: %s", data.decode())

        # Split the data into lines.
        lines = data.split(b"\n")
        for line in lines:
            if not line:
                continue

            addr = parse_header(line)
            if addr is not None:
                self._handle_new_peer(addr)
            elif line.startswith(b"ping:"):
                addr = parse_header(line[5:])
                print("ADDR:", addr)

                self._handle_peer_ping(addr)

    # Peer protocol handlers
    def _handle_new_peer(self, addr):
        """ Handle a new connection header received through the protocol. """
        if addr not in self.peers:
            host, port = addr

            peer_finished = self.loop.create_future()

            connect_task = self.loop.create_task(self.loop.create_connection(
                ChainLink.factory(peer_finished, {'addr': addr}), host, port
            ))

            connect_task.add_done_callback(self._peer_connected)
            # Return the future to the caller.
            return connect_task
  
    def _ping_peer(self, addr: tuple[str, int]) -> None:
        logger.debug("Pinging peer: %s", addr)

        transport, _ = self.peers[addr].result()
        transport.write(f"ping:{make_header(*self.config['addr']).decode()}\n".encode())

    def _handle_peer_ping(self, addr) -> None:
        if addr and addr not in self.peers:
            logger.debug("Received ping from new peer: %s", addr)
            connect_task = self._handle_new_peer(addr)
            # wait for the peer to connect.
            def l(f):
                print("PEERS", self.peers)
                self._handle_peer_ping(addr)
            connect_task.add_done_callback(l)
            return
        
        logger.debug("%s: PONG!", addr)
        self._ping_peer(addr)

    # Peer connection callbacks.
    def _peer_connected(self, future: asyncio.Future) -> None:    
        addr = future.result()[0].get_extra_info("peername")[:2]

        if addr not in self.peers:
            logger.debug("Peer connected: %s", addr)

            self.peers[addr] = future

            # Set up the reverse connection by sending a header with our address and port.
            future.result()[0].write(f"{make_header(*self.config['addr'])}\n".encode())

            # Set up a periodic task to ping the peer.
            self.loop.create_task(phoenix_task(partial(self._ping_peer, addr), 5))

    def _peer_finished(self, future: asyncio.Future) -> None:
        addr = future.result()[0].get_extra_info("peername")
        logger.debug("Peer finished: %s", addr)

        self.peers.pop(addr)
