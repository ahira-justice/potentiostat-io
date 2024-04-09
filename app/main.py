import json

import asyncio
from logging.config import fileConfig as configure_logging

from loguru import logger

import notifications
from client import start_experiment, post_measurement
from config import ABLY_API_KEY, CLIENT_ID
from constants import LOGGING_CONFIG_DIR
from potentiostat import get_measurements, prime_potentiostat


async def main():
    configure_logging(LOGGING_CONFIG_DIR, disable_existing_loggers=False)

    channel = await notifications.setup_channel(ABLY_API_KEY, CLIENT_ID)
    await channel.subscribe(event_handler)

    stop = False
    while not stop:
        await asyncio.sleep(1)


def event_handler(message):
    try:
        event = json.loads(message.data)

        experiment_id = event.get("id")

        prime_potentiostat(event)
        started = start_experiment(experiment_id)
        logger.info(f"Starting experiment {experiment_id}...")

        if not started:
            return

        for current, voltage in get_measurements():
            logger.info(f"Posting measurement for experiment {experiment_id}: current: {current}mA, voltage: {voltage}V")
            posted = post_measurement(experiment_id, current, voltage)

            if not posted:
                logger.info(f"Stopping experiment {experiment_id}")
                break
    except Exception as ex:
        logger.info(f"Uncaught event handler exception: {ex}")
        raise ex


if __name__ == '__main__':
    asyncio.run(main())
