from asyncio import create_task, sleep
from os import environ
from random import randrange
from typing import Optional

from discord import Client, Status, Game, TextChannel, Message


def verbose(*args) -> None:
    """Print the specified args only if $VERBOSE is set."""

    if "VERBOSE" in environ.keys():
        print("verbose:", *args)


class OobClient(Client):
    # These delay values do not apply to replies to mentions.
    DELAY_MIN = 1  # 1 second
    DELAY_MAX = 72 * 60 * 60  # 72 hours
    DELAY_POW = 0.9  # delay = delay ^ 0.9

    def __init__(self, channel_id: int, **options) -> None:
        super().__init__(**options)
        self.channel_id = channel_id
        self.delay_secs = self.DELAY_MAX
        self.delay_task = None

    async def oob(self, message: Optional[Message]) -> None:
        """Send an oob, optionally as a reply to a message."""

        # If message is provided, send to the same channel as that message.
        # Otherwise, send to the channel specified with $DISCORD_CHANNEL.
        channel: TextChannel = (
            message.channel if message else self.get_channel(self.channel_id)
        )

        verbose(
            f"sending an oob to #{channel.name}"
            + (f" as a reply to {message.author}" if message else "")
        )

        # Send the message, spending a random amount of time "typing" to make
        # things a little more fun :).
        with channel.typing():
            await sleep(randrange(1, 5))
            if message:
                await message.reply("oob")
            else:
                await channel.send("oob")

    def start_delayed_oob(self) -> None:
        """Set an oob to be sent in the future.

        This will replace the existing delay task if there is one. The delay
        will be in the range of [0.5 * self.delay_secs, self.delay_secs)."""

        # If there is already an oob waiting, cancel it.
        if self.delay_task:
            verbose(f"cancelling existing delay task '{self.delay_task.get_name()}'")
            self.delay_task.cancel()

        # Randomize the delay based on self.delay_secs.
        delay = max(
            self.DELAY_MIN, int(randrange(self.delay_secs // 2, self.delay_secs))
        )

        # Create a task that waits delay seconds before calling oob().
        async def oob_delay_fn():
            await sleep(delay)

            # While unlikely, it is possible that oob_delay could be called
            # while the current task is in the middle of running oob() (since
            # it has a small delay to simulate typing). Running oob() in a new
            # task should prevent this.
            create_task(self.oob(None))

            # Reset the delay to the maximum and start a new delay task.
            # Restarting the task ensures that the bot will eventually send an
            # oob again even if no one else sends one.
            self.delay_secs = self.DELAY_MAX
            self.start_delayed_oob()

        self.delay_task = create_task(oob_delay_fn(), name=f"oob_delay_fn.{delay}")
        verbose(f"started new delay task '{self.delay_task.get_name()}'")

        m, s = divmod(delay, 60)
        h, m = divmod(m, 60)
        d, h = divmod(h, 24)
        verbose(f"next oob will be in {delay}s", f"({d}d {h}h {m}m {s}s)")

    async def on_ready(self) -> None:
        """Called when the bot is ready to start."""

        print(f"logged in as {self.user}!")
        await self.change_presence(status=Status.idle, activity=Game("oob"))
        self.start_delayed_oob()

    async def on_message(self, message: Message) -> None:
        """Called when a message is sent."""

        # Never respond to our own messages.
        if message.author == self.user:
            return

        # If the message mentions us directly, respond immediately.
        if self.user.mentioned_in(message):
            await self.oob(message)
            return

        # Otherwise, handle the message if it is in $DISCORD_CHANNEL.
        elif message.channel.id == self.channel_id:
            # Reduce the delay by DELAY_POW and start a new delayed oob task.
            self.delay_secs = int(self.delay_secs ** self.DELAY_POW)
            self.start_delayed_oob()


if __name__ == "__main__":
    token = environ["DISCORD_TOKEN"]
    channel = int(environ["DISCORD_CHANNEL"])
    print(f"loaded configuration from environment:")
    print(f"    DISCORD_TOKEN=***")
    print(f"  DISCORD_CHANNEL={channel}")
    print("connecting to Discord...")
    OobClient(channel).run(token)
