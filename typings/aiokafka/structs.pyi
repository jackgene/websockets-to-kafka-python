from dataclasses import dataclass
from typing import Generic, List, NamedTuple, Optional, Sequence, Tuple, TypeVar
from aiokafka.errors import KafkaError

__all__ = ["OffsetAndMetadata", "TopicPartition", "RecordMetadata", "ConsumerRecord", "BrokerMetadata", "PartitionMetadata"]
class TopicPartition(NamedTuple):
    """A topic and partition tuple"""
    topic: str
    partition: int
    ...


class BrokerMetadata(NamedTuple):
    """A Kafka broker metadata used by admin tools"""
    nodeId: int | str
    host: str
    port: int
    rack: Optional[str]
    ...


class PartitionMetadata(NamedTuple):
    """A topic partition metadata describing the state in the MetadataResponse"""
    topic: str
    partition: int
    leader: int
    replicas: List[int]
    isr: List[int]
    error: Optional[KafkaError]
    ...


class OffsetAndMetadata(NamedTuple):
    """The Kafka offset commit API

    The Kafka offset commit API allows users to provide additional metadata
    (in the form of a string) when an offset is committed. This can be useful
    (for example) to store information about which node made the commit,
    what time the commit was made, etc.
    """
    offset: int
    metadata: str
    ...


class RecordMetadata(NamedTuple):
    """Returned when a :class:`~.AIOKafkaProducer` sends a message"""
    topic: str
    partition: int
    topic_partition: TopicPartition
    offset: int
    timestamp: Optional[int]
    timestamp_type: int
    log_start_offset: Optional[int]
    ...


KT = TypeVar("KT", covariant=True)
VT = TypeVar("VT", covariant=True)
@dataclass
class ConsumerRecord(Generic[KT, VT]):
    topic: str
    partition: int
    offset: int
    timestamp: int
    timestamp_type: int
    key: Optional[KT]
    value: Optional[VT]
    checksum: Optional[int]
    serialized_key_size: int
    serialized_value_size: int
    headers: Sequence[Tuple[str, bytes]]
    ...


class OffsetAndTimestamp(NamedTuple):
    offset: int
    timestamp: Optional[int]
    ...


