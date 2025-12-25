#!/usr/bin/env python3

import argparse, asyncio, aiohttp

from irctokens import build
from ircrobots import Bot as BaseBot
from ircrobots import Server as BaseServer
from ircrobots import ConnectionParams
from ircrobots.security import TLSVerifyChain, TLSNoVerify


class Server(BaseServer):
    def __init__(self, bot, name, delay):
        super().__init__(bot, name)
        self.delay = delay
        self.lusers = {}
        self.stats = {}

    async def line_read(self, line):
        print(f"{self.name} < {line.format()}")
        fun = "on_" + line.command.lower()
        if fun in dir(self):
            asyncio.create_task(getattr(self, fun)(line))

    async def line_send(self, line):
        print(f"{self.name} > {line.format()}")

    async def on_001(self, line):
        asyncio.create_task(self.collection_loop())

    async def collection_loop(self):
        while True:
            asyncio.create_task(self.collect_once())
            await asyncio.sleep(self.delay)

    async def collect_once(self):
        await self.send(build("LUSERS", []))
        await self.send(build("STATS", ["m"]))

    async def on_252(self, line):
        [_, num, *_] = line.params
        self.lusers["opers"] = num

    async def on_253(self, line):
        [_, num, *_] = line.params
        self.lusers["unknown"] = num

    async def on_254(self, line):
        [_, num, *_] = line.params
        self.lusers["channels"] = num

    async def on_265(self, line):
        [_, num, max, *_] = line.params
        self.lusers["local"] = num
        self.lusers["local_max"] = max

    async def on_266(self, line):
        [_, num, max, *_] = line.params
        self.lusers["global"] = num
        self.lusers["global_max"] = max

    async def on_212(self, line):
        [_, cmd, num, *_] = line.params
        self.stats[cmd.lower()] = num

    async def on_219(self, line):
        payload = (
            f"lusers,network={self.isupport.network},server={self.server} "
            + ",".join(f"{k}={v}" for k, v in self.lusers.items())
            + f"\nstatsm,network={self.isupport.network},server={self.server} "
            + ",".join(f"{k}={v}" for k, v in self.stats.items())
        )
        self.lusers.clear()
        self.stats.clear()

        async with self.bot.session.post(
            self.bot.url, data=payload.encode("UTF-8")
        ) as resp:
            print(f"uploaded {len(payload)} bytes, got status {resp.status}")


class Bot(BaseBot):
    def __init__(self, url, delay, headers):
        super().__init__()
        self.default_delay = delay
        self.session = aiohttp.ClientSession(headers=headers)
        self.url = url

    def create_server(self, name):
        return Server(self, name, self.default_delay)


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("url", help="specify influxdb-compatible write endpoint")
    parser.add_argument(
        "-H", help="additional request header(s)", nargs=2, action="append"
    )
    parser.add_argument(
        "-d", help="delay in seconds between collecting metrics", type=int, default=10
    )
    parser.add_argument("-n", help="nickname to use", default="solamon")
    parser.add_argument("-s", help="irc server(s) to connect to", action="append")
    parser.add_argument("-k", help="disable tls verification", action="store_true")
    args = parser.parse_args()

    bot = Bot(args.url, args.d, {h[0]: h[1] for h in args.H or []})

    for server in args.s:
        params = ConnectionParams(
            args.n, server, 6697, tls=TLSNoVerify() if args.k else TLSVerifyChain()
        )
        await bot.add_server(server, params)

    await bot.run()


if __name__ == "__main__":
    asyncio.run(main())
