import logging


def make_header(host: str, port: int) -> bytes:
    """ Build a ChainLink connection header from a host and port."""
    return f"NP={host}:{port}=NP".encode()


def parse_header(data: bytes) -> None:
    """ Parse a ChainLink connection header into a host and port."""
    if data[:3] == b"NP=" and data[-3:] == b"=NP":
        host, port = data[3:-3].split(b":")
        logging.debug("Parsed header: %s:%s", host, port)

        port = int(port, 10)
        return host, port