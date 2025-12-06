"""
Advanced NLP Engine
Uses spaCy for named entity recognition, dependency parsing, and text analysis
"""

import logging
import re
from typing import Dict, List, Tuple, Any, Optional
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)

# Try to import spaCy, fall back to basic NLP if not available
try:
    import spacy
    from spacy.matcher import Matcher
    SPACY_AVAILABLE = True
    logger.info("spaCy is available")
except ImportError:
    SPACY_AVAILABLE = False
    logger.warning("spaCy not available, using basic NLP")

try:
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
    VADER_AVAILABLE = True
except ImportError:
    VADER_AVAILABLE = False
    logger.warning("VADER sentiment not available")


@dataclass
class EntityExtraction:
    """Extracted entity with context"""
    text: str
    type: str
    confidence: float
    context: Optional[str] = None


@dataclass
class NLPAnalysis:
    """Complete NLP analysis of text"""
    entities: List[EntityExtraction]
    sentiment_score: float  # -1 to 1
    sentiment_label: str  # positive, negative, neutral, urgent
    key_phrases: List[str]
    topics: List[str]
    complexity: int  # 1-5


class AdvancedNLPEngine:
    """Advanced NLP processing using spaCy and VADER"""

    def __init__(self):
        global SPACY_AVAILABLE, VADER_AVAILABLE

        self.nlp = None
        self.matcher = None
        self.sentiment_analyzer = None

        # Initialize spaCy if available
        if SPACY_AVAILABLE:
            try:
                self.nlp = spacy.load('en_core_web_sm')
                logger.info("Loaded spaCy model: en_core_web_sm")

                # Create matcher for custom patterns
                self.matcher = Matcher(self.nlp.vocab)
                self._add_custom_patterns()

            except OSError:
                logger.warning("spaCy model not found. Run: python -m spacy download en_core_web_sm")
                SPACY_AVAILABLE = False

        # Initialize VADER sentiment
        if VADER_AVAILABLE:
            self.sentiment_analyzer = SentimentIntensityAnalyzer()

        # Custom entity patterns
        self.skill_patterns = {
            'programming_languages': [
                'python', 'javascript', 'typescript', 'java', 'c++', 'c#', 'go',
                'golang', 'rust', 'ruby', 'php', 'swift', 'kotlin', 'scala',
                'r', 'matlab', 'sql', 'nosql'
            ],
            'frameworks': [
                'react', 'vue', 'angular', 'svelte', 'next.js', 'nuxt',
                'django', 'flask', 'fastapi', 'express', 'nest.js',
                'spring', 'rails', 'laravel', '.net',
                'tensorflow', 'pytorch', 'keras', 'scikit-learn'
            ],
            'cloud_platforms': [
                'aws', 'azure', 'gcp', 'google cloud', 'heroku', 'vercel',
                'netlify', 'digital ocean', 'cloudflare'
            ],
            'databases': [
                'postgresql', 'mysql', 'mongodb', 'redis', 'cassandra',
                'dynamodb', 'elasticsearch', 'neo4j', 'sqlite'
            ],
            'tools': [
                'docker', 'kubernetes', 'k8s', 'jenkins', 'gitlab', 'github',
                'terraform', 'ansible', 'webpack', 'vite', 'git'
            ]
        }

        # Experience indicators
        self.experience_patterns = {
            'senior': ['senior', 'lead', 'staff', 'principal', 'architect'],
            'mid': ['mid-level', 'intermediate', '3-5 years', '5+ years'],
            'junior': ['junior', 'entry-level', 'new grad', 'recent grad', 'intern']
        }

    def _add_custom_patterns(self):
        """Add custom matching patterns to spaCy matcher"""
        if not self.matcher:
            return

        # Pattern for "I need/want X"
        need_pattern = [
            {"LOWER": {"IN": ["need", "want", "require", "looking"]}},
            {"OP": "*"},  # Any tokens
            {"POS": "NOUN"}
        ]
        self.matcher.add("NEED_PATTERN", [need_pattern])

        # Pattern for "I have experience with X"
        experience_pattern = [
            {"LOWER": {"IN": ["have", "got", "possess"]}},
            {"LOWER": {"IN": ["experience", "expertise", "knowledge"]}},
            {"LOWER": {"IN": ["with", "in"]}},
            {"POS": "NOUN"}
        ]
        self.matcher.add("EXPERIENCE_PATTERN", [experience_pattern])

    def analyze(self, text: str) -> NLPAnalysis:
        """
        Perform complete NLP analysis on text

        Args:
            text: Input text to analyze

        Returns:
            NLPAnalysis with entities, sentiment, and other features
        """
        # Extract entities
        entities = self._extract_entities(text)

        # Analyze sentiment
        sentiment_score, sentiment_label = self._analyze_sentiment(text)

        # Extract key phrases
        key_phrases = self._extract_key_phrases(text)

        # Identify topics
        topics = self._identify_topics(text, entities)

        # Estimate complexity
        complexity = self._estimate_complexity(text)

        return NLPAnalysis(
            entities=entities,
            sentiment_score=sentiment_score,
            sentiment_label=sentiment_label,
            key_phrases=key_phrases,
            topics=topics,
            complexity=complexity
        )

    def _extract_entities(self, text: str) -> List[EntityExtraction]:
        """Extract entities using spaCy and custom patterns"""
        entities = []

        if self.nlp:
            doc = self.nlp(text)

            # spaCy named entities
            for ent in doc.ents:
                entities.append(EntityExtraction(
                    text=ent.text,
                    type=ent.label_,
                    confidence=0.9,
                    context=text[max(0, ent.start_char - 20):min(len(text), ent.end_char + 20)]
                ))

        # Custom skill extraction
        text_lower = text.lower()

        for skill_type, skills in self.skill_patterns.items():
            for skill in skills:
                if re.search(r'\b' + re.escape(skill) + r'\b', text_lower):
                    entities.append(EntityExtraction(
                        text=skill,
                        type='SKILL',
                        confidence=0.95,
                        context=skill_type
                    ))

        # Experience level extraction
        for level, patterns in self.experience_patterns.items():
            for pattern in patterns:
                if re.search(r'\b' + re.escape(pattern) + r'\b', text_lower):
                    entities.append(EntityExtraction(
                        text=pattern,
                        type='EXPERIENCE_LEVEL',
                        confidence=0.9,
                        context=level
                    ))

        return entities

    def _analyze_sentiment(self, text: str) -> Tuple[float, str]:
        """
        Analyze sentiment using VADER

        Returns:
            Tuple of (score from -1 to 1, label)
        """
        if self.sentiment_analyzer:
            scores = self.sentiment_analyzer.polarity_scores(text)
            compound = scores['compound']

            # Check for urgency
            urgent_keywords = ['urgent', 'asap', 'immediately', 'now', 'emergency', 'critical']
            if any(kw in text.lower() for kw in urgent_keywords):
                return compound, 'urgent'

            # Classify sentiment
            if compound >= 0.05:
                label = 'positive'
            elif compound <= -0.05:
                label = 'negative'
            else:
                label = 'neutral'

            return compound, label

        else:
            # Fallback sentiment analysis
            positive_words = ['great', 'awesome', 'excellent', 'perfect', 'love', 'happy']
            negative_words = ['bad', 'terrible', 'awful', 'hate', 'disappointed']

            text_lower = text.lower()
            pos_count = sum(1 for word in positive_words if word in text_lower)
            neg_count = sum(1 for word in negative_words if word in text_lower)

            if neg_count > pos_count:
                return -0.5, 'negative'
            elif pos_count > neg_count:
                return 0.5, 'positive'
            else:
                return 0.0, 'neutral'

    def _extract_key_phrases(self, text: str) -> List[str]:
        """Extract key phrases using spaCy"""
        key_phrases = []

        if self.nlp:
            doc = self.nlp(text)

            # Extract noun chunks
            for chunk in doc.noun_chunks:
                if len(chunk.text.split()) > 1:  # Multi-word phrases
                    key_phrases.append(chunk.text)

            # Extract verb phrases
            for token in doc:
                if token.pos_ == 'VERB':
                    # Get verb with its object
                    phrase_parts = [token.text]
                    for child in token.children:
                        if child.dep_ in ['dobj', 'pobj', 'attr']:
                            phrase_parts.append(child.text)
                    if len(phrase_parts) > 1:
                        key_phrases.append(' '.join(phrase_parts))

        return key_phrases[:5]  # Top 5 phrases

    def _identify_topics(self, text: str, entities: List[EntityExtraction]) -> List[str]:
        """Identify main topics from text and entities"""
        topics = set()

        # Topics from entities
        for entity in entities:
            if entity.type == 'SKILL':
                topics.add('technical_skills')
            elif entity.type == 'ORG':
                topics.add('companies')
            elif entity.type == 'GPE':
                topics.add('locations')
            elif entity.type == 'EXPERIENCE_LEVEL':
                topics.add('experience')

        # Topics from keywords
        text_lower = text.lower()

        topic_keywords = {
            'hiring': ['hiring', 'recruit', 'looking for', 'need someone'],
            'fundraising': ['fundraising', 'investment', 'investors', 'capital', 'funding'],
            'technical': ['code', 'develop', 'build', 'engineer', 'technical'],
            'business': ['business', 'strategy', 'growth', 'marketing', 'sales'],
            'collaboration': ['collaborate', 'partnership', 'work together', 'team up'],
            'advice': ['advice', 'help', 'guidance', 'mentor', 'learn']
        }

        for topic, keywords in topic_keywords.items():
            if any(kw in text_lower for kw in keywords):
                topics.add(topic)

        return list(topics)

    def _estimate_complexity(self, text: str) -> int:
        """
        Estimate text complexity (1-5)

        Factors:
        - Sentence length
        - Word length
        - Question marks
        - Technical terms
        """
        sentences = text.split('.')
        words = text.split()

        avg_sentence_length = len(words) / max(len(sentences), 1)
        avg_word_length = sum(len(w) for w in words) / max(len(words), 1)

        has_question = '?' in text
        has_technical = any(term in text.lower() for term in ['api', 'database', 'framework', 'architecture'])

        complexity = 1

        if avg_sentence_length > 15:
            complexity += 1
        if avg_word_length > 6:
            complexity += 1
        if has_question:
            complexity += 1
        if has_technical:
            complexity += 1

        return min(complexity, 5)

    def extract_profile_updates(self, text: str) -> Dict[str, Any]:
        """
        Extract profile update information from text

        Args:
            text: User message

        Returns:
            Dictionary with profile fields to update
        """
        updates = {}
        entities = self._extract_entities(text)

        # Extract skills
        skills = [e.text for e in entities if e.type == 'SKILL']
        if skills:
            updates['skills'] = skills

        # Extract location
        locations = [e.text for e in entities if e.type == 'GPE']
        if locations:
            updates['location'] = locations[0]

        # Extract companies/organizations
        orgs = [e.text for e in entities if e.type == 'ORG']
        if orgs:
            updates['companies'] = orgs

        # Extract person names (potential network)
        people = [e.text for e in entities if e.type == 'PERSON']
        if people:
            updates['mentioned_people'] = people

        # Extract what they're working on
        if self.nlp:
            doc = self.nlp(text)
            project_patterns = [
                'working on', 'building', 'developing', 'creating', 'making'
            ]

            for pattern in project_patterns:
                if pattern in text.lower():
                    # Find what comes after the pattern
                    pattern_idx = text.lower().find(pattern)
                    after_pattern = text[pattern_idx + len(pattern):].strip()
                    if after_pattern:
                        # Get first sentence
                        project = after_pattern.split('.')[0].strip()
                        if project:
                            updates['current_project'] = project

        return updates


if __name__ == "__main__":
    # Test the NLP engine
    logging.basicConfig(level=logging.INFO)

    engine = AdvancedNLPEngine()

    test_messages = [
        "I'm working on a SaaS product using React and Python, need a senior backend engineer",
        "Looking for investors in the AI space, based in San Francisco",
        "Just built an amazing feature with TensorFlow and Docker!",
        "This introduction was terrible, complete waste of time",
    ]

    for msg in test_messages:
        print(f"\n{'='*60}")
        print(f"Text: {msg}")
        print(f"{'='*60}")

        analysis = engine.analyze(msg)

        print(f"\nEntities:")
        for entity in analysis.entities:
            print(f"  - {entity.text} ({entity.type}) [confidence: {entity.confidence:.2f}]")

        print(f"\nSentiment: {analysis.sentiment_label} (score: {analysis.sentiment_score:.2f})")
        print(f"Topics: {', '.join(analysis.topics)}")
        print(f"Key Phrases: {', '.join(analysis.key_phrases)}")
        print(f"Complexity: {analysis.complexity}/5")

        profile_updates = engine.extract_profile_updates(msg)
        if profile_updates:
            print(f"\nProfile Updates: {profile_updates}")
