"""
Series AI Friend - Main Application
Coordinates Kafka consumer, intent classification, and response generation
"""

import logging
import os
import sys
import random
from typing import Dict, Any
from dotenv import load_dotenv

# Add src to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from kafka_consumer import SeriesKafkaConsumer
from api_client import SeriesAPIClient, send_message_with_typing
from intent_classifier import IntentClassifier
from storage import user_storage, conversation_storage, intro_storage

load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('data/app.log')
    ]
)

logger = logging.getLogger(__name__)


class SeriesAIFriend:
    """Main application coordinating all components"""

    def __init__(self):
        self.api_client = SeriesAPIClient()
        self.intent_classifier = IntentClassifier()
        self.consumer = SeriesKafkaConsumer()

        self.user_phone = os.getenv('USER_PHONE')
        self.sender_number = os.getenv('SENDER_NUMBER')

        # Response templates
        self.response_templates = {
            'greeting': [
                "Hey! How can I help you today?",
                "Hi there! What's up?",
                "Hey! Good to hear from you!",
                "Hi! What can I do for you?"
            ],
            'explicit_intro_request': [
                "Got it! Let me search my network for someone who fits...",
                "On it! Searching for the perfect match...",
                "Let me think... I might know someone perfect for this!",
                "Interesting! Let me check who I know..."
            ],
            'implicit_need': [
                "Hmm, sounds like you could use some help with that. Let me see who I know...",
                "I might know someone who could help with this! Give me a sec...",
                "Let me check my network - I think I know someone perfect for this!",
            ],
            'acknowledgment': [
                "👍",
                "Got it!",
                "Sounds good!",
                "Awesome!",
                "Perfect!"
            ],
            'feedback_positive': [
                "That's great to hear! I'm glad it worked out!",
                "Awesome! Love making good connections 😊",
                "So happy it was helpful!",
                "That makes my day! Glad I could help!"
            ],
            'feedback_negative': [
                "Sorry to hear that. I'll keep that in mind for next time!",
                "Got it - I'll adjust my matching for future intros.",
                "Thanks for letting me know. I'm still learning!"
            ],
            'question': [
                "Good question! Can you give me a bit more context?",
                "Let me make sure I understand... can you clarify?",
                "Hmm, can you tell me more about what you're looking for?"
            ],
            'skill_share': [
                "Nice! I'll keep that in mind if anyone needs help with that.",
                "Good to know! I'll remember that about you.",
                "Awesome! Adding that to your profile."
            ],
            'default': [
                "I'm here to help you connect with people in my network. Let me know what you need!",
                "Not sure I follow - are you looking for an introduction to someone?",
                "Want me to introduce you to someone? Just let me know what you're looking for!"
            ]
        }

        # Register event handlers
        self.consumer.register_handler('message.received', self.handle_message)
        self.consumer.register_handler('reaction.added', self.handle_reaction)
        self.consumer.register_handler('typing_indicator.*', self.handle_typing_indicator)

    def get_response_template(self, intent: str) -> str:
        """Get a random response template for an intent"""
        templates = self.response_templates.get(intent, self.response_templates['default'])
        return random.choice(templates)

    def handle_message(self, event: Dict[str, Any]):
        """Handle incoming message event"""
        try:
            logger.info(f"Handling message event: {event.get('id', 'unknown')}")

            # Extract message details
            message_data = event.get('data', {})
            sender = message_data.get('from')
            text = message_data.get('text', '')
            chat_id = message_data.get('chat_id')

            if not sender or not text:
                logger.warning("Message missing sender or text")
                return

            # Don't respond to our own messages
            if sender == self.sender_number:
                logger.debug("Ignoring our own message")
                return

            logger.info(f"Message from {sender}: {text}")

            # Log conversation
            conversation_storage.log_message(sender, text, 'incoming', {
                'chat_id': chat_id,
                'event_id': event.get('id')
            })

            # Update user profile
            profile = user_storage.get_or_create_profile(sender)
            user_storage.add_conversation_message(sender, {
                'text': text,
                'direction': 'incoming',
                'timestamp': event.get('timestamp')
            })

            # Classify intent
            intent_result = self.intent_classifier.classify(text)
            logger.info(f"Intent: {intent_result.intent} (confidence: {intent_result.confidence:.2f})")

            # Update profile based on extracted entities
            self._update_profile_from_entities(sender, intent_result)

            # Generate response
            response = self._generate_response(sender, text, intent_result, profile)

            if response:
                # Send response with typing indicator
                complexity = self._estimate_complexity(intent_result.intent)
                send_message_with_typing(
                    self.api_client,
                    sender,
                    response,
                    complexity=complexity,
                    chat_id=chat_id
                )

                # Log outgoing message
                conversation_storage.log_message(sender, response, 'outgoing', {
                    'chat_id': chat_id,
                    'intent': intent_result.intent
                })

                user_storage.add_conversation_message(sender, {
                    'text': response,
                    'direction': 'outgoing',
                    'intent': intent_result.intent
                })

        except Exception as e:
            logger.error(f"Error handling message: {e}", exc_info=True)

    def handle_reaction(self, event: Dict[str, Any]):
        """Handle reaction event"""
        try:
            logger.info(f"Handling reaction event: {event.get('id', 'unknown')}")

            reaction_data = event.get('data', {})
            sender = reaction_data.get('from')
            reaction = reaction_data.get('reaction')
            message_id = reaction_data.get('message_id')

            logger.info(f"Reaction from {sender}: {reaction} on message {message_id}")

            # For now, just log it
            # In Phase 4, this will handle intro acceptance/rejection

        except Exception as e:
            logger.error(f"Error handling reaction: {e}", exc_info=True)

    def handle_typing_indicator(self, event: Dict[str, Any]):
        """Handle typing indicator event"""
        # Just log for now
        logger.debug(f"Typing indicator: {event.get('type', 'unknown')}")

    def _update_profile_from_entities(self, phone: str, intent_result):
        """Update user profile based on extracted entities"""
        entities = intent_result.entities

        # Add skills
        if 'technology' in entities:
            for tech in entities['technology']:
                user_storage.add_to_list(phone, 'skills', tech)

        # Add interests from industry
        if 'industry' in entities:
            for industry in entities['industry']:
                user_storage.add_to_list(phone, 'interests', industry)

        # Update location
        if 'location' in entities and entities['location']:
            user_storage.update_profile(phone, {'location': entities['location'][0]})

        # Track needs
        if intent_result.intent in ['explicit_intro_request', 'implicit_need']:
            need = self.intent_classifier.extract_need_details(
                intent_result.keywords,
                intent_result
            )
            # This will be used in Phase 4 for matching

    def _generate_response(self, phone: str, text: str, intent_result, profile: Dict) -> str:
        """Generate appropriate response based on intent"""

        intent = intent_result.intent

        # Get base response template
        response = self.get_response_template(intent)

        # Personalize if we know their name
        if profile.get('name') and random.random() < 0.3:  # 30% of the time
            response = f"{profile['name']}, {response.lower()}"

        return response

    def _estimate_complexity(self, intent: str) -> int:
        """Estimate message complexity for typing delay calculation"""
        complexity_map = {
            'greeting': 1,
            'acknowledgment': 1,
            'farewell': 1,
            'explicit_intro_request': 3,
            'implicit_need': 3,
            'question': 2,
            'skill_share': 2,
            'feedback_positive': 2,
            'feedback_negative': 2,
            'default': 2
        }

        return complexity_map.get(intent, 2)

    def start(self):
        """Start the application"""
        logger.info("=" * 60)
        logger.info("Starting Series AI Friend")
        logger.info("=" * 60)
        logger.info(f"Sender Number: {self.sender_number}")
        logger.info(f"User Phone: {self.user_phone}")
        logger.info("=" * 60)

        try:
            self.consumer.start()
        except KeyboardInterrupt:
            logger.info("Shutting down...")
        except Exception as e:
            logger.error(f"Fatal error: {e}", exc_info=True)
        finally:
            logger.info("Series AI Friend stopped")


def main():
    """Main entry point"""
    app = SeriesAIFriend()
    app.start()


if __name__ == "__main__":
    main()
