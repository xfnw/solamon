#!/usr/bin/env python3

import argparse, asyncio, aiohttp

from irctokens import build
from ircrobots import Bot as BaseBot
from ircrobots import Server as BaseServer
from ircrobots import ConnectionParams

class Server(BaseServer):
    def __init__(self, bot, name, delay):
        super().__init__(bot, name)
        self.delay = delay
        self.servers = []
        self.queue = []

    async def line_read(self, line):
        print(f"{self.name} < {line.format()}")
        fun = "on_" + line.command.lower()
        if fun in dir(self):
            asyncio.create_task(getattr(self, fun)(line))

    async def line_send(self, line):
        print(f"{self.name} > {line.format()}")

    async def on_001(self, line):
        await self.send(build("LINKS", []))

    async def on_364(self, line):
        [_, server, *_] = line.params

        if server.startswith("services."):
            return

        self.servers.append(server)

    async def on_365(self, line):
        asyncio.create_task(self.collection_loop())

    async def collection_loop(self):
        while True:
            asyncio.create_task(self.collect_once())
            await asyncio.sleep(self.delay)

    async def collect_once(self):
        for server in self.servers:
            await self.send(build("LUSERS", ["*", server]))
            await self.send(build("STATS", ["m", server]))
            await asyncio.sleep(30)

    async def on_252(self, line):
        [_, num, *_] = line.params
        self.queue.append((line.source, 252, 'opers', num))

    async def on_253(self, line):
        [_, num, *_] = line.params
        self.queue.append((line.source, 253, 'unknown', num))

    async def on_254(self, line):
        [_, num, *_] = line.params
        self.queue.append((line.source, 254, 'channels', num))

    async def on_265(self, line):
        [_, num, *_] = line.params
        self.queue.append((line.source, 265, 'lusers', num))

    async def on_266(self, line):
        [_, num, *_] = line.params
        self.queue.append((line.source, 266, 'gusers', num))

    async def on_212(self, line):
        [_, cmd, num, *_] = line.params
        self.queue.append((line.source, 212, cmd, num))

    async def on_219(self, line):
        if not self.queue:
            return
        payload = "\n".join(map(lambda q: f"solamon,network={self.isupport.network},server={q[0]},numeric={q[1]},name={q[2]} val={q[3]}", self.queue))
        self.queue.clear()

        async with self.bot.session.post(self.bot.url, data=payload.encode("UTF-8")) as resp:
            print(f"uploaded {len(payload)} bytes, got status {resp.status}")


class Bot(BaseBot):
    def __init__(self, url, delay):
        super().__init__()
        self.default_delay = delay
        self.session = aiohttp.ClientSession()
        self.url = url

    def create_server(self, name):
        return Server(self, name, self.default_delay)

async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("url", help="specify influxdb-compatible write endpoint")
    parser.add_argument("-d", help="delay in minutes between collecting metrics", type=int, default=10)
    parser.add_argument("-n", help="nickname to use", default="solamon")
    parser.add_argument("-s", help="irc server(s) to connect to", action='append')
    args = parser.parse_args()

    bot = Bot(args.url, args.d*60)

    for server in args.s:
        params = ConnectionParams(args.n, server, 6697)
        await bot.add_server(server, params)

    await bot.run()


if __name__ == "__main__":
    asyncio.run(main())
