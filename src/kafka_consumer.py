"""
Kafka consumer for Series AI Friend
Connects to Confluent Cloud and processes incoming events
"""

import json
import logging
import time
from typing import Callable, Dict, Any
from confluent_kafka import Consumer, KafkaError, KafkaException
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

        # Event handlers by type
        self.handlers: Dict[str, Callable] = {}

        # Configure consumer
        self.config = {
            'bootstrap.servers': self.bootstrap_servers,
            'group.id': 'series-ai-friend-consumer',
            'auto.offset.reset': 'latest',  # Start from latest messages
            'enable.auto.commit': True,
            'security.protocol': 'SASL_SSL',
            'sasl.mechanisms': 'PLAIN',
            'sasl.username': self.sasl_username,
            'sasl.password': self.sasl_password,
        }

        self.consumer = None
        self.running = False

    def register_handler(self, event_type: str, handler: Callable):
        """Register a handler function for a specific event type"""
        self.handlers[event_type] = handler
        logger.info(f"Registered handler for event type: {event_type}")

    def connect(self):
        """Initialize connection to Kafka"""
        try:
            self.consumer = Consumer(self.config)
            self.consumer.subscribe([self.topic])
            logger.info(f"Connected to Kafka topic: {self.topic}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Kafka: {e}")
            return False

    def process_event(self, event_data: Dict[str, Any]):
        """Route event to appropriate handler"""
        event_type = event_data.get('type')

        if not event_type:
            logger.warning("Event missing 'type' field")
            return

        logger.debug(f"Processing event type: {event_type}")

        # Try to find specific handler
        handler = self.handlers.get(event_type)

        if handler:
            try:
                handler(event_data)
            except Exception as e:
                logger.error(f"Error in handler for {event_type}: {e}", exc_info=True)
        else:
            # Try wildcard handlers (e.g., "typing_indicator.*")
            for registered_type, handler_func in self.handlers.items():
                if '*' in registered_type:
                    prefix = registered_type.replace('.*', '')
                    if event_type.startswith(prefix):
                        try:
                            handler_func(event_data)
                            return
                        except Exception as e:
                            logger.error(f"Error in wildcard handler for {event_type}: {e}", exc_info=True)
                            return

            logger.debug(f"No handler registered for event type: {event_type}")

    def start(self):
        """Start consuming messages from Kafka"""
        if not self.consumer:
            if not self.connect():
                logger.error("Cannot start consumer - connection failed")
                return

        self.running = True
        logger.info("Starting Kafka consumer loop...")

        try:
            while self.running:
                msg = self.consumer.poll(timeout=1.0)

                if msg is None:
                    continue

                if msg.error():
                    if msg.error().code() == KafkaError._PARTITION_EOF:
                        logger.debug(f"Reached end of partition {msg.partition()}")
                    else:
                        logger.error(f"Kafka error: {msg.error()}")
                        raise KafkaException(msg.error())
                else:
                    # Parse message
                    try:
                        event_data = json.loads(msg.value().decode('utf-8'))
                        logger.info(f"Received event: {event_data.get('type', 'unknown')}")
                        self.process_event(event_data)
                    except json.JSONDecodeError as e:
                        logger.error(f"Failed to parse message: {e}")
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
            self.consumer.close()
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
