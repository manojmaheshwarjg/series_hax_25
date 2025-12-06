"""
Intent Classification Engine
Analyzes user messages to determine intent and extract entities
"""

import re
import logging
from typing import Dict, List, Tuple, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class IntentResult:
    """Result of intent classification"""
    intent: str
    confidence: float
    entities: Dict[str, List[str]]
    sentiment: str  # 'positive', 'neutral', 'negative', 'urgent'
    keywords: List[str]


class IntentClassifier:
    """Rule-based intent classification with entity extraction"""

    def __init__(self):
        # Intent patterns (intent_type, patterns, confidence)
        self.patterns = {
            'explicit_intro_request': [
                (r'\b(need|looking for|want|require|seeking)\b.*\b(connect|intro|introduction|meet)\b', 0.95),
                (r'\b(know anyone|anyone who|someone who)\b', 0.90),
                (r'\b(connect me|introduce me)\b', 0.95),
            ],
            'implicit_need': [
                (r'\b(struggling with|having trouble|need help|stuck on)\b', 0.85),
                (r'\b(looking for|searching for|trying to find)\b.*\b(developer|engineer|designer|founder|investor|advisor)\b', 0.90),
                (r'\b(need|want|require)\b.*\b(developer|engineer|designer|founder|investor|advisor|expert)\b', 0.88),
            ],
            'skill_share': [
                (r'\b(I (can|could) help|I know|I\'m good at|expert in|experienced in)\b', 0.85),
                (r'\b(worked on|built|developed|created|designed)\b', 0.75),
            ],
            'feedback_positive': [
                (r'\b(great|awesome|perfect|excellent|amazing|fantastic|love|loved|helpful)\b', 0.85),
                (r'\b(thanks|thank you|appreciate)\b.*\b(intro|introduction|connection)\b', 0.90),
            ],
            'feedback_negative': [
                (r'\b(not (a )?good (fit|match)|didn\'t work out|wasn\'t helpful)\b', 0.85),
                (r'\b(waste of time|not relevant|not what I needed)\b', 0.90),
            ],
            'acknowledgment': [
                (r'^\b(ok|okay|got it|sounds good|sure|yes|yeah|yep|alright)\b', 0.90),
                (r'^\b(thanks|thank you|ty|thx)\b$', 0.95),
            ],
            'question': [
                (r'\?$', 0.80),
                (r'^\b(what|when|where|who|why|how|can|could|would|do you)\b', 0.85),
            ],
            'clarification': [
                (r'\b(what do you mean|not sure|confused|clarify|explain)\b', 0.85),
                (r'\b(can you (explain|tell me more))\b', 0.80),
            ],
            'greeting': [
                (r'^\b(hi|hey|hello|sup|yo|howdy)\b', 0.95),
                (r'^\b(good (morning|afternoon|evening))\b', 0.95),
            ],
            'farewell': [
                (r'\b(bye|goodbye|see you|later|gotta go|gtg)\b', 0.90),
            ],
        }

        # Entity extraction patterns
        self.entity_patterns = {
            'role': [
                'developer', 'engineer', 'designer', 'product manager', 'pm',
                'founder', 'ceo', 'cto', 'investor', 'advisor', 'consultant',
                'marketer', 'sales', 'recruiter', 'data scientist', 'ml engineer',
                'backend', 'frontend', 'fullstack', 'devops', 'mobile'
            ],
            'technology': [
                'python', 'javascript', 'typescript', 'react', 'vue', 'angular',
                'node', 'nodejs', 'django', 'flask', 'fastapi', 'express',
                'aws', 'gcp', 'azure', 'docker', 'kubernetes', 'k8s',
                'postgresql', 'mysql', 'mongodb', 'redis',
                'ml', 'machine learning', 'ai', 'deep learning', 'nlp',
                'tensorflow', 'pytorch', 'scikit-learn',
                'react native', 'flutter', 'ios', 'android',
                'java', 'c++', 'go', 'golang', 'rust', 'ruby', 'php'
            ],
            'seniority': [
                'senior', 'junior', 'mid-level', 'staff', 'principal',
                'lead', 'manager', 'director', 'vp', 'head of',
                'intern', 'entry-level', 'experienced'
            ],
            'location': [
                'nyc', 'new york', 'sf', 'san francisco', 'bay area',
                'boston', 'austin', 'seattle', 'la', 'los angeles',
                'chicago', 'remote', 'distributed'
            ],
            'industry': [
                'fintech', 'saas', 'b2b', 'b2c', 'e-commerce', 'ecommerce',
                'healthcare', 'health tech', 'edtech', 'education',
                'crypto', 'web3', 'blockchain', 'ai', 'ml',
                'startup', 'enterprise', 'agency'
            ],
            'goal': [
                'hiring', 'fundraising', 'investment', 'partnership',
                'advice', 'mentorship', 'consulting', 'freelance',
                'collaboration', 'co-founder'
            ]
        }

        # Sentiment keywords
        self.sentiment_keywords = {
            'positive': ['great', 'awesome', 'perfect', 'excellent', 'love', 'amazing', 'helpful'],
            'negative': ['bad', 'terrible', 'awful', 'horrible', 'waste', 'useless', 'disappointed'],
            'urgent': ['urgent', 'asap', 'quickly', 'immediately', 'now', 'emergency', 'critical']
        }

    def classify(self, text: str) -> IntentResult:
        """
        Classify intent of a message

        Args:
            text: Input message text

        Returns:
            IntentResult with intent, confidence, and extracted entities
        """
        text_lower = text.lower().strip()

        # Find matching intent
        best_intent = 'other'
        best_confidence = 0.0

        for intent_type, patterns in self.patterns.items():
            for pattern, confidence in patterns:
                if re.search(pattern, text_lower, re.IGNORECASE):
                    if confidence > best_confidence:
                        best_intent = intent_type
                        best_confidence = confidence

        # Extract entities
        entities = self._extract_entities(text_lower)

        # Determine sentiment
        sentiment = self._analyze_sentiment(text_lower)

        # Extract keywords
        keywords = self._extract_keywords(text_lower)

        result = IntentResult(
            intent=best_intent,
            confidence=best_confidence if best_confidence > 0 else 0.5,
            entities=entities,
            sentiment=sentiment,
            keywords=keywords
        )

        logger.debug(f"Classified intent: {result.intent} (confidence: {result.confidence:.2f})")

        return result

    def _extract_entities(self, text: str) -> Dict[str, List[str]]:
        """Extract entities from text"""
        entities = {}

        for entity_type, keywords in self.entity_patterns.items():
            found = []
            for keyword in keywords:
                # Use word boundaries for better matching
                pattern = r'\b' + re.escape(keyword) + r'\b'
                if re.search(pattern, text, re.IGNORECASE):
                    found.append(keyword)

            if found:
                entities[entity_type] = found

        return entities

    def _analyze_sentiment(self, text: str) -> str:
        """Analyze sentiment of text"""
        # Check for urgent signals first
        for keyword in self.sentiment_keywords['urgent']:
            if keyword in text:
                return 'urgent'

        # Count positive and negative keywords
        positive_count = sum(1 for kw in self.sentiment_keywords['positive'] if kw in text)
        negative_count = sum(1 for kw in self.sentiment_keywords['negative'] if kw in text)

        if negative_count > positive_count:
            return 'negative'
        elif positive_count > negative_count:
            return 'positive'
        else:
            return 'neutral'

    def _extract_keywords(self, text: str) -> List[str]:
        """Extract important keywords from text"""
        # Remove common stop words
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
                     'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'been',
                     'be', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
                     'could', 'should', 'may', 'might', 'can', 'i', 'you', 'he', 'she',
                     'it', 'we', 'they', 'this', 'that', 'these', 'those'}

        words = re.findall(r'\b\w+\b', text.lower())
        keywords = [w for w in words if w not in stop_words and len(w) > 2]

        return keywords[:10]  # Return top 10 keywords

    def extract_need_details(self, text: str, intent_result: IntentResult) -> Dict[str, Any]:
        """
        Extract detailed need information from a request

        Args:
            text: Original message text
            intent_result: Intent classification result

        Returns:
            Dictionary with structured need details
        """
        details = {
            'query': text,
            'intent': intent_result.intent,
            'entities': intent_result.entities,
            'requirements': []
        }

        # Extract specific requirements
        if 'role' in intent_result.entities:
            details['requirements'].append({
                'type': 'role',
                'values': intent_result.entities['role']
            })

        if 'technology' in intent_result.entities:
            details['requirements'].append({
                'type': 'technology',
                'values': intent_result.entities['technology']
            })

        if 'seniority' in intent_result.entities:
            details['requirements'].append({
                'type': 'seniority',
                'values': intent_result.entities['seniority']
            })

        if 'location' in intent_result.entities:
            details['requirements'].append({
                'type': 'location',
                'values': intent_result.entities['location']
            })

        return details


if __name__ == "__main__":
    # Test the classifier
    logging.basicConfig(level=logging.DEBUG)

    classifier = IntentClassifier()

    test_messages = [
        "Hey, I need a senior React developer for my startup",
        "Looking for someone who knows Python and machine learning",
        "I'm struggling with AWS deployment, need help",
        "Thanks for the intro, it was great!",
        "The person you introduced wasn't a good fit",
        "What do you mean by that?",
        "Hi there!",
        "I'm experienced in backend development with Django and PostgreSQL",
    ]

    for msg in test_messages:
        result = classifier.classify(msg)
        print(f"\nMessage: {msg}")
        print(f"Intent: {result.intent} (confidence: {result.confidence:.2f})")
        print(f"Entities: {result.entities}")
        print(f"Sentiment: {result.sentiment}")
