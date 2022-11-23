import logging


logger = logging.getLogger(__name__)


def make_header(host: str, port: int) -> bytes:
    """ Build a ChainLink connection header from a host and port."""
    return f"new:NP={host}|{port}=NP".encode()


def parse_header(data: bytes) -> None:
    """ Parse a ChainLink connection header into a host and port."""
    if data[:7] == b"new:NP=" and data[-3:] == b"=NP":
        host, port = data[7:-3].split(b"|")

        port = int(port, 10)
        return host, port