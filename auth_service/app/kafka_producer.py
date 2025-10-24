import json
import logging
import asyncio
from aiokafka import AIOKafkaProducer
from aiokafka.errors import KafkaConnectionError
from .config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class KafkaProducerClient:
    def __init__(self):
        self.producer = None
        self.broker = settings.KAFKA_BROKER
        self.max_retries = 5
        self.retry_delay = 2
    
    async def start(self):
        """Start Kafka producer with retries"""
        for attempt in range(self.max_retries):
            try:
                self.producer = AIOKafkaProducer(
                    bootstrap_servers=self.broker,
                    value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                    request_timeout_ms=10000,
                    connections_max_idle_ms=540000
                )
                await self.producer.start()
                logger.info(f"Kafka producer connected to {self.broker}")
                return
            except (KafkaConnectionError, Exception) as e:
                logger.warning(f"Kafka connection attempt {attempt + 1}/{self.max_retries} failed: {e}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay)
                else:
                    logger.error("Failed to connect to Kafka after max retries. Service will continue without Kafka.")
                    self.producer = None
    
    async def stop(self):
        """Stop Kafka producer"""
        if self.producer:
            try:
                await self.producer.stop()
                logger.info("Kafka producer stopped")
            except Exception as e:
                logger.error(f"Error stopping Kafka producer: {e}")
    
    async def send_message(self, topic: str, message: dict):
        """Send message to Kafka topic"""
        if not self.producer:
            logger.warning("Kafka producer not initialized. Message not sent.")
            return False
        
        try:
            await self.producer.send_and_wait(topic, message)
            logger.info(f"Message sent to topic '{topic}': {message}")
            return True
        except Exception as e:
            logger.error(f"Failed to send message to Kafka: {e}")
            return False

# Global producer instance
kafka_producer = KafkaProducerClient()