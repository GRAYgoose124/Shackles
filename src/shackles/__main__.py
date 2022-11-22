import asyncio
import logging
from asyncio import transports
from functools import partial

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

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

        task.add_done_callback(partial(self._peer_connected, peer_finished))

    def _peer_connected(self, future: asyncio.Future) -> None:    
        logging.debug("Peer connected")
        self.peers.append(future)

    
    def _peer_finished(self, future: asyncio.Future) -> None:
        logging.debug("Peer finished")
        self.peers.remove(future)



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
        logger.debug("Connecting peers")
        for a1, a2 in zip(self.peers.keys(), list(self.peers.keys())[1:]):
            if a1 == a2:
                continue
            # Loopback
            if a2 is None:
                a2 = self.peers[0][0]

            logging.debug("Connecting %s to %s", a1, a2)
            await self.connect(a1, a2)

    async def run(self):
        logger.debug("Starting ring manager")
        await self.connect_peers()

        futures = asyncio.gather(*[peer[1] for peer in self.peers.values()])
        await futures


def main():
    asyncio.run(async_main())

async def async_main():
    LOCAL_PORTS = range(9600, 9610)
    HOSTS = [('localhost', port) for port in LOCAL_PORTS]

    loop = asyncio.get_event_loop()

    ring = RingManager(loop)
    await ring.build(HOSTS)

    await ring.run()


if __name__ == "__main__":
    # Poetry runs main() directly, this is for compatibility.
    main()





 