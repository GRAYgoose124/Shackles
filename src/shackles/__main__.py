import asyncio
import logging

from .manager import RingManager


def main():
    asyncio.run(async_main())


async def async_main():
    logging.basicConfig(level=logging.DEBUG)

    LOCAL_PORTS = range(9600, 9610)
    HOSTS = [('localhost', port) for port in LOCAL_PORTS]

    loop = asyncio.get_event_loop()

    ring = RingManager(loop)
    await ring.build(HOSTS)

    await ring.run()


if __name__ == "__main__":
    # Poetry runs main() directly, this is for compatibility.
    main()





 