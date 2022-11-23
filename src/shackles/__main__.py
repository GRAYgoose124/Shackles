import asyncio
import logging

from .manager import RingManager


def main():
    logging.basicConfig(level=logging.INFO, format="%(name)s> %(message)s")
    
    # filter out everything but the client logger
    logging.getLogger("shackles.client").setLevel(logging.DEBUG)

    asyncio.run(async_main())


async def async_main():
    LOCAL_PORTS = range(9600, 9610)
    HOSTS = [('::1', port) for port in LOCAL_PORTS]

    loop = asyncio.get_event_loop()

    ring = RingManager(loop)
    await ring.build(HOSTS)

    try:
        await ring.run()
    except asyncio.exceptions.CancelledError:
        pass

if __name__ == "__main__":
    # Poetry runs main() directly, this is for compatibility.
    main()





 