import random
from asyncio import sleep
from os import environ

from discord import Client, Status, Game, TextChannel, Message


class OobClient(Client):
    def __init__(self, channel_id: int, **options) -> None:
        super().__init__(**options)
        self.channel_id = channel_id

    async def oob(self) -> None:
        channel: TextChannel = self.get_channel(self.channel_id)
        with channel.typing():
            await sleep(random.randrange(5))
            await channel.send("oob")

    async def on_ready(self) -> None:
        print(f"Logged in as {self.user}!")
        await self.change_presence(status=Status.idle, activity=Game("oob"))
        await self.oob()

    async def on_message(self, message: Message) -> None:
        # Don't respond too our own oobs (infinite oob loop!)
        if message.author == self.user:
            return
        # Don't respond if the message is outside the oob channel
        if message.channel.id != self.channel_id:
            return
        # Don't respond if the message is not oob (heresy!)
        if message.content != "oob":
            return
        # Otherwise, oob!
        await sleep(random.randrange(5))
        await self.oob()


if __name__ == "__main__":
    token = environ["DISCORD_TOKEN"]
    channel = int(environ["DISCORD_CHANNEL"])
    OobClient(channel).run(token)
