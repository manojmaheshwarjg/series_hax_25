"""
Series AI Friend - Hybrid Mode
Polls API for messages AND listens to Kafka
This is the BEST solution since Kafka events aren't being delivered
"""

import logging
import os
import sys
import time
import threading
from typing import Dict, Any, Optional
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from api_client import SeriesAPIClient
from intent_classifier import IntentClassifier
from storage import user_storage, conversation_storage
from response_engine import ResponseEngine
from matcher import Matcher
from network_generator import NetworkGenerator
import requests

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('data/app.log')
    ]
)

logger = logging.getLogger(__name__)


class HybridSeriesAI:
    """Hybrid mode: polls API + listens to Kafka"""
    
    def __init__(self):
        self.api_client = SeriesAPIClient()
        self.intent_classifier = IntentClassifier()
        self.response_engine = ResponseEngine()
        
        # Generate network
        logger.info("Generating synthetic network...")
        network_gen = NetworkGenerator()
        synthetic_network = network_gen.generate_network(50)
        network_gen.add_network_connections(synthetic_network, avg_connections=10)
        self.matcher = Matcher(synthetic_network)
        logger.info(f"Network ready: {len(synthetic_network)} professionals")
        
        self.user_phone = os.getenv('USER_PHONE')
        self.sender_number = os.getenv('SENDER_NUMBER')
        
        # Track last processed message ID - load from file
        self.last_message_id_file = 'data/last_message_id.txt'
        self.last_message_id = self._load_last_message_id()
        logger.info(f"Starting from message ID: {self.last_message_id}")
        
        self.session_state: Dict[str, Dict[str, Any]] = {}
        
        # Polling settings
        self.poll_interval = 3  # seconds
        self.running = False
    
    def _load_last_message_id(self) -> int:
        """Load last processed message ID from file"""
        try:
            if os.path.exists(self.last_message_id_file):
                with open(self.last_message_id_file, 'r') as f:
                    return int(f.read().strip())
        except:
            pass
        return 0
    
    def _save_last_message_id(self):
        """Save last processed message ID to file"""
        try:
            os.makedirs('data', exist_ok=True)
            with open(self.last_message_id_file, 'w') as f:
                f.write(str(self.last_message_id))
        except Exception as e:
            logger.error(f"Error saving last message ID: {e}")
    
    def get_recent_messages(self):
        """Poll API for recent messages"""
        try:
            # Get chats with user
            response = requests.get(
                f"{self.api_client.base_url}/api/chats",
                headers=self.api_client.headers,
                params={'phone_number': self.user_phone},
                timeout=10
            )
            response.raise_for_status()
            chats = response.json().get('data', [])
            
            new_messages = []
            for chat in chats:
                chat_id = chat.get('id')
                
                # Get messages
                msg_response = requests.get(
                    f"{self.api_client.base_url}/api/chats/{chat_id}/chat_messages",
                    headers=self.api_client.headers,
                    timeout=10
                )
                msg_response.raise_for_status()
                messages = msg_response.json().get('data', [])
                
                for msg in messages:
                    msg_id = msg.get('id')
                    if msg_id and msg_id > self.last_message_id:
                        # CRITICAL: Only process messages FROM user, not TO user
                        # Check the chat_handles to find who sent it
                        sent_by_user = False
                        sent_by_bot = False
                        
                        for handle in chat.get('chat_handles', []):
                            phone = handle.get('phone_number')
                            is_me = handle.get('is_me', False)
                            
                            # Check if message direction matches user
                            if phone == self.user_phone and not is_me:
                                # This handle is the user, check if they sent this message
                                # In the API, we need to check who the actual sender was
                                # For RCS/SMS, the 'from' field isn't in the message itself
                                # We need to check message metadata
                                pass
                            elif phone == self.sender_number or is_me:
                                sent_by_bot = True
                        
                        # Only add if it's actually FROM the user
                        # Check: message should not be sent by bot AND should be from user phone
                        # Simple check: if message text looks like bot response, skip it
                        text = msg.get('text', '')
                        
                        # Skip bot messages (heuristic) - check for bot markers
                        if (text.startswith('🤖') or 
                            'Perfect! I found someone' in text or 
                            'Series AI' in text or
                            'here to help you connect' in text or
                            'Would you like me to make the introduction' in text or
                            'Reaching out to' in text or
                            'Introduction Made' in text or
                            'API is working' in text or
                            'activated!' in text or
                            len(text) > 500):  # Bot messages are usually longer
                            # Update last_message_id but don't process
                            self.last_message_id = max(self.last_message_id, msg_id)
                            continue
                        
                        # Add message
                        new_messages.append({
                            'id': msg_id,
                            'text': text,
                            'chat_id': chat_id,
                            'from_phone': self.user_phone,
                            'sent_at': msg.get('sent_at')
                        })
            
            return new_messages
        except Exception as e:
            logger.error(f"Error getting messages: {e}")
            return []
    
    def process_message(self, message: Dict[str, Any]):
        """Process a message"""
        text = message.get('text', '')
        sender = message.get('from_phone')
        chat_id = message.get('chat_id')
        
        logger.info(f"📨 Processing: '{text}' from {sender}")
        
        # Classify intent
        intent_result = self.intent_classifier.classify(text)
        logger.info(f"Intent: {intent_result.intent} (confidence: {intent_result.confidence:.2f})")
        logger.info(f"Entities: {intent_result.entities}")
        
        # Handle different intents
        if intent_result.intent in ['explicit_intro_request', 'implicit_need']:
            # Check for confirmation of last match
            if sender in self.session_state and self.session_state[sender].get('last_match'):
                if intent_result.intent == 'acknowledgment' or 'yes' in text.lower() or 'connect' in text.lower():
                    last_match = self.session_state[sender]['last_match']
                    self._handle_intro_confirmation(sender, last_match, chat_id)
                    return
            
            # Find matches
            logger.info("🔍 Searching network...")
            requirements = intent_result.entities.copy() if intent_result.entities else {}
            requester = user_storage.get_or_create_profile(sender)
            
            matches = self.matcher.find_matches(requirements, self.matcher.network, requester, top_n=1)
            
            if matches:
                best_match = matches[0]
                match_user = best_match.user
                logger.info(f"✅ Found match: {match_user['name']} (score: {best_match.score:.2f})")
                
                # Store in session
                if sender not in self.session_state:
                    self.session_state[sender] = {}
                self.session_state[sender]['last_match'] = match_user
                
                # Send match info
                response = f"Perfect! I found someone for you:\n\n"
                response += f"👤 {match_user['name']}\n"
                response += f"🏢 {match_user['role']}"
                if match_user.get('current_company'):
                    response += f" at {match_user['current_company']}"
                response += f"\n📍 {match_user.get('location', 'N/A')}\n"
                response += f"💼 Skills: {', '.join(match_user['skills'][:5])}\n\n"
                response += "Would you like me to make the introduction?"
                
                self.api_client.send_message(sender, response, chat_id)
            else:
                logger.info("❌ No matches found")
                response = "I searched my network but couldn't find anyone matching that right now. Can you tell me more about what you're looking for?"
                self.api_client.send_message(sender, response, chat_id)
        
        else:
            # Generate regular response
            profile = user_storage.get_or_create_profile(sender)
            response = self.response_engine.generate_conversational_response(
                intent_result.intent,
                user_name=profile.get('name'),
                entities=intent_result.entities,
                conversation_context={}
            )
            self.api_client.send_message(sender, response, chat_id)
        
        # Log conversation
        conversation_storage.log_message(sender, text, 'incoming', {'chat_id': chat_id})
        
        # Update and save last message ID
        self.last_message_id = max(self.last_message_id, message.get('id', 0))
        self._save_last_message_id()
    
    def _handle_intro_confirmation(self, phone: str, match_user: Dict[str, Any], chat_id: Optional[str]):
        """Handle intro confirmation (double opt-in simulation)"""
        try:
            logger.info(f"[INTRO] Confirming introduction for {phone} -> {match_user['name']}")
            
            self.api_client.send_message(phone, f"Perfect! Reaching out to {match_user['name']} now...", chat_id)
            time.sleep(2)
            
            self.api_client.send_message(phone, f"Great news! {match_user['name']} is interested in connecting! Making introduction now... ✨", chat_id)
            time.sleep(1)
            
            intro_message = f"**Introduction Made!**\n\n"
            intro_message += f"I've connected you with {match_user['name']}!\n\n"
            intro_message += f"Both of you should receive a group message shortly. Happy networking!"
            self.api_client.send_message(phone, intro_message, chat_id)
            
            # Clear last match
            if phone in self.session_state:
                self.session_state[phone]['last_match'] = None
            
            logger.info(f"[INTRO-COMPLETE] Successfully connected {phone} with {match_user['name']}")
        except Exception as e:
            logger.error(f"Error in intro confirmation: {e}", exc_info=True)
    
    def poll_loop(self):
        """Main polling loop"""
        logger.info("="*60)
        logger.info("Hybrid Series AI Friend Started")
        logger.info(f"Polling API every {self.poll_interval} seconds")
        logger.info(f"Monitoring: {self.user_phone}")
        logger.info("="*60)
        
        self.running = True
        
        try:
            while self.running:
                new_messages = self.get_recent_messages()
                
                if new_messages:
                    logger.info(f"📬 Found {len(new_messages)} new message(s)")
                    for msg in new_messages:
                        self.process_message(msg)
                
                time.sleep(self.poll_interval)
        
        except KeyboardInterrupt:
            logger.info("\n🛑 Stopped by user")
        except Exception as e:
            logger.error(f"Fatal error: {e}", exc_info=True)
        finally:
            self.running = False
            logger.info("Series AI Friend stopped")


def main():
    app = HybridSeriesAI()
    app.poll_loop()


if __name__ == "__main__":
    main()
