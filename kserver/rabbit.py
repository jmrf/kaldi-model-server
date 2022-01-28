import logging
import time

from typing import Callable
from typing import List
from typing import Tuple

import pika

from pika.adapters.blocking_connection import BlockingChannel


logger = logging.getLogger(__name__)


def get_q_count(channel, q_name):
    return channel.queue_declare(queue=q_name, passive=True).method.message_count


def wait_on_q_limit(channel: BlockingChannel, q_name: str, lim: int, sleep: int = 10):
    msg_in_q = get_q_count(channel, q_name)
    logger.info(f"🐇 Found {msg_in_q} messages in the queue ({q_name})...")
    while msg_in_q > lim:
        logger.debug(f"🐇 Waiting... ({msg_in_q} remaining)")
        time.sleep(sleep)
        msg_in_q = get_q_count(channel, q_name)


class BaseQueueClient:

    VALID_EXCHANGE_TYPES = ["fanout", "topic", "headers"]

    def __init__(
        self,
        amqp_uri: str,
        blocked_timeout: int = 10,
        q_lim: int = None,
        *args,
        **kwargs,
    ):
        # super().__init__(*args, **kwargs)
        self.queue_name = None
        self.exchange_name = None
        self.exchange_type = None
        self._amqp_uri = amqp_uri
        self._timeout = blocked_timeout
        self.q_lim = q_lim or -1

    def _validate_params(self):

        if self.queue_name and self.exchange_name:
            logger.warning("🐇 Connecting to an exchange and a queue simultanously")  # type: ignore

        if self.exchange_name and self.exchange_type not in self.VALID_EXCHANGE_TYPES:
            raise ValueError(
                f"Invalid exchange type: '{self.exchange_type}'. "
                f"Must be one of: {self.VALID_EXCHANGE_TYPES}"
            )
        if self.q_lim > 0 and self.exchange_name:
            logger.warning(f"🐇 Queue limit will be ignored when sending to an exchange")

        logger.info(f"🐇 @ {self._amqp_uri} | {self.queue_name or self.exchange_name}")

    def declare_queue(
        self,
        channel: BlockingChannel,
        queue_name: str,
        passive: bool = False,
        durable: bool = False,
        exclusive: bool = False,
        auto_delete: bool = False,
    ) -> None:

        # Create the channel **persistent** queue
        logger.info(f"🐇 Connecting to queue: {self.queue_name}")
        channel.queue_declare(
            queue=queue_name,
            passive=passive,  # message persistance
            durable=durable,  # message persistance
            exclusive=exclusive,  # so we can reconnect after a consumer restart
            auto_delete=auto_delete,  # queue survives consumer restart
        )

    def declare_exchange(
        self,
        channel: BlockingChannel,
        exchange_name: str,
        exchange_type: str,
        durable: bool = False,
    ) -> None:
        logger.info(
            f"🐇 Connecting to a '{self.exchange_type}' exchange: {self.exchange_name}"
        )
        channel.exchange_declare(
            exchange=exchange_name,
            exchange_type=exchange_type,
            durable=durable,
        )

    def connect(self) -> Tuple[pika.BlockingConnection, BlockingChannel]:
        connection = pika.BlockingConnection(
            # for connection no to die while blocked waiting for inputs
            # we must set the heartbeat to 0 (although is discouraged)
            pika.ConnectionParameters(
                self._amqp_uri, blocked_connection_timeout=self._timeout, heartbeat=0
            )
        )
        channel = connection.channel()

        return connection, channel


class BlockingQueuePublisher(BaseQueueClient):
    def __init__(
        self,
        amqp_uri: str,
        queue_name: str = None,
        exchange_name: str = None,
        exchange_type: str = None,
        *args,
        **kwargs,
    ):
        super().__init__(amqp_uri, *args, **kwargs)
        self.queue_name = queue_name
        self.exchange_name = exchange_name or ""
        self.exchange_type = exchange_type

    def send_message(self, message, topic: str = None):
        connection, channel = self.connect()
        if self.exchange_name and self.exchange_type:
            self.declare_exchange(
                channel, self.exchange_name, self.exchange_type, durable=True
            )

        if self.queue_name:
            # If a queue_name is given but doesn't exist, will fail
            self.declare_queue(channel, self.queue_name, passive=True)

            if self.q_lim > 0:
                wait_on_q_limit(channel, self.queue_name, lim=self.q_lim)

        logger.debug(
            f"Publishing to: {self.exchange_name} | {self.queue_name} ({topic})"
        )
        channel.basic_publish(
            exchange=self.exchange_name,
            routing_key=topic,
            body=message,
            properties=pika.BasicProperties(
                delivery_mode=2,
            ),  # make message persistent
        )

        connection.close()
        logger.info("🐇🍻 Sent!")


class BlockingQueueConsumer(BaseQueueClient):

    PREFETCH_COUNT = 10

    def __init__(
        self,
        amqp_uri: str,
        on_event: Callable,
        on_done: Callable,
        load_func: Callable,
        queue_name: str = None,
        exchange_name: str = None,
        exchange_type: str = None,
        routing_keys: List = None,
        prefetch_count: int = None,
        *args,
        **kwargs,
    ):
        super().__init__(
            amqp_uri,
            *args,
            **kwargs,
        )

        self._on_event = on_event
        self._on_done = on_done
        self._load_func = load_func
        self.routing_keys = routing_keys
        self.queue_name = queue_name
        self.exchange_name = exchange_name or ""
        self.exchange_type = exchange_type

        self._prefetch_count = prefetch_count or self.PREFETCH_COUNT

        self._validate_params()
        self._connection, self._channel = self.connect()

        self._bind()

    def _bind(self):
        # Connecting directly to a Queue
        result = self._channel.queue_declare(
            queue=self.queue_name or "", durable=True, passive=False
        )
        self.queue_name = result.method.queue
        self._channel.basic_qos(prefetch_count=self._prefetch_count)

        if self.exchange_name and self.exchange_type:
            # Connect to an exchange and bind to the given topics
            self.declare_exchange(
                self._channel, self.exchange_name, self.exchange_type, durable=True
            )
            for k in self.routing_keys:
                logger.info(f"🐇 Binding queue '{self.queue_name}' to key: '{k}'")
                self._channel.queue_bind(
                    exchange=self.exchange_name, queue=self.queue_name, routing_key=k
                )

    def _callback(self, ch, method, properties, body):
        """Assumes a 'body' is an encoded list of data. For each element
        the 'on_event' function is called to process the messages
        """
        try:
            rx_data = self._load_func(body)
            for event in rx_data:
                self._on_event(event)
        except Exception as e:
            logger.error(f"🐇 Error in queue callback: {e}")
        else:
            # Notify Inference Server via endpoint
            self._on_done()
        finally:
            # Send basic acknowledge back (no matter what)
            ch.basic_ack(delivery_tag=method.delivery_tag)
            logger.info("🐇 Done!")

    def consume(self):
        self._channel.basic_consume(
            queue=self.queue_name, on_message_callback=self._callback
        )

        logger.info(
            f"🐇 Waiting for messages on {self.queue_name}. To exit press CTRL+C"
        )
        self._channel.start_consuming()

    def unbind(self):
        for k in self.routing_keys:
            logger.info(f"🐇 Unbinding queue '{self.queue_name}' and key: '{k}'")
            self._channel.queue_unbind(
                exchange=self.exchange_name, queue=self.queue_name, routing_key=k
            )

    def close(self):
        logger.info("🐇 Closing connection!")
        self._connection.close()
