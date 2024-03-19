from ably import AblyRealtime, logger
from ably.realtime.realtime_channel import RealtimeChannel


async def setup_channel(api_key: str, channel_name: str) -> RealtimeChannel:
    ably_realtime = AblyRealtime(api_key)
    await ably_realtime.connection.once_async("connected")
    logger.info("Connected to ably")

    return ably_realtime.channels.get(channel_name)
