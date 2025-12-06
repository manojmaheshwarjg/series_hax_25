#!/usr/bin/env python
"""
API-to-Kafka Bridge
Polls the Series API for new messages and publishes them to Kafka
This bridges the gap since the hackathon platform isn't auto-publishing incoming messages
"""

import os
import sys
import time
import json
import logging
from datetime import datetime, timedelta
from dotenv import load_dotenv
from confluent_kafka import Producer
import requests

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class APIToKafkaBridge:
    def __init__(self):
        # API setup
        self.api_key = os.getenv('API_KEY')
        self.base_url = os.getenv('API_BASE_URL')
        self.user_phone = os.getenv('USER_PHONE')
        self.headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        
        # Kafka producer setup
        conf = {
            'bootstrap.servers': os.getenv('KAFKA_BOOTSTRAP_SERVERS'),
            'security.protocol': 'SASL_SSL',
            'sasl.mechanisms': 'PLAIN',
            'sasl.username': os.getenv('SASL_USERNAME'),
            'sasl.password': os.getenv('SASL_PASSWORD'),
        }
        self.producer = Producer(conf)
        self.topic = os.getenv('KAFKA_TOPIC')
        
        # Track last seen message ID to avoid duplicates
        self.last_message_id = None
        self.poll_interval = 2  # seconds
        
    def get_chats(self):
        """Get all chats involving the user phone"""
        try:
            response = requests.get(
                f"{self.base_url}/api/chats",
                headers=self.headers,
                params={'phone_number': self.user_phone},
                timeout=10
            )
            response.raise_for_status()
            return response.json().get('data', [])
        except Exception as e:
            logger.error(f"Error getting chats: {e}")
            return []
    
    def get_chat_messages(self, chat_id):
        """Get messages from a specific chat"""
        try:
            response = requests.get(
                f"{self.base_url}/api/chats/{chat_id}/chat_messages",
                headers=self.headers,
                timeout=10
            )
            response.raise_for_status()
            return response.json().get('data', [])
        except Exception as e:
            logger.error(f"Error getting messages for chat {chat_id}: {e}")
            return []
    
    def publish_to_kafka(self, event):
        """Publish event to Kafka topic"""
        try:
            self.producer.produce(
                self.topic,
                key=event.get('event_id', '').encode('utf-8'),
                value=json.dumps(event).encode('utf-8')
            )
            self.producer.flush()
            logger.info(f"✅ Published event {event.get('event_type')} to Kafka")
            return True
        except Exception as e:
            logger.error(f"Error publishing to Kafka: {e}")
            return False
    
    def poll_and_bridge(self):
        """Main polling loop"""
        logger.info("="*60)
        logger.info("API-to-Kafka Bridge Started")
        logger.info(f"Polling API every {self.poll_interval} seconds")
        logger.info(f"Publishing to Kafka topic: {self.topic}")
        logger.info("="*60)
        
        while True:
            try:
                # Get all chats
                chats = self.get_chats()
                
                for chat in chats:
                    chat_id = chat.get('id')
                    
                    # Get messages from this chat
                    messages = self.get_chat_messages(chat_id)
                    
                    for message in messages:
                        message_id = message.get('id')
                        
                        # Skip if we've already seen this message
                        if self.last_message_id and message_id <= self.last_message_id:
                            continue
                        
                        # Check if this is an incoming message (from user, not from bot)
                        from_phone = None
                        for handle in chat.get('chat_handles', []):
                            if not handle.get('is_me', False):
                                from_phone = handle.get('phone_number')
                                break
                        
                        if from_phone == self.user_phone:
                            # This is a message FROM the user - publish to Kafka
                            event = {
                                'api_version': 'v2',
                                'created_at': message.get('sent_at', datetime.utcnow().isoformat()),
                                'data': {
                                    'attachments': [],
                                    'chat_handles': chat.get('chat_handles', []),
                                    'chat_id': str(chat_id),
                                    'from_phone': from_phone,
                                    'id': str(message_id),
                                    'is_read': message.get('is_read', False),
                                    'reaction_id': None,
                                    'sent_at': message.get('sent_at'),
                                    'service': message.get('service', 'RCS'),
                                    'text': message.get('text', '')
                                },
                                'event_id': f"bridge-{message_id}",
                                'event_type': 'message.received'
                            }
                            
                            logger.info(f"📨 New message from {from_phone}: {message.get('text', '')[:50]}")
                            self.publish_to_kafka(event)
                            
                            # Update last seen ID
                            if message_id > (self.last_message_id or 0):
                                self.last_message_id = message_id
                
                time.sleep(self.poll_interval)
                
            except KeyboardInterrupt:
                logger.info("\n🛑 Bridge stopped by user")
                break
            except Exception as e:
                logger.error(f"Error in polling loop: {e}", exc_info=True)
                time.sleep(self.poll_interval)

if __name__ == "__main__":
    bridge = APIToKafkaBridge()
    bridge.poll_and_bridge()
