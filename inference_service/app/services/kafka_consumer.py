import json
import logging
import asyncio
from typing import Callable
from ..config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class KafkaConsumer:
    """
    Simplified Kafka consumer that reads from event log file
    Can be upgraded to use aiokafka later
    """
    def __init__(self):
        self.running = False
        self.callback = None
        self.event_log_file = "/app/kafka_events.log"
        self.processed_events = set()
    
    def set_callback(self, callback: Callable):
        """Set callback function to handle consumed messages"""
        self.callback = callback
    
    async def start(self):
        """Start consuming messages"""
        self.running = True
        logger.info("Kafka consumer started (reading from event log)")
        
        # Start background task to monitor event log
        asyncio.create_task(self.consume_loop())
    
    async def stop(self):
        """Stop consuming"""
        self.running = False
        logger.info("Kafka consumer stopped")
    
    async def consume_loop(self):
        """Continuously monitor and consume events"""
        while self.running:
            try:
                await self.read_events()
                await asyncio.sleep(2)  # Check every 2 seconds
            except Exception as e:
                logger.error(f"Error in consume loop: {e}")
                await asyncio.sleep(5)
    
    async def read_events(self):
        """Read new events from log file"""
        try:
            import os
            if not os.path.exists(self.event_log_file):
                return
            
            with open(self.event_log_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if not line or line in self.processed_events:
                        continue
                    
                    try:
                        event = json.loads(line)
                        
                        # Mark as processed
                        self.processed_events.add(line)
                        
                        # Call callback
                        if self.callback:
                            await self.callback(event)
                        
                        logger.info(f"Processed event: {event.get('event')}")
                    except json.JSONDecodeError:
                        logger.warning(f"Invalid JSON in event log: {line}")
        except Exception as e:
            logger.error(f"Error reading events: {e}")

# Global instance
kafka_consumer = KafkaConsumer()