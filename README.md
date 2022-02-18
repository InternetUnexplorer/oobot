# oobot

A Discord bot that goes "oob", to keep us company in #oob.

## Description

oobot does two things:
- oobot will reply "oob" when mentioned, regardless of channel.
- oobot will periodically say "oob" in the specified channel.

For the latter, oobot works as follows:
- oobot will wait a random amount of time in the range of
  `[0.5*DELAY_MAX,DELAY_MAX)` seconds before sending an oob.
- If a message arrives in the specified channel before the above time has
  elapsed, oobot will pick a new delay in the range of `[0.5*DELAY,DELAY)`,
  where `DELAY` is the previous delay time to the `DELAY_POW` power.
  - This will happen every time someone sends a message in the specified
    channel, so the more active the channel is the more active oobot will be.
- Every time the delay elapses it is reset to a random amount of time in the
  range of `[0.5*DELAY_MAX,DELAY_MAX)` like at the start.

Replying to mentions happens immediately and is separate from the above delays.

## Usage

oobot requires [discord.py](https://discordpy.readthedocs.io/en/stable/).

oobot accepts the following environment variables:
- `DISCORD_TOKEN`: the bot token (required)
- `DISCORD_CHANNEL`: the channel ID to periodically send oobs to (required)
- `VERBOSE`: enables additional logging if set

## License

Licensed under [the Unlicense](https://unlicense.org/).
