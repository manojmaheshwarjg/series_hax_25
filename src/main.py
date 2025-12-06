"""
Series AI Friend - Main Application
Coordinates Kafka consumer, intent classification, and response generation
"""

import logging
import os
import sys
import random
from typing import Dict, Any, Optional, List
from dotenv import load_dotenv

# Add src to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Add catalyst_pairing to path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'catalyst_pairing'))

from kafka_consumer import SeriesKafkaConsumer
from api_client import SeriesAPIClient, send_message_with_typing
from intent_classifier import IntentClassifier
from storage import user_storage, conversation_storage, intro_storage
from nlp_engine import AdvancedNLPEngine
from conversation_manager import ConversationManager, ConversationState
from profile_builder import ProfileBuilder
from catalyst_profile_enhancer import CatalystProfileEnhancer  # CATALYST FIELDS
from catalyst_conversation_director import CatalystConversationDirector  # PROACTIVE QUESTIONS
from vague_answer_detector import VagueAnswerDetector  # HANDLE VAGUE ANSWERS
from response_engine import ResponseEngine
from human_behavior import HumanBehaviorSimulator, MessageEditSimulator
from platform_adapter import PlatformDetector, PlatformAdapter, Platform
from hybrid_matcher import HybridMatcher  # CATALYST PAIRING ALGORITHM
from intro_manager import IntroductionManager
from network_generator import NetworkGenerator
from error_handler import (
    safe_execute, handle_api_error, ErrorRecovery,
    KafkaConnectionError, APIClientError, StorageError, MatchingError
)

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

        # Phase 2 components
        self.nlp_engine = AdvancedNLPEngine()
        self.conversation_manager = ConversationManager()
        self.profile_builder = ProfileBuilder(self.nlp_engine)
        self.catalyst_enhancer = CatalystProfileEnhancer()  # CATALYST FIELDS
        self.catalyst_director = CatalystConversationDirector()  # PROACTIVE QUESTIONS
        self.vague_detector = VagueAnswerDetector()  # HANDLE VAGUE ANSWERS
        self.response_engine = ResponseEngine()

        # Phase 3 components
        self.behavior_simulator = HumanBehaviorSimulator()
        self.platform_detector = PlatformDetector()
        self.platform_adapter = PlatformAdapter(self.platform_detector)
        self.message_editor = MessageEditSimulator(self.api_client, self.behavior_simulator)

        # Phase 4 components + CATALYST PAIRING ALGORITHM
        # Generate synthetic network for demo
        self.network = self._initialize_network()
        self.matcher = HybridMatcher(self.network)  # Using Catalyst Pairing!
        self.intro_manager = IntroductionManager(
            self.api_client,
            self.platform_adapter,
            self.response_engine
        )
        
        # Session state for conversation memory and double opt-in flow
        self.session_state: Dict[str, Dict[str, Any]] = {}

        self.user_phone = os.getenv('USER_PHONE')
        self.sender_number = os.getenv('SENDER_NUMBER')

        # Legacy response templates (keeping for backward compatibility)
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

            # Handle malformed messages
            if not message_data:
                message_data = ErrorRecovery.handle_malformed_message(event)

            # Series API format: data.from_phone, data.text
            sender = message_data.get('from_phone') or message_data.get('from')
            text = message_data.get('text', '')
            chat_id = message_data.get('chat_id')

            if not sender or not text:
                logger.warning("Message missing sender or text")
                logger.debug(f"Message data: {message_data}")
                return

            # Don't respond to our own messages
            if sender == self.sender_number:
                logger.debug("Ignoring our own message")
                return

            logger.info(f"Message from {sender}: {text}")

            # Phase 3: Detect and cache platform
            platform = self.platform_detector.detect_platform(message_data)
            self.platform_detector.set_platform_for_user(sender, platform)
            logger.info(f"Platform: {platform.value}")

            # Send platform notice if first time on SMS
            if platform == Platform.SMS and sender not in self.platform_detector.user_platforms:
                notice = self.platform_adapter.send_platform_notice(sender)
                if notice:
                    self.api_client.send_message(sender, notice, chat_id)

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

            # Get or create session state for this user
            if sender not in self.session_state:
                self.session_state[sender] = {
                    'last_match': None,
                    'pending_intro': None,
                    'conversation_history': [],
                    'rejected_matches': []  # Track rejected candidates
                }

            # Phase 2: Advanced NLP Analysis
            nlp_analysis = self.nlp_engine.analyze(text)
            logger.info(f"NLP: sentiment={nlp_analysis.sentiment_label}, topics={nlp_analysis.topics}")

            # Build conversation history for context-aware classification
            conversation_history = self.session_state[sender]['conversation_history']
            
            # Get conversation context
            conv_context = self.conversation_manager.get_conversation_state(sender)

            # Classify intent with conversation context
            intent_result = self.intent_classifier.classify(text, conversation_history)
            logger.info(f"Intent: {intent_result.intent} (confidence: {intent_result.confidence:.2f})")

            # FALLBACK: Check for confirmation keywords if there's a pending match
            # This handles cases where intent classification might miss confirmations
            confirmation_keywords = ['yes', 'sure', 'ok', 'okay', 'please', 'connect', 'go ahead', 'sounds good', 'perfect', 'great']
            text_lower = text.lower().strip()

            if self.session_state[sender]['last_match'] and any(keyword in text_lower for keyword in confirmation_keywords) and len(text.split()) <= 5:
                # Short message with confirmation keyword + pending match = likely confirmation
                logger.info(f"[FALLBACK] Detected confirmation via keywords: '{text}'")
                last_match = self.session_state[sender]['last_match']

                # Add to conversation history
                self.session_state[sender]['conversation_history'].append({"role": "user", "content": text})

                # Handle double opt-in flow
                self._handle_intro_confirmation(sender, last_match, chat_id)
                return  # Skip normal response generation

            # Phase 2: Update profile using profile builder (with intent awareness)
            profile_updates = self.profile_builder.update_profile_from_message(
                profile, text, intent_result.entities, nlp_analysis, intent_result.intent
            )
            if profile_updates:
                logger.info(f"Profile updates: {profile_updates}")
            
            # CATALYST: Extract Catalyst fields (goals, trajectory, problems, mentorship)
            catalyst_updates = self.catalyst_enhancer.enhance_profile(
                profile, text, intent_result.intent
            )
            if catalyst_updates:
                logger.info(f"[CATALYST] Profile enhancements: {catalyst_updates}")
                # CRITICAL FIX: Persist profile updates immediately
                user_storage.update_profile(sender, profile)

            
            # VAGUE ANSWER DETECTION: Check if user gave a vague answer to our last question
            if conv_context and conv_context.last_question:
                # Get context from the question we asked
                question_context = self.vague_detector.get_context_from_question(conv_context.last_question)
                
                # Check if answer is vague
                if self.vague_detector.is_vague(text, question_context):
                    logger.info(f"[VAGUE-ANSWER] Detected vague answer: '{text}'")
                    
                    # Generate quirky follow-up
                    follow_up = self.vague_detector.generate_follow_up(
                        text, question_context, conv_context.last_question
                    )
                    
                    # Return follow-up immediately (don't proceed with normal flow)
                    logger.info(f"[VAGUE-FOLLOW-UP] Asking: {follow_up}")
                    return follow_up
            
            # Save profile if any updates were made
            if profile_updates or catalyst_updates:
                user_storage.update_profile(sender, profile)
            else:
                logger.debug(f"No profile updates (likely search request, not self-description)")

            # Get conversation context
            conv_context = self.conversation_manager.get_or_create_context(sender)

            # CRITICAL: Detect if user is rejecting the last match
            rejection_keywords = ['no', 'nope', 'nah', 'someone else', 'not them', 'different', 'another']
            text_lower = text.lower().strip()
            has_rejection = any(keyword in text_lower for keyword in rejection_keywords)

            if has_rejection and self.session_state[sender]['last_match']:
                # User is rejecting the last suggested match
                rejected_match = self.session_state[sender]['last_match']
                rejected_name = rejected_match.get('name')

                if rejected_name not in self.session_state[sender]['rejected_matches']:
                    self.session_state[sender]['rejected_matches'].append(rejected_name)
                    logger.info(f"[REJECTION] User rejected: {rejected_name}")
                    logger.info(f"[REJECTION] Rejected list: {self.session_state[sender]['rejected_matches']}")

                # Clear last match so we search for new one
                self.session_state[sender]['last_match'] = None

            # Check if user is confirming a previous match (intent-based detection)
            if intent_result.intent in ['acknowledgment', 'explicit_intro_request'] and self.session_state[sender]['last_match'] and not intent_result.entities and not has_rejection:
                # User said "yes" or "connect me" - they want the last match!
                last_match = self.session_state[sender]['last_match']
                logger.info(f"[CONTEXT] User confirming intro with: {last_match['name']}")

                # Add to conversation history
                self.session_state[sender]['conversation_history'].append({"role": "user", "content": text})

                # Handle double opt-in flow
                self._handle_intro_confirmation(sender, last_match, chat_id)
                return  # Skip normal response generation

            # Add user message to conversation history
            self.session_state[sender]['conversation_history'].append({
                "role": "user",
                "content": text
            })

            # Phase 2: Generate intelligent response
            response = self._generate_intelligent_response(
                sender, text, intent_result, nlp_analysis, profile, conv_context
            )

            if response:
                # Add bot response to conversation history
                self.session_state[sender]['conversation_history'].append({
                    "role": "assistant",
                    "content": response
                })

                # Keep only last 10 messages to avoid memory bloat
                if len(self.session_state[sender]['conversation_history']) > 10:
                    self.session_state[sender]['conversation_history'] = self.session_state[sender]['conversation_history'][-10:]

                # Phase 3: Send with human-like behavior
                self._send_human_like_message(
                    sender, response, chat_id, nlp_analysis.complexity
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

                # Process any pending message edits
                self.message_editor.process_pending_edits()

        except StorageError as e:
            logger.error(f"Storage error handling message: {e}", exc_info=True)
            ErrorRecovery.send_error_notification(self.api_client, sender, 'storage_error')
        except APIClientError as e:
            logger.error(f"API error handling message: {e}", exc_info=True)
            ErrorRecovery.send_error_notification(self.api_client, sender, 'api_error')
        except Exception as e:
            logger.error(f"Error handling message: {e}", exc_info=True)
            ErrorRecovery.send_error_notification(self.api_client, sender, 'unknown')

    def handle_reaction(self, event: Dict[str, Any]):
        """Handle reaction event"""
        try:
            logger.info(f"Handling reaction event: {event.get('id', 'unknown')}")

            reaction_data = event.get('data', {})
            sender = reaction_data.get('from')
            reaction = reaction_data.get('reaction')
            message_id = reaction_data.get('message_id')

            logger.info(f"Reaction from {sender}: {reaction} on message {message_id}")

            # Phase 3 & 4: Handle reaction using platform adapter
            result = self.platform_adapter.handle_reaction(sender, reaction, 'confirmation')

            if result is not None:
                logger.info(f"Reaction interpreted as: {result}")

                # Phase 4: Check if this is an intro confirmation
                pending_intro = self.intro_manager.get_pending_intro_for_user(sender)

                if pending_intro:
                    # This is an intro confirmation
                    intro_id = pending_intro['id']

                    if pending_intro['requester'] == sender:
                        # Requester responding
                        response = self.intro_manager.handle_requester_response(intro_id, result)
                    elif pending_intro['match'] == sender:
                        # Match responding
                        response = self.intro_manager.handle_match_response(intro_id, result)
                    else:
                        response = None

                    if response:
                        self.api_client.send_message(sender, response)
                else:
                    # Generic acknowledgment
                    ack = "Got it!" if result else "No problem!"
                    self.api_client.send_message(sender, ack)

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

    def _generate_intelligent_response(self, phone: str, text: str, intent_result,
                                       nlp_analysis, profile: Dict, conv_context) -> str:
        """
        Generate intelligent, context-aware response using Phase 2 components

        Args:
            phone: User's phone number
            text: User's message
            intent_result: Intent classification result
            nlp_analysis: Advanced NLP analysis
            profile: User profile
            conv_context: Conversation context

        Returns:
            Generated response
        """
        intent = intent_result.intent

        # Check if user is answering a question
        if self.conversation_manager.is_answering_question(phone):
            answer = self.conversation_manager.extract_answer_to_question(
                phone, text, intent_result.entities
            )
            if answer:
                # Store the answer
                for key, value in answer.items():
                    self.conversation_manager.add_gathered_info(phone, key, value)

                # Check if we have enough info to match
                if self.conversation_manager.has_sufficient_info(phone):
                    # Phase 4: Find matches
                    return self._handle_matching_request(phone, profile)
                else:
                    # Ask another question
                    next_question = self.conversation_manager.get_next_question(
                        phone, intent_result.entities
                    )
                    if next_question:
                        self.conversation_manager.update_state(
                            phone, ConversationState.CLARIFYING_REQUIREMENTS
                        )
                        return self.response_engine.generate_response(
                            'clarification_request',
                            {'question': next_question}
                        )

        # Handle intro requests with progressive disclosure
        if intent in ['explicit_intro_request', 'implicit_need']:
            # Add to conversation context
            for entity_type, values in intent_result.entities.items():
                for value in values:
                    self.conversation_manager.add_gathered_info(phone, entity_type, value)

            # Check if we need more info
            if self.conversation_manager.needs_clarification(phone, intent_result.entities):
                next_question = self.conversation_manager.get_next_question(
                    phone, intent_result.entities
                )
                if next_question:
                    self.conversation_manager.update_state(
                        phone, ConversationState.GATHERING_NEED
                    )
                    # Acknowledge first, then ask
                    ack = self.response_engine.generate_response('explicit_intro_request')
                    return f"{ack}\n\n{next_question}"
            else:
                # Have enough info, but check if we should build profile/Catalyst data first
                conversation_turn = len(conv_context.questions_asked) if conv_context else 0
                
                if self.catalyst_director.should_ask_catalyst_question(profile, conversation_turn):
                    catalyst_question = self.catalyst_director.get_next_catalyst_question(profile)
                    if catalyst_question:
                        logger.info(f"[CATALYST-DIRECTOR] Asking: {catalyst_question}")
                        # Acknowledge request + ask Catalyst question
                        ack = "On it 🔍"
                        response = f"{ack}\n\n{catalyst_question}"
                        
                        # Update state so we know we asked
                        conv_context.last_question = catalyst_question
                        conv_context.current_topic = 'catalyst_profile'
                        self.conversation_manager.update_state(phone, ConversationState.GATHERING_NEED)
                        
                        return response

                # If no Catalyst questions needed, find matches
                return self._handle_matching_request(phone, profile)

        # CRITICAL FIX: Only pass gathered_info for search-related intents
        # For other intents (acknowledgment, feedback, etc.), gathered_info contains
        # SEARCH REQUIREMENTS which should NOT be treated as user attributes
        search_related_intents = {
            'explicit_intro_request',
            'implicit_need',
            'question',
            'clarification'
        }

        context_for_response = {}
        if intent in search_related_intents and conv_context:
            # Safe to pass - user is actively searching
            context_for_response = conv_context.gathered_info
            logger.debug(f"[RESPONSE-CTX] Passing search context for intent: {intent}")
        else:
            # Don't pass search requirements - they're not about the user!
            logger.debug(f"[RESPONSE-CTX] Not passing search context for intent: {intent}")

        # Use response engine with context and history
        response = self.response_engine.generate_conversational_response(
            intent,
            user_name=profile.get('name'),
            entities=intent_result.entities,
            conversation_context=context_for_response,
            message_history=self.session_state[phone]['conversation_history']
        )

        # CATALYST: Check if we should ask a Catalyst question
        # This happens BEFORE matching to collect bidirectional value data
        conversation_turn = len(conv_context.questions_asked) if conv_context else 0
        
        if intent in ['explicit_intro_request', 'implicit_need']:
            # User is requesting an intro - check if we should collect Catalyst data first
            if self.catalyst_director.should_ask_catalyst_question(profile, conversation_turn):
                catalyst_question = self.catalyst_director.get_next_catalyst_question(profile)
                if catalyst_question:
                    logger.info(f"[CATALYST-DIRECTOR] Asking: {catalyst_question}")
                    # Acknowledge request + ask Catalyst question
                    ack = "On it 🔍"
                    response = f"{ack}\n\n{catalyst_question}"

                    # Update state so we know we asked
                    conv_context.last_question = catalyst_question
                    conv_context.current_topic = 'catalyst_profile'
                    
                    return response

        # Adapt tone to user's communication style
        comm_style = profile.get('communication_style', 'neutral')
        response = self.response_engine.adapt_tone(response, comm_style)

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

    def _send_human_like_message(self, recipient: str, message: str, chat_id: Optional[str],
                                  complexity: int):
        """
        Send message with human-like behavior (Phase 3)

        Args:
            recipient: Phone number to send to
            message: Message text
            chat_id: Chat ID
            complexity: Message complexity (1-5)
        """
        import time

        # Check if platform supports typing indicators
        if self.platform_adapter.should_use_typing_indicator(recipient):
            # Calculate realistic typing delay
            typing_delay = self.behavior_simulator.calculate_typing_delay(message, complexity)
            typing_duration_ms = int(typing_delay * 1000)

            # Send typing indicator
            self.api_client.send_typing_indicator(recipient, typing_duration_ms)

            # Wait for typing delay
            time.sleep(typing_delay)
        else:
            # SMS: Just a small delay
            small_delay = self.behavior_simulator.calculate_typing_delay(message, complexity) * 0.5
            time.sleep(min(small_delay, 3.0))

        # Split message if too long for platform
        message_parts = self.platform_adapter.split_long_message(recipient, message)

        # Send message(s)
        for part in message_parts:
            result = self.api_client.send_message(recipient, part, chat_id)

            # Schedule message edit if applicable
            if result and 'message_id' in result:
                self.message_editor.schedule_edit(
                    result['message_id'],
                    part,
                    chat_id,
                    recipient
                )

            # Small delay between parts
            if len(message_parts) > 1:
                time.sleep(0.5)

    def _initialize_network(self) -> List[Dict[str, Any]]:
        """Initialize synthetic network for demo with Catalyst fields"""
        generator = NetworkGenerator()
        network = generator.generate_network(200)  # 200 users for better Catalyst matching
        generator.add_network_connections(network, avg_connections=10)

        logger.info(f"Initialized network with {len(network)} users (Catalyst-enhanced profiles)")
        return network

    @safe_execute(fallback_value="Sorry, I'm having trouble searching my network right now. Can you try again?")
    def _handle_matching_request(self, phone: str, profile: Dict[str, Any]) -> str:
        """
        Handle matching request (Phase 4)

        Args:
            phone: User's phone number
            profile: User's profile

        Returns:
            Response message
        """
        try:
            # Get gathered requirements
            requirements = self.conversation_manager.get_gathered_info(phone)

            logger.info(f"Finding matches for: {requirements}")

            # Get rejected matches to exclude from search
            excluded_names = []
            if phone in self.session_state:
                excluded_names = self.session_state[phone].get('rejected_matches', [])

            # Find matches using CATALYST PAIRING ALGORITHM (excluding rejected ones)
            matches = self.matcher.find_best_matches(
                requirements, self.network, profile,
                top_n=3, use_catalyst=True
            )
            
            # Filter out excluded names manually (HybridMatcher doesn't have excluded_names param)
            if excluded_names:
                matches = [m for m in matches if m.user.get('name') not in excluded_names]

            if not matches:
                # No matches found
                self.conversation_manager.reset_context(phone)
                return "Hmm, I don't have anyone in my network who fits right now. But I'll keep this in mind!"

            # Get best match
            best_match = matches[0]
            
            # Store match in session for conversation memory
            if phone in self.session_state:
                self.session_state[phone]['last_match'] = best_match.user
                logger.info(f"[MATCH-FOUND] {best_match.user['name']} (score: {best_match.score:.2f})")

            # Generate match introduction message
            match_user = best_match.user
            response = f"Perfect! I found someone for you:\n\n"
            response += f"**{match_user['name']}**\n"
            response += f"{match_user['role']}"
            if match_user.get('current_company'):
                response += f" at {match_user['current_company']}"
            response += f"\nLocation: {match_user.get('location', 'N/A')}\n"
            response += f"Skills: {', '.join(match_user['skills'][:5])}\n\n"
            response += "Would you like me to make the introduction?"
            
            return response
        except Exception as e:
            logger.error(f"Matching error: {e}", exc_info=True)
            raise MatchingError(f"Failed to find matches: {e}")

    
    def _handle_intro_confirmation(self, phone: str, match_user: Dict[str, Any], chat_id: Optional[str]):
        """
        Handle user confirming they want an introduction (double opt-in flow)
        
        Args:
            phone: User's phone number
            match_user: The matched user
            chat_id: Chat ID
        """
        import time
        
        try:
            logger.info(f"[DOUBLE-OPT-IN] Starting introduction flow for {phone} -> {match_user['name']}")
            
            # Step 1: Acknowledge and reach out to match
            ack_message = f"Perfect! Reaching out to {match_user['name']} now..."
            self.api_client.send_message(phone, ack_message, chat_id)
            
            # Simulate delay (realistic behavior)
            time.sleep(2)
            
            # Step 2: Actually message the matched person (simulated for demo)
            match_phone = match_user.get('phone', '+15551234567')  # Demo phone
            outreach_message = f"Hey {match_user['name']}! Someone in my network is interested in connecting with you about your work. Would you be open to a quick intro?"
            
            # Only send if it's a real phone number in the network
            if match_phone and match_phone.startswith('+1'):
                logger.info(f"[OUTREACH] Messaging {match_user['name']} at {match_phone}")
                # For demo, we'll auto-accept
                # self.api_client.send_message(match_phone, outreach_message)
            
            # Step 3: Simulate acceptance (in production, this would be async)
            time.sleep(1)
            
            # Step 4: Notify requester that match accepted
            success_message = f"Great news! {match_user['name']} is interested in connecting! Making introduction now... ✨"
            self.api_client.send_message(phone, success_message, chat_id)
            
            time.sleep(1)
            # Step 5: Send final confirmation
            intro_message = f"**Introduction Made!**\n\n"
            intro_message += f"I've connected you with {match_user['name']}!\n\n"
            intro_message += f"Both of you should receive a group message shortly. Happy networking!"
            
            self.api_client.send_message(phone, intro_message, chat_id)
            
            # Clear last match from session AND reset conversation context
            if phone in self.session_state:
                self.session_state[phone]['last_match'] = None
                self.session_state[phone]['rejected_matches'] = []  # Clear rejected matches
                logger.info(f"[SESSION-CLEARED] Cleared last_match and rejected_matches")

            # CRITICAL: Clear search requirements from conversation context
            # This prevents the bot from treating search requirements as user attributes
            self.conversation_manager.reset_context(phone)
            logger.info(f"[CONTEXT-CLEARED] Cleared search requirements after successful introduction")

            logger.info(f"[INTRO-COMPLETE] Successfully connected {phone} with {match_user['name']}")
            
        except Exception as e:
            logger.error(f"Error in intro confirmation: {e}", exc_info=True)
            error_msg = "Sorry, I had trouble setting up that introduction. Can you try again?"
            self.api_client.send_message(phone, error_msg, chat_id)

    def start(self):
        """Start the application"""
        logger.info("=" * 60)
        logger.info("Starting Series AI Friend")
        logger.info("=" * 60)
        logger.info(f"Sender Number: {self.sender_number}")
        logger.info(f"User Phone: {self.user_phone}")
        logger.info("=" * 60)

        retry_count = 0
        max_retries = 3

        while retry_count < max_retries:
            try:
                self.consumer.start()
                break  # Success
            except KeyboardInterrupt:
                logger.info("Shutting down...")
                break
            except KafkaConnectionError as e:
                logger.error(f"Kafka connection error: {e}", exc_info=True)
                retry_count += 1
                if retry_count < max_retries:
                    logger.info(f"Attempting to reconnect ({retry_count}/{max_retries})...")
                    if ErrorRecovery.recover_from_kafka_disconnect(self.consumer):
                        logger.info("Reconnection successful")
                        retry_count = 0  # Reset counter
                    else:
                        import time
                        time.sleep(5 * retry_count)  # Exponential backoff
                else:
                    logger.error("Max reconnection attempts reached. Exiting.")
            except Exception as e:
                logger.error(f"Fatal error: {e}", exc_info=True)
                retry_count += 1
                if retry_count >= max_retries:
                    logger.error("Max retries reached. Exiting.")
                    break
                import time
                time.sleep(5)

        logger.info("Series AI Friend stopped")


def main():
    """Main entry point"""
    app = SeriesAIFriend()
    app.start()


if __name__ == "__main__":
    main()
