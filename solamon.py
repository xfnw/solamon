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
    def __init__(self, url):
        super().__init__()
        self.url = url

    def create_server(self, name, delay):
        return Server(self, name, delay)

def main():
    parser = argparse.ArgumentParser()

    args = parser.parse_args()

if __name__ == "__main__":
    main()
