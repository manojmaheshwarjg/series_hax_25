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

    def classify(self, text: str) -> IntentResult:
        """
        Classify intent of a message using Groq
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
            # Simple, effective prompt that works reliably with Llama 3
            system_prompt = """
            You are an intent classification system.
            Identify the user's intent and extract entities (role, technology, location, etc.).
            
            INTENTS:
            - explicit_intro_request
            - implicit_need
            - skill_share
            - feedback_positive
            - feedback_negative
            - greeting
            - question_system_capabilities
            - question_status
            - clarification
            - schedule_meeting
            - update_profile
            - farewell
            - acknowledgment
            - other

            Return JSON object only.

            Example:
            Input: "I need a senior React dev in NYC"
            Output: {
                "intent": "explicit_intro_request",
                "confidence": 0.99,
                "entities": {
                    "role": ["dev"],
                    "technology": ["React"],
                    "location": ["NYC"]
                },
                "sentiment": "neutral"
            }
            """

            chat_completion = self.client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": system_prompt
                    },
                    {
                        "role": "user",
                        "content": text
                    }
                ],
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
