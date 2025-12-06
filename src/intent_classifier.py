"""
Intent Classification Engine
Analyzes user messages to determine intent and extract entities using Groq AI
"""

import os
import json
import logging
from typing import Dict, List, Any
from dataclasses import dataclass
from groq import Groq
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

@dataclass
class IntentResult:
    """Result of intent classification"""
    intent: str
    confidence: float
    entities: Dict[str, List[str]]
    sentiment: str  # 'positive', 'neutral', 'negative', 'urgent'
    keywords: List[str]


class IntentClassifier:
    """Groq-powered intent classification with entity extraction"""

    def __init__(self):
        api_key = os.environ.get("GROQ_API_KEY")
        if not api_key:
            logger.warning("GROQ_API_KEY not found in environment variables. Classifier will fail.")
        
        self.client = Groq(api_key=api_key)
        self.model = "llama-3.3-70b-versatile"

    def classify(self, text: str, conversation_history: List[Dict[str, str]] = None) -> IntentResult:
        """
        Classify intent of a message using Groq with conversation context

        Args:
            text: Current message text
            conversation_history: List of recent messages [{"role": "user"/"assistant", "content": "..."}]
        """
        if not text or not text.strip():
             return IntentResult(
                intent='other',
                confidence=0.0,
                entities={},
                sentiment='neutral',
                keywords=[]
            )

        try:
            # Context-aware prompt
            system_prompt = """
            You are an intent classification system for a networking chatbot.
            Identify the user's intent and extract entities (role, technology, location, etc.).

            IMPORTANT: Consider the conversation history when classifying intent.
            - If the bot just suggested a match, and user says "yes"/"sure"/"connect me"/"please" -> intent is "acknowledgment"
            - If user is confirming an introduction request -> intent is "acknowledgment"

            INTENTS:
            - explicit_intro_request: User explicitly asks for an introduction
            - implicit_need: User mentions a problem/need without explicitly asking
            - skill_share: User shares their skills or expertise
            - feedback_positive: User gives positive feedback
            - feedback_negative: User gives negative feedback
            - greeting: Initial greeting or hello
            - question_system_capabilities: Asking what the bot can do
            - question_status: Asking about status of intro/request
            - clarification: User asking for clarification
            - schedule_meeting: Scheduling related
            - update_profile: Updating their info
            - farewell: Goodbye messages
            - acknowledgment: Confirming, agreeing, saying yes/ok/sure (ESPECIALLY after match suggestions)
            - other: Anything else

            ENTITY EXTRACTION RULES:
            - "devs", "developers", "coding guys" -> role: ["Software Engineer"]
            - "frontend guys", "FE devs" -> role: ["Frontend Engineer"]
            - "content folks", "creators", "youtubers" -> role: ["Content Creator"]
            - "tech" -> technology (e.g. "React", "Python") or industry if generic.
            - "video guy" -> role: ["Videographer", "Video Editor"]

            Return JSON object only.

            Example:
            Input: "I need a senior React dev in NYC"
            Output: {
                "intent": "explicit_intro_request",
                "confidence": 0.99,
                "entities": {
                    "role": ["Software Engineer"],
                    "technology": ["React"],
                    "location": ["NYC"]
                },
                "sentiment": "neutral"
            }

            Example with context:
            Bot: "I found James Williams, a React developer. Want me to introduce you?"
            User: "Yes please"
            Output: {
                "intent": "acknowledgment",
                "confidence": 0.95,
                "entities": {},
                "sentiment": "positive"
            }
            """

            # Build messages with conversation history
            messages = [{"role": "system", "content": system_prompt}]

            # Add conversation history if provided (last 3 messages for context)
            if conversation_history:
                recent_history = conversation_history[-3:] if len(conversation_history) > 3 else conversation_history
                messages.extend(recent_history)

            # Add current user message
            messages.append({"role": "user", "content": text})

            chat_completion = self.client.chat.completions.create(
                messages=messages,
                model=self.model,
                temperature=0.0,
                response_format={"type": "json_object"}
            )

            response_content = chat_completion.choices[0].message.content
            data = json.loads(response_content)
            
            # Normalize entities dict
            entities = data.get("entities", {})
            # Ensure values are lists
            for k, v in entities.items():
                if not isinstance(v, list):
                    entities[k] = [v] if v else []

            return IntentResult(
                intent=data.get("intent", "other"),
                confidence=data.get("confidence", 0.5),
                entities=entities,
                sentiment=data.get("sentiment", "neutral"),
                keywords=data.get("keywords", [])
            )

        except Exception as e:
            logger.error(f"Error calling Groq API: {e}")
            return IntentResult(
                intent='other',
                confidence=0.0,
                entities={},
                sentiment='neutral',
                keywords=[]
            )

    def extract_need_details(self, text: str, intent_result: IntentResult) -> Dict[str, Any]:
        """
        Extract detailed need information from a request
        """
        details = {
            'query': text,
            'intent': intent_result.intent,
            'entities': intent_result.entities,
            'requirements': []
        }

        # Structure the requirements list from the flat entities dict
        for key in ['role', 'technology', 'seniority', 'location']:
            if key in intent_result.entities and intent_result.entities[key]:
                 details['requirements'].append({
                    'type': key,
                    'values': intent_result.entities[key]
                })

        return details

if __name__ == "__main__":
    # Test the classifier
    logging.basicConfig(level=logging.INFO)
    
    # Silence third-party loggers
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("http").setLevel(logging.WARNING)
    logging.getLogger("groq").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    
    # Check for API Key
    if not os.environ.get("GROQ_API_KEY"):
         print("ERROR: GROQ_API_KEY not set. Please set it in your environment or .env file.")
         exit(1)

    classifier = IntentClassifier()

    test_messages = [
        "Hey, I need a senior React developer for my startup",
        "I'm drowning in AWS configs and need someone to save me", # Implicit need
        "Just launched my MVP!",
        "The person you introduced wasn't a good fit",
    ]

    print("Testing Groq Intent Classifier...")
    for msg in test_messages:
        print(f"\nMessage: {msg}")
        result = classifier.classify(msg)
        print(f"Intent: {result.intent} ({result.confidence})")
        print(f"Entities: {result.entities}")
        print(f"Sentiment: {result.sentiment}")
