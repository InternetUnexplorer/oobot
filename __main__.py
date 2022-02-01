import random
from asyncio import sleep
from os import environ
from typing import Optional

from discord import Client, Status, Game, TextChannel, Message


class OobClient(Client):
    def __init__(self, channel_id: int, **options) -> None:
        super().__init__(**options)
        self.channel_id = channel_id

    async def oob(self, message: Optional[Message]) -> None:
        channel: TextChannel = message.channel if message else self.get_channel(self.channel_id)
        with channel.typing():
            await sleep(random.randrange(5))
            if message:
                await message.reply("oob")
            else:
                await channel.send("oob")

    async def on_ready(self) -> None:
        print(f"Logged in as {self.user}!")
        await self.change_presence(status=Status.idle, activity=Game("oob"))

    async def on_message(self, message: Message) -> None:
        # Don't respond too our own oobs (infinite oob loop!)
        if message.author == self.user:
            return
        # Respond if the message is in the oob channel or if we were mentioned
        is_mention = self.user.mentioned_in(message)
        is_in_oob_channel = message.channel.id == self.channel_id
        if is_mention or (is_in_oob_channel and random.randrange(10) > 4):
            await sleep(random.randrange(5))
            await self.oob(None if not is_mention else message)


if __name__ == "__main__":
    token = environ["DISCORD_TOKEN"]
    channel = int(environ["DISCORD_CHANNEL"])
    OobClient(channel).run(token)
