from asyncio import create_task, sleep
from os import environ
from random import randrange
from typing import List, Optional

from discord import Client, DMChannel, Game, Intents, Message, Status, TextChannel


def verbose(*args) -> None:
    """Print the specified args only if $VERBOSE is set."""

    if "VERBOSE" in environ.keys():
        print("verbose:", *args)


class OobClient(Client):
    # These delay values control the delay for scheduled oobs.
    DELAY_MIN = 1  # 1 second
    DELAY_MAX = 72 * 60 * 60  # 72 hours
    DELAY_POW = 0.9  # delay = delay ^ 0.9

    def __init__(self, channel_ids: List[int], **options) -> None:
        super().__init__(intents=Intents(guilds=True, messages=True), **options)
        self.scheduled_oobs = {
            channel_id: {"delay_secs": self.DELAY_MAX, "delay_task": None}
            for channel_id in channel_ids
        }

    async def oob(self, channel: TextChannel, message: Optional[Message]) -> None:
        """Send an oob, optionally as a reply to a message."""

        # Get a human-friendly description of the channel.
        channel_desc = (
            "a DM"
            if isinstance(channel, DMChannel)
            else f"#{channel.name} in {channel.guild.name}"
        )

        if message:
            verbose(f"replying to {message.author} in {channel_desc}")
        else:
            verbose(f"sending a scheduled oob to {channel_desc}")

        # 0.5% chance to send :alembic: instead (increases whimsy).
        reply = "oob" if randrange(200) != 0 else "\u2697"

        # Send the message, spending a random amount of time "typing" to make
        # things a little more fun :).
        async with channel.typing():
            await sleep(randrange(1, 5))
            if message:
                await message.reply(reply)
            else:
                await channel.send(reply)

    def schedule_oob(self, channel_id: int) -> None:
        """Schedule an oob to be sent in the future.

        This will replace any existing scheduled oob for this channel. The delay
        will be in the range of [0.5 * self.delay_secs, self.delay_secs)."""

        channel = self.get_channel(channel_id)
        channel_desc = f"#{channel.name} in {channel.guild.name}"

        delay_task = self.scheduled_oobs[channel_id]["delay_task"]
        delay_secs = self.scheduled_oobs[channel_id]["delay_secs"]

        # If there is already an oob scheduled, cancel it.
        if delay_task:
            verbose(f"cancelling existing delay task '{delay_task.get_name()}'")
            delay_task.cancel()

        # Randomize the delay based on self.delay_secs.
        delay_secs = max(self.DELAY_MIN, int(randrange(delay_secs // 2, delay_secs)))

        # Create a task that waits delay seconds before calling oob().
        async def task():
            await sleep(delay_secs)

            # While unlikely, it is possible that schedule_oob() could be called
            # while the current task is in the middle of running oob() (since
            # it has a small delay to simulate typing). Running oob() in a new
            # task should prevent this.
            create_task(self.oob(channel, None))

            # Reset the delay to the maximum and start a new delay task.
            # Restarting the task ensures that the bot will eventually send an
            # oob again even if no one else sends one.
            self.scheduled_oobs[channel_id]["delay_secs"] = self.DELAY_MAX
            self.schedule_oob(channel_id)

        delay_task = create_task(task(), name=f"oob_delay_fn.{channel_id}.{delay_secs}")
        self.scheduled_oobs[channel_id]["delay_task"] = delay_task
        verbose(f"started new delay task '{delay_task.get_name()}'")

        m, s = divmod(delay_secs, 60)
        h, m = divmod(m, 60)
        d, h = divmod(h, 24)
        verbose(
            f"next oob in {channel_desc} will be in {delay_secs}s",
            f"({d}d {h}h {m}m {s}s)",
        )

    async def on_ready(self) -> None:
        """Called when the bot is ready to start."""

        print(f"logged in as {self.user}!")
        await self.change_presence(status=Status.idle, activity=Game("oob"))
        for channel_id in self.scheduled_oobs.keys():
            self.schedule_oob(channel_id)

    async def on_message(self, message: Message) -> None:
        """Called when a message is sent."""

        # Never respond to our own messages.
        if message.author == self.user:
            return

        # Respond immediately if the message is a DM or mentions us.
        if isinstance(message.channel, DMChannel) or self.user.mentioned_in(message):
            await self.oob(message.channel, message)
            return

        # Otherwise, handle the message if it is in $DISCORD_CHANNEL.
        if message.channel.id in self.scheduled_oobs.keys():
            # Reduce the delay by DELAY_POW and start a new delayed oob task.
            self.scheduled_oobs[message.channel.id]["delay_secs"] = int(
                self.scheduled_oobs[message.channel.id]["delay_secs"] ** self.DELAY_POW
            )
            self.schedule_oob(message.channel.id)


if __name__ == "__main__":
    token = environ["DISCORD_TOKEN"]
    channels = [
        int(channel_str.strip())
        for channel_str in environ["DISCORD_CHANNELS"].split(",")
    ]
    print(f"loaded configuration from environment:")
    print(f"     DISCORD_TOKEN=***")
    print(f"  DISCORD_CHANNELS={','.join(map(str, channels))}")
    print("connecting to Discord...")
    OobClient(channels).run(token)
