import asyncio
from collections.abc import Iterable
from ssl import SSLContext
from types import ModuleType, TracebackType
from typing import Callable, Generic, Literal, TypeVar

from aiokafka.abc import AbstractTokenProvider
from aiokafka.structs import OffsetAndMetadata, RecordMetadata, TopicPartition

from .message_accumulator import BatchBuilder

log = ...
_missing = ...
_DEFAULT_PARTITIONER = ...

def _identity(data: bytes) -> bytes: ...

KT_contra = TypeVar("KT_contra", contravariant=True)
VT_contra = TypeVar("VT_contra", contravariant=True)
ET = TypeVar("ET", bound=BaseException)

class AIOKafkaProducer(Generic[KT_contra, VT_contra]):
    """A Kafka client that publishes records to the Kafka cluster.

    The producer consists of a pool of buffer space that holds records that
    haven't yet been transmitted to the server as well as a background task
    that is responsible for turning these records into requests and
    transmitting them to the cluster.

    The :meth:`send` method is asynchronous. When called it adds the record to a
    buffer of pending record sends and immediately returns. This allows the
    producer to batch together individual records for efficiency.

    The `acks` config controls the criteria under which requests are considered
    complete. The ``all`` setting will result in waiting for all replicas to
    respond, the slowest but most durable setting.

    The `key_serializer` and `value_serializer` instruct how to turn the key and
    value objects the user provides into :class:`bytes`.

    Arguments:
        bootstrap_servers (str, list(str)): a ``host[:port]`` string or list of
            ``host[:port]`` strings that the producer should contact to
            bootstrap initial cluster metadata. This does not have to be the
            full node list.  It just needs to have at least one broker that will
            respond to a Metadata API Request. Default port is 9092. If no
            servers are specified, will default to ``localhost:9092``.
        client_id (str or None): a name for this client. This string is passed in
            each request to servers and can be used to identify specific
            server-side log entries that correspond to this client.
            If ``None`` ``aiokafka-producer-#`` (appended with a unique number
            per instance) is used.
            Default: :data:`None`
        key_serializer (Callable): used to convert user-supplied keys to bytes
            If not :data:`None`, called as ``f(key),`` should return
            :class:`bytes`.
            Default: :data:`None`.
        value_serializer (Callable): used to convert user-supplied message
            values to :class:`bytes`. If not :data:`None`, called as
            ``f(value)``, should return :class:`bytes`.
            Default: :data:`None`.
        acks (Any): one of ``0``, ``1``, ``all``. The number of acknowledgments
            the producer requires the leader to have received before considering a
            request complete. This controls the durability of records that are
            sent. The following settings are common:

            * ``0``: Producer will not wait for any acknowledgment from the server
              at all. The message will immediately be added to the socket
              buffer and considered sent. No guarantee can be made that the
              server has received the record in this case, and the retries
              configuration will not take effect (as the client won't
              generally know of any failures). The offset given back for each
              record will always be set to -1.
            * ``1``: The broker leader will write the record to its local log but
              will respond without awaiting full acknowledgement from all
              followers. In this case should the leader fail immediately
              after acknowledging the record but before the followers have
              replicated it then the record will be lost.
            * ``all``: The broker leader will wait for the full set of in-sync
              replicas to acknowledge the record. This guarantees that the
              record will not be lost as long as at least one in-sync replica
              remains alive. This is the strongest available guarantee.

            If unset, defaults to ``acks=1``. If `enable_idempotence` is
            :data:`True` defaults to ``acks=all``
        compression_type (str): The compression type for all data generated by
            the producer. Valid values are ``gzip``, ``snappy``, ``lz4``, ``zstd``
            or :data:`None`.
            Compression is of full batches of data, so the efficacy of batching
            will also impact the compression ratio (more batching means better
            compression). Default: :data:`None`.
        max_batch_size (int): Maximum size of buffered data per partition.
            After this amount :meth:`send` coroutine will block until batch is
            drained.
            Default: 16384
        linger_ms (int): The producer groups together any records that arrive
            in between request transmissions into a single batched request.
            Normally this occurs only under load when records arrive faster
            than they can be sent out. However in some circumstances the client
            may want to reduce the number of requests even under moderate load.
            This setting accomplishes this by adding a small amount of
            artificial delay; that is, if first request is processed faster,
            than `linger_ms`, producer will wait ``linger_ms - process_time``.
            Default: 0 (i.e. no delay).
        partitioner (Callable): Callable used to determine which partition
            each message is assigned to. Called (after key serialization):
            ``partitioner(key_bytes, all_partitions, available_partitions)``.
            The default partitioner implementation hashes each non-None key
            using the same murmur2 algorithm as the Java client so that
            messages with the same key are assigned to the same partition.
            When a key is :data:`None`, the message is delivered to a random partition
            (filtered to partitions with available leaders only, if possible).
        max_request_size (int): The maximum size of a request. This is also
            effectively a cap on the maximum record size. Note that the server
            has its own cap on record size which may be different from this.
            This setting will limit the number of record batches the producer
            will send in a single request to avoid sending huge requests.
            Default: 1048576.
        metadata_max_age_ms (int): The period of time in milliseconds after
            which we force a refresh of metadata even if we haven't seen any
            partition leadership changes to proactively discover any new
            brokers or partitions. Default: 300000
        request_timeout_ms (int): Produce request timeout in milliseconds.
            As it's sent as part of
            :class:`~aiokafka.protocol.produce.ProduceRequest` (it's a blocking
            call), maximum waiting time can be up to ``2 *
            request_timeout_ms``.
            Default: 40000.
        retry_backoff_ms (int): Milliseconds to backoff when retrying on
            errors. Default: 100.
        api_version (str): specify which kafka API version to use.
            If set to ``auto``, will attempt to infer the broker version by
            probing various APIs. Default: ``auto``
        security_protocol (str): Protocol used to communicate with brokers.
            Valid values are: ``PLAINTEXT``, ``SSL``, ``SASL_PLAINTEXT``,
            ``SASL_SSL``. Default: ``PLAINTEXT``.
        ssl_context (ssl.SSLContext): pre-configured :class:`~ssl.SSLContext`
            for wrapping socket connections. Directly passed into asyncio's
            :meth:`~asyncio.loop.create_connection`. For more
            information see :ref:`ssl_auth`.
            Default: :data:`None`
        connections_max_idle_ms (int): Close idle connections after the number
            of milliseconds specified by this config. Specifying :data:`None` will
            disable idle checks. Default: 540000 (9 minutes).
        enable_idempotence (bool): When set to :data:`True`, the producer will
            ensure that exactly one copy of each message is written in the
            stream. If :data:`False`, producer retries due to broker failures,
            etc., may write duplicates of the retried message in the stream.
            Note that enabling idempotence acks to set to ``all``. If it is not
            explicitly set by the user it will be chosen. If incompatible
            values are set, a :exc:`ValueError` will be thrown.
            New in version 0.5.0.
        sasl_mechanism (str): Authentication mechanism when security_protocol
            is configured for ``SASL_PLAINTEXT`` or ``SASL_SSL``. Valid values
            are: ``PLAIN``, ``GSSAPI``, ``SCRAM-SHA-256``, ``SCRAM-SHA-512``,
            ``OAUTHBEARER``.
            Default: ``PLAIN``
        sasl_plain_username (str): username for SASL ``PLAIN`` authentication.
            Default: :data:`None`
        sasl_plain_password (str): password for SASL ``PLAIN`` authentication.
            Default: :data:`None`
        sasl_oauth_token_provider (:class:`~aiokafka.abc.AbstractTokenProvider`):
            OAuthBearer token provider instance.
            Default: :data:`None`

    Note:
        Many configuration parameters are taken from the Java client:
        https://kafka.apache.org/documentation.html#producerconfigs
    """

    _PRODUCER_CLIENT_ID_SEQUENCE = ...
    _COMPRESSORS = ...
    _closed = ...
    _source_traceback = ...
    def __init__(
        self,
        *,
        loop: asyncio.AbstractEventLoop | None = ...,
        bootstrap_servers: str | list[str] = ...,
        client_id: str | None = ...,
        metadata_max_age_ms: int = ...,
        request_timeout_ms: int = ...,
        api_version: str = ...,
        acks: Literal[0] | Literal[1] | Literal["all"] | object = ...,
        # Skip type-checking for mypy because it doesn't seem to realize KT_contra and VT_contra are typevars
        key_serializer: Callable[[KT_contra], bytes] = _identity,  # type: ignore
        value_serializer: Callable[[VT_contra], bytes] = _identity,  # type: ignore
        compression_type: (
            Literal["gzip"]
            | Literal["snappy"]
            | Literal["lz4"]
            | Literal["zstd"]
            | None
        ) = ...,
        max_batch_size: int = ...,
        partitioner: Callable[[bytes, list[int], list[int]], int] = ...,
        max_request_size: int = ...,
        linger_ms: int = ...,
        retry_backoff_ms: int = ...,
        security_protocol: (
            Literal["PLAINTEXT"]
            | Literal["SSL"]
            | Literal["SASL_PLAINTEXT"]
            | Literal["SASL_SSL"]
        ) = ...,
        ssl_context: SSLContext | None = ...,
        connections_max_idle_ms: int = ...,
        enable_idempotence: bool = ...,
        transactional_id: int | str | None = ...,
        transaction_timeout_ms: int = ...,
        sasl_mechanism: (
            Literal["PLAIN"]
            | Literal["GSSAPI"]
            | Literal["SCRAM-SHA-256"]
            | Literal["SCRAM-SHA-512"]
            | Literal["OAUTHBEARER"]
        ) = ...,
        sasl_plain_password: str | None = ...,
        sasl_plain_username: str | None = ...,
        sasl_kerberos_service_name: str = ...,
        sasl_kerberos_domain_name: str | None = ...,
        sasl_oauth_token_provider: AbstractTokenProvider | None = ...,
    ) -> None: ...
    def __del__(self, _warnings: ModuleType = ...) -> None: ...
    async def start(self) -> None:
        """Connect to Kafka cluster and check server version"""

    async def flush(self) -> None:
        """Wait until all batches are Delivered and futures resolved"""

    async def stop(self) -> None:
        """Flush all pending data and close all connections to kafka cluster"""

    async def partitions_for(self, topic: str) -> set[int]:
        """Returns set of all known partitions for the topic."""

    async def send(
        self,
        topic: str,
        value: VT_contra | None = ...,
        key: KT_contra | None = ...,
        partition: int | None = ...,
        timestamp_ms: int | None = ...,
        headers: Iterable[tuple[str, bytes]] | None = ...,
    ) -> asyncio.Future[RecordMetadata]:
        """Publish a message to a topic.

        Arguments:
            topic (str): topic where the message will be published
            value (Optional): message value. Must be type :class:`bytes`, or be
                serializable to :class:`bytes` via configured `value_serializer`. If
                value is :data:`None`, key is required and message acts as a
                ``delete``.

                See `Kafka compaction documentation
                <https://kafka.apache.org/documentation.html#compaction>`__ for
                more details. (compaction requires kafka >= 0.8.1)
            partition (int, Optional): optionally specify a partition. If not
                set, the partition will be selected using the configured
                `partitioner`.
            key (Optional): a key to associate with the message. Can be used to
                determine which partition to send the message to. If partition
                is :data:`None` (and producer's partitioner config is left as default),
                then messages with the same key will be delivered to the same
                partition (but if key is :data:`None`, partition is chosen randomly).
                Must be type :class:`bytes`, or be serializable to bytes via configured
                `key_serializer`.
            timestamp_ms (int, Optional): epoch milliseconds (from Jan 1 1970
                UTC) to use as the message timestamp. Defaults to current time.
            headers (Optional): Kafka headers to be included in the message using
                the format ``[("key", b"value")]``. Iterable of tuples where key
                is a normal string and value is a byte string.

        Returns:
            asyncio.Future: object that will be set when message is
            processed

        Raises:
            ~aiokafka.errors.KafkaTimeoutError: if we can't schedule this record
                (pending buffer is full) in up to `request_timeout_ms`
                milliseconds.

        Note:
            The returned future will wait based on `request_timeout_ms`
            setting. Cancelling the returned future **will not** stop event
            from being sent, but cancelling the :meth:`send` coroutine itself
            **will**.
        """

    async def send_and_wait(
        self,
        topic: str,
        value: VT_contra | None = ...,
        key: KT_contra | None = ...,
        partition: int | None = ...,
        timestamp_ms: int | None = ...,
        headers: Iterable[tuple[str, bytes]] | None = ...,
    ) -> RecordMetadata:
        """Publish a message to a topic and wait the result"""

    def create_batch(self) -> BatchBuilder:
        """Create and return an empty :class:`.BatchBuilder`.

        The batch is not queued for send until submission to :meth:`send_batch`.

        Returns:
            BatchBuilder: empty batch to be filled and submitted by the caller.
        """

    async def send_batch(
        self, batch: BatchBuilder, topic: str, *, partition: int
    ) -> asyncio.Future[RecordMetadata]:
        """Submit a BatchBuilder for publication.

        Arguments:
            batch (BatchBuilder): batch object to be published.
            topic (str): topic where the batch will be published.
            partition (int): partition where this batch will be published.

        Returns:
            asyncio.Future: object that will be set when the batch is
                delivered.
        """

    async def begin_transaction(self) -> None: ...
    async def commit_transaction(self) -> None: ...
    async def abort_transaction(self) -> None: ...
    def transaction(self) -> TransactionContext:
        """Start a transaction context"""

    async def send_offsets_to_transaction(
        self,
        offsets: dict[TopicPartition, int | tuple[int, str] | OffsetAndMetadata],
        group_id: str,
    ) -> None: ...
    async def __aenter__(self) -> AIOKafkaProducer[KT_contra, VT_contra]: ...
    async def __aexit__(
        self, exc_type: type[ET] | None, exc: ET | None, tb: TracebackType | None
    ) -> None: ...

class TransactionContext:
    def __init__(self, producer: AIOKafkaProducer[KT_contra, VT_contra]) -> None: ...
    async def __aenter__(self) -> TransactionContext: ...
    async def __aexit__(
        self, exc_type: type[ET] | None, exc: ET | None, tb: TracebackType | None
    ) -> None: ...
