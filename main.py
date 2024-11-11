import asyncio
import json
import logging
import tomllib
from asyncio import CancelledError
from typing import Any

from aiokafka import AIOKafkaProducer
from tenacity import retry, retry_if_exception_type, wait_random_exponential
from websockets import ConnectionClosed, Data
from websockets.asyncio.client import ClientConnection, connect


logging.basicConfig(
    format='%(asctime)s %(levelname)-8s %(message)s',
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S')


@retry(
    retry=retry_if_exception_type((ConnectionClosed, TimeoutError)),
    wait=wait_random_exponential(multiplier=1, max=60)
)
async def stream(
    ws_url: str, bootstrap_servers: list[str], topic: str
) -> None:
    kafka_producer: AIOKafkaProducer[str, dict[str, str]] = AIOKafkaProducer(
        bootstrap_servers=bootstrap_servers,
        key_serializer=str.encode,
        value_serializer=lambda d: json.dumps(d).encode(),
    )

    async with kafka_producer:
        ws_conn: ClientConnection
        async with connect(ws_url) as ws_conn:
            logging.info('WebSocket connection established')
            data: Data
            async for data in ws_conn:
                logging.info(f'Processing {data}')
                msg: dict[str, str] = json.loads(data)
                await kafka_producer.send(topic, msg, msg['s'])


async def main():
    with open('config.toml', 'rb') as f:
        config: dict[str, Any] = tomllib.load(f)

    try:
        await stream(
            config['source']['websockets']['url'],
            config['destination']['kafka']['bootstrap_servers'],
            config['destination']['kafka']['topic_name'],
        )
    except CancelledError:
        logging.info("Shutting down")
        exit(0)


if __name__ == "__main__":
    asyncio.run(main())
