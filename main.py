import asyncio
import json
import logging
from collections import namedtuple

import httpx
from decouple import Csv, config

BOT_TOKEN = config("BOT_TOKEN")
CHAT_ID = config("CHAT_ID")
NOTIFY_TRAFFIC_PERCENTS = sorted(
    config("NOTIFY_TRAFFIC_PERCENTS", cast=Csv(int)),  # type: ignore
    reverse=True,
)
PROXY = config("PROXY", default=None)
INTERVAL_MINUTES = config("INTERVAL_MINUTES", cast=int)
NEXT_TRAFFIC_PERCENT_THRESHOLD = {}

# client used for server requests
client = httpx.AsyncClient(
    timeout=httpx.Timeout(20.0, connect=20.0),
    verify=False,
    proxy=PROXY,  # type: ignore
)
# client used for telegram bot requests
tg_client = httpx.AsyncClient()
logger = logging.getLogger(__name__)
ServerStats = namedtuple(
    "ServerStats",
    [
        "name",
        "remaingin_traffic",
        "remaining_traffic_percent",
    ],
)


class ServerStatsFetchException(Exception):
    """Custom exception for server stats fetch errors."""

    def __init__(self, message):
        super().__init__(message)
        self.message = message


async def tg_bot_send_message(chat_id, message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "html",
    }
    try:
        response = await tg_client.post(url, json=payload)
        response.raise_for_status()
        return response.json()
    except httpx.RequestError as e:
        logger.error(f"Telegram bot request failed: {e}")


async def fetch_server_data(server) -> ServerStats:
    try:
        response = await client.get(server["url"])
        response.raise_for_status()
    except httpx.RequestError as e:
        raise ServerStatsFetchException(
            f"Failed to fetch data for server {server['name']}: {e}"
        )
    except httpx.HTTPStatusError:
        raise ServerStatsFetchException(
            f"Failed to fetch data for server {server['name']}: {response.text}"
        )

    data = response.json()
    return ServerStats(
        server["name"],
        data["info"]["bandwidth"]["free_gb"],
        data["info"]["bandwidth"]["percent_free"],
    )


def is_threshold_reached(server_stats):
    reached = False
    if server_stats.remaining_traffic_percent <= NEXT_TRAFFIC_PERCENT_THRESHOLD.get(
        server_stats.name,
        float("-inf"),
    ):
        reached = True

    # set next threshold
    for percent in NOTIFY_TRAFFIC_PERCENTS:
        if percent < server_stats.remaining_traffic_percent:
            NEXT_TRAFFIC_PERCENT_THRESHOLD[server_stats.name] = percent
            break

    return reached


async def check_and_notify():
    with open("servers.json", "r") as file:
        servers = json.load(file)

    tasks = [fetch_server_data(server) for server in servers]
    for completed in asyncio.as_completed(tasks):
        try:
            server_stats = await completed
        except ServerStatsFetchException as e:
            await tg_bot_send_message(CHAT_ID, e.message)
            continue

        if is_threshold_reached(server_stats):
            message = (
                f"Server: <b>{server_stats.name}</b>\n"
                f"Remaining Traffic: <code>{server_stats.remaingin_traffic}GB ({server_stats.remaining_traffic_percent}%)</code>"
            )
            asyncio.create_task(tg_bot_send_message(CHAT_ID, message))


async def main():
    logger.info("Starting server traffic monitor...")
    while True:
        await check_and_notify()
        await asyncio.sleep(INTERVAL_MINUTES * 60)


if __name__ == "__main__":
    asyncio.run(main())
