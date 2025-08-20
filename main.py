import asyncio
import json
import logging
from collections import namedtuple

import httpx
from decouple import Csv, config

BOT_TOKEN = config("BOT_TOKEN")
CHAT_IDS: list[int] = config("CHAT_ID", cast=Csv(int))  # type: ignore
NOTIFY_TRAFFIC_PERCENTS = sorted(
    config("NOTIFY_TRAFFIC_PERCENTS", cast=Csv(int)),  # type: ignore
    reverse=True,
)
NOTIFY_CPU_USAGE_PERCENT = config("NOTIFY_CPU_USAGE_PERCENT", cast=int)
NOTIFY_RAM_USAGE_PERCENT = config("NOTIFY_RAM_USAGE_PERCENT", cast=int)
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
        "cpu_usage_percent",
        "ram_usage_percent",
    ],
)


class ServerStatsFetchException(Exception):
    """Custom exception for server stats fetch errors."""

    def __init__(self, message):
        super().__init__(message)
        self.message = message


async def tg_bot_send_message(chat_ids: list[int], message: str):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    async def _send(chat_id):
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

    await asyncio.gather(*[_send(chat_id) for chat_id in chat_ids])


async def fetch_server_data(server) -> ServerStats:
    retry = 3
    delay = 0.5
    exception = None
    for _ in range(retry):
        try:
            response = await client.get(server["url"])
            response.raise_for_status()
            break
        except (httpx.RequestError, httpx.HTTPStatusError) as e:
            e_message = response.text if isinstance(e, httpx.HTTPStatusError) else e
            exception = e
            await asyncio.sleep(delay)

    if exception is not None:
        raise ServerStatsFetchException(
            f"Failed to fetch data for server {server['name']}: {e_message}"
        )

    data = response.json()
    return ServerStats(
        server["name"],
        data["info"]["bandwidth"]["free_gb"],
        data["info"]["bandwidth"]["percent_free"],
        data["info"]["cpu"]["percent"],
        data["info"]["ram"]["percent"],
    )


def is_traffic_threshold_reached(server_stats: ServerStats):
    next_threshold = NEXT_TRAFFIC_PERCENT_THRESHOLD.get(
        server_stats.name,
        float("-inf"),
    )
    return server_stats.remaining_traffic_percent <= next_threshold


def is_cpu_usage_threshold_reached(server_stats: ServerStats):
    return server_stats.cpu_usage_percent >= NOTIFY_CPU_USAGE_PERCENT


def is_ram_usage_threshold_reached(server_stats: ServerStats):
    return server_stats.cpu_usage_percent >= NOTIFY_RAM_USAGE_PERCENT


def is_threshold_reached(server_stats: ServerStats):
    funcs = [
        is_traffic_threshold_reached,
        is_cpu_usage_threshold_reached,
        is_ram_usage_threshold_reached,
    ]
    return any(func(server_stats) for func in funcs)


def set_next_traffic_threshold(server_stats: ServerStats):
    for percent in NOTIFY_TRAFFIC_PERCENTS:
        if percent < server_stats.remaining_traffic_percent:
            NEXT_TRAFFIC_PERCENT_THRESHOLD[server_stats.name] = percent
            break


async def check_and_notify():
    with open("servers.json", "r") as file:
        servers = json.load(file)

    tasks = [fetch_server_data(server) for server in servers]
    for completed in asyncio.as_completed(tasks):
        try:
            server_stats = await completed
        except ServerStatsFetchException as e:
            await tg_bot_send_message(CHAT_IDS, e.message)
            continue

        if is_threshold_reached(server_stats):
            message = (
                "⚠️ Alert\n"
                f"Server: <b>{server_stats.name}</b>\n"
                f"CPU Usage: <code>{server_stats.cpu_usage_percent}</code>\n"
                f"RAM Usage: <code>{server_stats.ram_usage_percent}</code>\n"
                f"Remaining Traffic: <code>{server_stats.remaingin_traffic}GB ({server_stats.remaining_traffic_percent}%)</code>"
            )
            await tg_bot_send_message(CHAT_IDS, message)
            set_next_traffic_threshold(server_stats)


async def main():
    logger.info("Starting server traffic monitor...")
    while True:
        await check_and_notify()
        await asyncio.sleep(INTERVAL_MINUTES * 60)


if __name__ == "__main__":
    asyncio.run(main())
