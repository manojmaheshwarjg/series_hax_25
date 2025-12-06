"""
Test Phase 2: Conversation Intelligence
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from nlp_engine import AdvancedNLPEngine
from conversation_manager import ConversationManager, ConversationState
from profile_builder import ProfileBuilder
from response_engine import ResponseEngine


def test_nlp_engine():
    """Test advanced NLP analysis"""
    print("Testing NLP Engine...")

    engine = AdvancedNLPEngine()

    msg = "I'm working on a SaaS product using React and Python, need a senior backend engineer"
    analysis = engine.analyze(msg)

    assert len(analysis.entities) > 0, "Should extract entities"
    assert analysis.sentiment_label in ['positive', 'negative', 'neutral', 'urgent']
    assert analysis.complexity >= 1 and analysis.complexity <= 5

    print(f"  Entities: {len(analysis.entities)} found")
    print(f"  Sentiment: {analysis.sentiment_label}")
    print(f"  Topics: {', '.join(analysis.topics)}")
    print("  [PASS]")


def test_conversation_manager():
    """Test multi-turn conversation management"""
    print("\nTesting Conversation Manager...")

    manager = ConversationManager()
    user = "+11234567890"

    # Initial request
    entities = {'role': ['developer'], 'technology': ['react']}
    manager.add_gathered_info(user, 'role', 'developer')
    manager.add_gathered_info(user, 'technology', ['react'])

    # Should need clarification
    assert manager.needs_clarification(user, entities), "Should need clarification"

    # Get next question
    question = manager.get_next_question(user, entities)
    assert question is not None, "Should have a question"

    print(f"  AI asks: {question}")

    # Simulate answer
    answer = manager.extract_answer_to_question(user, "senior level", {'seniority': ['senior']})
    assert answer is not None, "Should extract answer"

    for key, value in answer.items():
        manager.add_gathered_info(user, key, value)

    # Check summary
    summary = manager.get_conversation_summary(user)
    assert 'developer' in summary or 'react' in summary
    print(f"  Summary: {summary}")
    print("  [PASS]")


def test_profile_builder():
    """Test profile building from messages"""
    print("\nTesting Profile Builder...")

    builder = ProfileBuilder()

    profile = {
        'phone': '+11234567890',
        'skills': [],
        'interests': [],
        'projects': [],
    }

    # Test message
    msg = "Hey, I'm Alex and I'm working on a SaaS product with React and Python"
    entities = {'technology': ['react', 'python']}

    updates = builder.update_profile_from_message(profile, msg, entities)

    assert 'skills' in updates or len(profile['skills']) > 0, "Should add skills"
    assert profile.get('name') == 'Alex', "Should extract name"

    summary = builder.build_profile_summary(profile)
    completeness = builder.calculate_profile_completeness(profile)

    print(f"  Name: {profile.get('name')}")
    print(f"  Skills: {profile['skills']}")
    print(f"  Summary: {summary}")
    print(f"  Completeness: {completeness:.1%}")
    print("  [PASS]")


def test_response_engine():
    """Test response generation and variation"""
    print("\nTesting Response Engine...")

    engine = ResponseEngine()

    # Generate multiple responses for same intent
    responses = set()
    for i in range(5):
        response = engine.generate_conversational_response(
            'explicit_intro_request',
            user_name='Alex'
        )
        responses.add(response)

    # Should have at least 3 different responses
    assert len(responses) >= 3, f"Should generate varied responses, got {len(responses)} unique"

    print(f"  Generated {len(responses)} unique responses from 5 attempts")

    # Test tone adaptation
    msg = "Hey! That's cool. Yep, I can help!"
    formal = engine.adapt_tone(msg, 'formal')
    casual = engine.adapt_tone(msg, 'casual')

    assert formal != msg or casual != msg, "Should adapt tone"
    print(f"  Original: {msg}")
    print(f"  Formal: {formal}")
    print(f"  Casual: {casual}")
    print("  [PASS]")


def test_integration():
    """Test Phase 2 components working together"""
    print("\nTesting Phase 2 Integration...")

    nlp = AdvancedNLPEngine()
    conv_mgr = ConversationManager()
    profile_builder = ProfileBuilder(nlp)
    response_engine = ResponseEngine()

    user = "+11234567890"
    profile = {
        'phone': user,
        'skills': [],
        'interests': [],
        'communication_style': 'casual'
    }

    # Simulate conversation
    msg1 = "Hey, I need a React developer"

    # Analyze
    analysis = nlp.analyze(msg1)
    entities = {'role': ['developer'], 'technology': ['react']}

    # Update profile
    profile_builder.update_profile_from_message(profile, msg1, entities, analysis)

    # Manage conversation
    for entity_type, values in entities.items():
        for value in values:
            conv_mgr.add_gathered_info(user, entity_type, value)

    # Generate response
    if conv_mgr.needs_clarification(user, entities):
        question = conv_mgr.get_next_question(user, entities)
        response = response_engine.generate_response('clarification_request', {'question': question})
    else:
        response = response_engine.generate_conversational_response(
            'explicit_intro_request',
            user_name=profile.get('name'),
            entities=entities
        )

    # Adapt tone
    response = response_engine.adapt_tone(response, profile['communication_style'])

    assert response is not None and len(response) > 0
    print(f"  User: {msg1}")
    print(f"  AI: {response}")
    print(f"  Profile skills: {profile['skills']}")
    print("  [PASS]")


if __name__ == "__main__":
    print("="*60)
    print("Phase 2: Conversation Intelligence Tests")
    print("="*60)

    test_nlp_engine()
    test_conversation_manager()
    test_profile_builder()
    test_response_engine()
    test_integration()

    print("\n" + "="*60)
    print("All Phase 2 tests passed!")
    print("="*60)
