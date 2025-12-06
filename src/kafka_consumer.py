"""
Kafka consumer for Series AI Friend
Connects to Confluent Cloud and processes incoming events
Switched to confluent-kafka to avoid kafka-python packaging issues on Windows
"""

import json
import logging
import time
from typing import Callable, Dict, Any
from confluent_kafka import Consumer, KafkaError
import os
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


class SeriesKafkaConsumer:
    """Handles Kafka event consumption and routing"""

    def __init__(self):
        self.bootstrap_servers = os.getenv('KAFKA_BOOTSTRAP_SERVERS')
        self.topic = os.getenv('KAFKA_TOPIC')
        self.sasl_username = os.getenv('SASL_USERNAME')
        self.sasl_password = os.getenv('SASL_PASSWORD')
        self.group_id = os.getenv('KAFKA_CONSUMER_GROUP') or 'series-ai-bot-v1'

        # Event handlers by type
        self.handlers: Dict[str, Callable] = {}

        self.consumer: Consumer | None = None
        self.running = False

    def register_handler(self, event_type: str, handler: Callable):
        """Register a handler function for a specific event type"""
        self.handlers[event_type] = handler
        logger.info(f"Registered handler for event type: {event_type}")

    def connect(self) -> bool:
        """Initialize connection to Kafka (Confluent)
        Returns True on success, False otherwise.
        """
        try:
            if not self.bootstrap_servers:
                logger.error("No bootstrap servers found")
                return False

            conf = {
                'bootstrap.servers': self.bootstrap_servers,
                'security.protocol': 'SASL_SSL',
                'sasl.mechanisms': 'PLAIN',
                'sasl.username': self.sasl_username,
                'sasl.password': self.sasl_password,
                'group.id': self.group_id,
                'auto.offset.reset': 'earliest',
                'enable.auto.commit': True,
            }

            self.consumer = Consumer(conf)
            self.consumer.subscribe([self.topic])
            logger.info(f"Connected to Kafka topic: {self.topic} (group: {self.group_id})")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Kafka: {e}")
            return False

    def process_event(self, event_data: Dict[str, Any]):
        """Route event to appropriate handler"""
        # Series API uses 'event_type' not 'type'
        event_type = (event_data.get('event_type')
                      or event_data.get('type'))

        # "Series API uses 'event_type' not 'type'" -> This line was above.
        # Check alignment. The previous block was:
        # event_type = ...
        
        # Fallback for messages missing event_type
        if not event_type:
            # Check if it looks like a message
            if event_data.get('data', {}).get('text') and (event_data.get('data', {}).get('from_phone') or event_data.get('data', {}).get('from')):
                event_type = 'message.received'
                logger.info("Inferred event_type: message.received")
            else:
                logger.warning("Event missing 'event_type' field")
                logger.debug(f"Event data: {event_data}")
                return

        logger.info(f"Received event: {event_type}")

        # Try to find specific handler
        handler = self.handlers.get(event_type)

        if not handler:
            # Try wildcard patterns (e.g., "typing_indicator.*")
            for pattern, h in self.handlers.items():
                if pattern.endswith('.*'):
                    prefix = pattern[:-2]
                    if event_type.startswith(prefix):
                        handler = h
                        break

        if handler:
            try:
                handler(event_data)
            except Exception as e:
                logger.error(f"Error in handler for {event_type}: {e}", exc_info=True)
        else:
            logger.warning(f"No handler registered for event type: {event_type}")

    def start(self):
        """Start consuming messages from Kafka"""
        if not self.consumer:
            if not self.connect():
                logger.error("Cannot start consumer - connection failed")
                return

        self.running = True
        logger.info("Starting Kafka consumer loop...")

        try:
            poll_count = 0
            while self.running:
                poll_count += 1
                if poll_count % 10 == 0:
                    logger.info(f"Consumer still polling... (count: {poll_count})")

                msg = self.consumer.poll(1.0)
                if msg is None:
                    continue
                if msg.error():
                    # Ignore EOF errors
                    if msg.error().code() == KafkaError._PARTITION_EOF:
                        continue
                    logger.error(f"Kafka error: {msg.error()}")
                    continue

                try:
                    payload = msg.value()
                    if not payload:
                        continue
                    event_data = json.loads(payload.decode('utf-8')) if isinstance(payload, (bytes, bytearray)) else payload
                    logger.info(f"About to process event...")
                    self.process_event(event_data)
                    logger.info(f"Finished processing event, continuing to poll...")
                except Exception as e:
                    logger.error(f"Error processing message: {e}", exc_info=True)
        except KeyboardInterrupt:
            logger.info("Consumer interrupted by user")
        except Exception as e:
            logger.error(f"Consumer error: {e}", exc_info=True)
        finally:
            self.stop()

    def stop(self):
        """Stop consuming and close connection"""
        self.running = False
        if self.consumer:
            logger.info("Closing Kafka consumer...")
            try:
                self.consumer.close()
            finally:
                logger.info("Kafka consumer closed")


if __name__ == "__main__":
    # Test the consumer
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    def test_handler(event_data):
        print(f"Test handler received: {event_data.get('type')}")

    consumer = SeriesKafkaConsumer()
    consumer.register_handler('message.received', test_handler)
    consumer.register_handler('reaction.added', test_handler)
    consumer.start()
