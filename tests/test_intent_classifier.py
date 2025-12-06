"""
Test suite for Intent Classifier
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from intent_classifier import IntentClassifier


def test_explicit_intro_request():
    """Test explicit introduction requests"""
    classifier = IntentClassifier()

    messages = [
        "I need to meet a React developer",
        "Can you introduce me to someone who knows Python?",
        "Connect me with a designer please",
    ]

    for msg in messages:
        result = classifier.classify(msg)
        assert result.intent == 'explicit_intro_request', f"Failed for: {msg}"
        assert result.confidence > 0.8


def test_implicit_need():
    """Test implicit need detection"""
    classifier = IntentClassifier()

    messages = [
        "I'm struggling with my AWS deployment",
        "Having trouble finding a good frontend engineer",
        "Need help with machine learning models",
    ]

    for msg in messages:
        result = classifier.classify(msg)
        assert result.intent == 'implicit_need', f"Failed for: {msg}"
        assert result.confidence > 0.75


def test_entity_extraction():
    """Test entity extraction"""
    classifier = IntentClassifier()

    msg = "I need a senior React developer in San Francisco"
    result = classifier.classify(msg)

    assert 'role' in result.entities
    assert 'developer' in result.entities['role']

    assert 'technology' in result.entities
    assert 'react' in result.entities['technology']

    assert 'seniority' in result.entities
    assert 'senior' in result.entities['seniority']

    assert 'location' in result.entities
    assert any('san francisco' in loc.lower() for loc in result.entities['location'])


def test_greeting():
    """Test greeting detection"""
    classifier = IntentClassifier()

    messages = ["Hey", "Hi there", "Hello!", "Good morning"]

    for msg in messages:
        result = classifier.classify(msg)
        assert result.intent == 'greeting', f"Failed for: {msg}"


def test_acknowledgment():
    """Test acknowledgment detection"""
    classifier = IntentClassifier()

    messages = ["ok", "got it", "sure", "thanks"]

    for msg in messages:
        result = classifier.classify(msg)
        assert result.intent == 'acknowledgment', f"Failed for: {msg}"


def test_sentiment_analysis():
    """Test sentiment detection"""
    classifier = IntentClassifier()

    # Positive
    result = classifier.classify("This introduction was great!")
    assert result.sentiment in ['positive']

    # Negative
    result = classifier.classify("This was a waste of time")
    assert result.sentiment == 'negative'

    # Urgent
    result = classifier.classify("I need help urgently!")
    assert result.sentiment == 'urgent'


if __name__ == "__main__":
    print("Running intent classifier tests...")

    test_explicit_intro_request()
    print("[PASS] Explicit intro request tests passed")

    test_implicit_need()
    print("[PASS] Implicit need tests passed")

    test_entity_extraction()
    print("[PASS] Entity extraction tests passed")

    test_greeting()
    print("[PASS] Greeting tests passed")

    test_acknowledgment()
    print("[PASS] Acknowledgment tests passed")

    test_sentiment_analysis()
    print("[PASS] Sentiment analysis tests passed")

    print("\nAll tests passed!")
