#!/usr/bin/env python3

import argparse, asyncio

from irctokens import build
from ircrobots import Bot as BaseBot
from ircrobots import Server as BaseServer
from ircrobots import ConnectionParams

class Server(BaseServer):
    def __init__(self, bot, name, delay):
        super().__init__(bot, name)
        self.delay = delay
        self.queue = []

    async def line_read(self, line):
        print(f"{self.name} < {line.format()}")
        fun = "on_" + line.command.lower()
        if fun in dir(self):
            asyncio.create_task(getattr(self, fun)(line))

    async def line_send(self, line):
        print(f"{self.name} > {line.format()}")

class Bot(BaseBot):
    def __init__(self, url, delay):
        super().__init__()
        self.default_delay = delay
        self.url = url

    def create_server(self, name):
        return Server(self, name, self.default_delay)

async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("url")
    parser.add_argument("-d", help="delay in minutes between collecting metrics", type=int, default=10)
    parser.add_argument("-n", help="nickname to use", default="solamon")
    parser.add_argument("-s", help="irc server(s) to connect to", action='append')
    args = parser.parse_args()

    bot = Bot(args.url, args.d)

    for server in args.s:
        params = ConnectionParams(args.n, server, 6697)
        await bot.add_server(server, params)

    await bot.run()


if __name__ == "__main__":
    asyncio.run(main())
