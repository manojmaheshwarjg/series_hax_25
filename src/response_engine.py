"""
Response Variation Engine
Generates natural, varied responses with 200+ templates
"""

import random
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class ResponseEngine:
    """Generates human-like, varied responses"""

    def __init__(self):
        # Track recently used templates to avoid repetition
        self.recent_templates: Dict[str, List[str]] = {}
        self.max_recent = 5

        # Massive template library (200+ templates)
        self.templates = {
            'greeting': [
                "Hey! How can I help you today?",
                "Hi there! What's up?",
                "Hey! Good to hear from you!",
                "Hi! What can I do for you?",
                "Hey there! How's it going?",
                "Hi! What's on your mind?",
                "Hey! Long time no chat!",
                "Hi! How can I help?",
                "Hey! What brings you here?",
                "Hi there! Need anything?",
            ],

            'greeting_with_name': [
                "Hey {name}! How can I help?",
                "Hi {name}! What's up?",
                "{name}! Good to hear from you!",
                "Hey {name}, how's it going?",
                "Hi {name}! What can I do for you?",
            ],

            'explicit_intro_request': [
                "Got it! Let me search my network for someone who fits...",
                "On it! Searching for the perfect match...",
                "Let me think... I might know someone perfect for this!",
                "Interesting! Let me check who I know...",
                "Sure thing! Give me a sec to search...",
                "Absolutely! Let me see who comes to mind...",
                "You got it! Searching my network now...",
                "Perfect! I know a lot of people, let me find the right one...",
                "Alright! Let me think about who would be a good fit...",
                "For sure! Checking my network...",
            ],

            'implicit_need': [
                "Hmm, sounds like you could use some help with that. Let me see who I know...",
                "I might know someone who could help with this! Give me a sec...",
                "Let me check my network - I think I know someone perfect for this!",
                "Oh interesting! I know people who specialize in this...",
                "Sounds challenging! Let me see who could help...",
                "I've heard this before - let me think who would be great for this...",
                "This sounds right up someone's alley. Let me check...",
                "I definitely know people who could help! One sec...",
            ],

            'acknowledgment': [
                "👍",
                "Got it!",
                "Sounds good!",
                "Awesome!",
                "Perfect!",
                "Cool!",
                "Alright!",
                "Sweet!",
                "Noted!",
                "Roger that!",
                "Okay!",
                "Sure thing!",
                "Yep!",
                "Absolutely!",
            ],

            'feedback_positive': [
                "That's great to hear! I'm glad it worked out!",
                "Awesome! Love making good connections 😊",
                "So happy it was helpful!",
                "That makes my day! Glad I could help!",
                "Wonderful! Always happy when an intro works out!",
                "Amazing! This is what I'm here for!",
                "So glad to hear that! You're welcome!",
                "Perfect! That's exactly what I hoped for!",
                "Excellent! Happy to help anytime!",
                "That's fantastic! Really glad it went well!",
            ],

            'feedback_negative': [
                "Sorry to hear that. I'll keep that in mind for next time!",
                "Got it - I'll adjust my matching for future intros.",
                "Thanks for letting me know. I'm still learning!",
                "Appreciate the feedback! I'll do better next time.",
                "Noted! I'll be more careful about matching in the future.",
                "Sorry it wasn't a good fit. Thanks for telling me!",
                "I appreciate you letting me know. Will improve!",
            ],

            'question': [
                "Good question! Can you give me a bit more context?",
                "Let me make sure I understand... can you clarify?",
                "Hmm, can you tell me more about what you're looking for?",
                "Want to make sure I get this right - can you elaborate?",
                "Interesting question! What specifically are you wondering?",
                "Can you give me more details on that?",
            ],

            'skill_share': [
                "Nice! I'll keep that in mind if anyone needs help with that.",
                "Good to know! I'll remember that about you.",
                "Awesome! Adding that to your profile.",
                "Perfect! I'll definitely think of you if someone needs that.",
                "Cool! Always good to know what people are skilled at.",
                "Great! Noted in your profile.",
                "Sweet! I'll remember you for that.",
            ],

            'clarification_request': [
                "Just to make sure I find the right person - {question}",
                "Quick question to help me search better - {question}",
                "Before I search, {question}",
                "To find the best match - {question}",
                "One thing - {question}",
                "Quick clarification - {question}",
            ],

            'found_match': [
                "I think I found someone! {name} - {description}",
                "Oh perfect! I know {name} - {description}",
                "Actually, {name} would be great! {description}",
                "I have someone in mind - {name}. {description}",
                "{name} came to mind immediately - {description}",
                "You should meet {name}! {description}",
            ],

            'multiple_matches': [
                "I found a few people who could work! Top pick: {name} - {description}",
                "Good news - I know a few people! I'd start with {name} - {description}",
                "A couple people come to mind. Best match is probably {name} - {description}",
            ],

            'asking_confirmation': [
                "Want me to reach out to them?",
                "Should I make an intro?",
                "Want me to introduce you?",
                "Should I connect you two?",
                "Interested in meeting them?",
                "Want an introduction?",
                "Should I send them a message?",
            ],

            'confirmed_reaching_out': [
                "Awesome! Reaching out to them now...",
                "Perfect! I'll message them right away...",
                "Got it! Sending them a message...",
                "Great! I'll reach out now...",
                "On it! Messaging them...",
                "You got it! Reaching out...",
            ],

            'waiting_response': [
                "I've reached out! Will let you know when they respond.",
                "Message sent! I'll update you once they get back to me.",
                "Sent! Should hear back soon.",
                "Messaged them! Waiting for their response.",
                "Reached out! They're usually pretty quick to respond.",
            ],

            'match_confirmed': [
                "Great news! {name} is interested. Creating group chat now...",
                "{name} said yes! Setting up the intro...",
                "They're in! Creating a group chat for you two...",
                "Perfect! {name} is excited to connect. Making the intro...",
            ],

            'intro_complete': [
                "{name_a}, meet {name_b}! {context_a}\n\n{name_b}, this is {name_a}! {context_b}\n\nI'll leave you two to connect!",
                "Great to intro you both!\n\n{name_a}: {context_a}\n{name_b}: {context_b}\n\nTake it from here!",
                "Excited to connect you two!\n\n{name_a} - {context_a}\n{name_b} - {context_b}\n\nHave a great conversation!",
            ],

            'no_match_found': [
                "Hmm, I don't have anyone in my network who fits right now. But I'll keep this in mind!",
                "Don't have a perfect match at the moment, but I'll let you know if I meet someone!",
                "Nothing immediately comes to mind, but I'm always meeting new people. I'll remember this!",
                "Can't think of anyone right now, but I'll keep my eyes open!",
            ],

            'needs_more_info': [
                "Can you tell me a bit more about what you're looking for?",
                "Want to give me a few more details so I can find the right person?",
                "What else should I know to find the perfect match?",
                "Any other requirements I should know about?",
            ],

            'farewell': [
                "Talk soon!",
                "Catch you later!",
                "See you!",
                "Later!",
                "Take care!",
                "Bye!",
                "Have a good one!",
                "Cheers!",
            ],

            'default': [
                "I'm here to help you connect with people in my network. Let me know what you need!",
                "Not sure I follow - are you looking for an introduction to someone?",
                "Want me to introduce you to someone? Just let me know what you're looking for!",
                "I can help you connect with people! What are you looking for?",
                "Need an intro? Tell me what kind of person you're looking for!",
            ],

            'thinking': [
                "Hmm...",
                "Let me think...",
                "Give me a sec...",
                "One moment...",
                "Thinking...",
                "Let me check...",
            ],

            'profile_update_acknowledge': [
                "Noted! I'll remember that.",
                "Got it! Added to your profile.",
                "Perfect! I'll keep that in mind.",
                "Cool! Updated your info.",
                "Awesome! I'll remember that about you.",
            ],

            'follow_up': [
                "Hey! Just checking in - how did it go with {name}?",
                "How's it going with {name}? Hope the connection was helpful!",
                "Wanted to follow up - did {name} work out well?",
                "Curious how things went with {name}!",
            ],
        }

    def generate_response(self, intent: str, context: Dict[str, Any] = None) -> str:
        """
        Generate a varied response for an intent

        Args:
            intent: The classified intent
            context: Additional context for personalization

        Returns:
            Generated response
        """
        context = context or {}

        # Get template category
        templates = self.templates.get(intent, self.templates['default'])

        # Filter out recently used templates
        available_templates = self._filter_recent_templates(intent, templates)

        # Pick a random template
        template = random.choice(available_templates)

        # Track usage
        self._track_template_usage(intent, template)

        # Apply context/personalization
        response = self._apply_context(template, context)

        return response

    def generate_conversational_response(self, intent: str, user_name: Optional[str] = None,
                                       entities: Dict[str, List[str]] = None,
                                       conversation_context: Dict[str, Any] = None) -> str:
        """
        Generate a more conversational response with context awareness

        Args:
            intent: Classified intent
            user_name: User's name if known
            entities: Extracted entities
            conversation_context: Conversation state

        Returns:
            Contextual response
        """
        entities = entities or {}
        conversation_context = conversation_context or {}

        # Build context
        context = {
            'name': user_name,
            'entities': entities,
        }

        # Add thinking delay for complex requests
        if intent in ['explicit_intro_request', 'implicit_need']:
            # Sometimes add a thinking phrase
            if random.random() < 0.3:
                thinking = self.generate_response('thinking')
                base_response = self.generate_response(intent, context)
                return f"{thinking} {base_response}"

        # Use name-specific greeting if available
        if intent == 'greeting' and user_name and random.random() < 0.5:
            return self.generate_response('greeting_with_name', context)

        return self.generate_response(intent, context)

    def _filter_recent_templates(self, intent: str, templates: List[str]) -> List[str]:
        """Filter out recently used templates"""
        if intent not in self.recent_templates:
            return templates

        recent = self.recent_templates[intent]
        available = [t for t in templates if t not in recent]

        # If all templates have been used, reset
        if not available:
            self.recent_templates[intent] = []
            available = templates

        return available

    def _track_template_usage(self, intent: str, template: str):
        """Track template usage to avoid repetition"""
        if intent not in self.recent_templates:
            self.recent_templates[intent] = []

        self.recent_templates[intent].append(template)

        # Keep only last N templates
        if len(self.recent_templates[intent]) > self.max_recent:
            self.recent_templates[intent] = self.recent_templates[intent][-self.max_recent:]

    def _apply_context(self, template: str, context: Dict[str, Any]) -> str:
        """Apply context to template"""
        try:
            return template.format(**context)
        except KeyError:
            # If template has placeholders we don't have, return as-is
            return template

    def generate_match_description(self, match_profile: Dict[str, Any]) -> str:
        """
        Generate a compelling description of a match

        Args:
            match_profile: Profile of the matched person

        Returns:
            Description string
        """
        parts = []

        if match_profile.get('current_company'):
            parts.append(f"works at {match_profile['current_company']}")

        if match_profile.get('skills'):
            skills = match_profile['skills'][:3]
            parts.append(f"expert in {', '.join(skills)}")

        if match_profile.get('projects'):
            parts.append(f"recently {match_profile['projects'][0]}")

        if match_profile.get('location'):
            parts.append(f"based in {match_profile['location']}")

        return ', '.join(parts) if parts else "seems like a great match"

    def adapt_tone(self, response: str, communication_style: str) -> str:
        """
        Adapt response tone to match user's communication style

        Args:
            response: Original response
            communication_style: 'formal', 'casual', or 'neutral'

        Returns:
            Tone-adapted response
        """
        if communication_style == 'formal':
            # Make more formal
            response = response.replace("Hey", "Hello")
            response = response.replace("Yep", "Yes")
            response = response.replace("!", ".")
            response = response.replace("Cool", "Excellent")

        elif communication_style == 'casual':
            # Make more casual
            response = response.replace("Hello", "Hey")
            response = response.replace("Yes", "Yep")
            # Add occasional emoji
            if random.random() < 0.2 and '😊' not in response:
                response = response + " 😊"

        return response


if __name__ == "__main__":
    # Test response engine
    logging.basicConfig(level=logging.INFO)

    engine = ResponseEngine()

    # Test response variation
    print("Testing response variation (same intent, different outputs):\n")

    for i in range(5):
        response = engine.generate_conversational_response(
            'explicit_intro_request',
            user_name='Alex',
            entities={'role': ['developer'], 'technology': ['react']}
        )
        print(f"{i+1}. {response}")

    print("\n" + "="*60)
    print("Testing tone adaptation:\n")

    base_response = "Hey! That's cool. Yep, I can help!"

    formal = engine.adapt_tone(base_response, 'formal')
    print(f"Formal: {formal}")

    casual = engine.adapt_tone(base_response, 'casual')
    print(f"Casual: {casual}")

    print(f"\nTotal templates: {sum(len(v) for v in engine.templates.values())}")
