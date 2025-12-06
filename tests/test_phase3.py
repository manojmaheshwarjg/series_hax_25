"""
Test Phase 3: Human-Like Interaction
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from human_behavior import HumanBehaviorSimulator, MessageEditSimulator
from platform_adapter import PlatformDetector, PlatformAdapter, Platform


def test_typing_delays():
    """Test realistic typing delay calculation"""
    print("Testing Typing Delays...")

    simulator = HumanBehaviorSimulator()

    test_cases = [
        ("ok", 1, 0.5, 3.5),  # message, complexity, min_expected, max_expected
        ("Let me search my network...", 3, 2.0, 10.0),
        ("I found someone perfect! Sarah Chen is a senior React developer.", 4, 3.0, 15.0),
    ]

    for msg, complexity, min_exp, max_exp in test_cases:
        delay = simulator.calculate_typing_delay(msg, complexity)

        assert min_exp <= delay <= max_exp, \
            f"Delay {delay:.2f}s outside expected range [{min_exp}, {max_exp}] for: '{msg}'"

        print(f"  '{msg[:30]}...' (complexity {complexity}): {delay:.2f}s")

    print("  [PASS]")


def test_message_editing():
    """Test message editing simulation"""
    print("\nTesting Message Editing...")

    simulator = HumanBehaviorSimulator()

    # Test should_edit probability
    edit_count = sum(1 for _ in range(100) if simulator.should_edit_message())
    expected_edits = 12  # 12% probability
    tolerance = 8  # Allow more tolerance for randomness

    assert abs(edit_count - expected_edits) < tolerance, \
        f"Edit probability off: got {edit_count}%, expected ~{expected_edits}%"

    print(f"  Edit probability: {edit_count}% (expected ~12%)")

    # Test edit delay
    delay = simulator.generate_edit_delay()
    assert 2.0 <= delay <= 5.0, f"Edit delay {delay}s outside range [2, 5]"

    print(f"  Edit delay: {delay:.2f}s")

    # Test edit types
    original = "I think I can help with that"
    edited, edit_type = simulator.create_message_edit(original)

    assert edit_type in ['typo_fix', 'rephrase', 'add_detail', 'tone_adjustment']
    print(f"  Edit type: {edit_type}")
    print(f"    Original: '{original}'")
    print(f"    Edited:   '{edited}'")

    print("  [PASS]")


def test_platform_detection():
    """Test platform detection"""
    print("\nTesting Platform Detection...")

    detector = PlatformDetector()

    # Test iMessage detection
    imessage_data = {
        'from': 'user@example.com',
        'metadata': {'platform': 'imessage'},
        'supports_reactions': True
    }

    platform = detector.detect_platform(imessage_data)
    assert platform == Platform.IMESSAGE, "Should detect iMessage"

    print(f"  Detected iMessage: {platform.value}")

    # Test SMS detection
    sms_data = {
        'from': '+12223334444',
        'metadata': {},
        'supports_reactions': False
    }

    platform = detector.detect_platform(sms_data)
    assert platform == Platform.SMS, "Should detect SMS"

    print(f"  Detected SMS: {platform.value}")

    # Test caching
    detector.set_platform_for_user('+11111111111', Platform.IMESSAGE)
    cached = detector.get_platform_for_user('+11111111111')

    assert cached == Platform.IMESSAGE, "Should cache platform"
    print(f"  Platform caching works")

    print("  [PASS]")


def test_platform_adapter():
    """Test platform-specific adaptations"""
    print("\nTesting Platform Adapter...")

    detector = PlatformDetector()
    adapter = PlatformAdapter(detector)

    # Setup users
    imessage_user = '+11111111111'
    sms_user = '+12222222222'

    detector.set_platform_for_user(imessage_user, Platform.IMESSAGE)
    detector.set_platform_for_user(sms_user, Platform.SMS)

    # Test confirmation prompts
    imessage_prompt = adapter.format_confirmation_prompt(imessage_user, "Want an intro?")
    sms_prompt = adapter.format_confirmation_prompt(sms_user, "Want an intro?")

    assert 'heart' in imessage_prompt.lower() or '❤' in imessage_prompt or 'to confirm' in imessage_prompt, "iMessage should use reactions"
    assert ('1' in sms_prompt and '2' in sms_prompt), "SMS should use numbered options"

    print(f"  iMessage prompt uses reactions: {('❤' in imessage_prompt or 'heart' in imessage_prompt.lower())}")
    print(f"  SMS prompt uses numbers: {'1' in sms_prompt and '2' in sms_prompt}")

    # Test response parsing
    yes_response = adapter.parse_user_response(sms_user, "1", 'confirmation')
    no_response = adapter.parse_user_response(sms_user, "no thanks", 'confirmation')

    assert yes_response == True, "Should parse '1' as yes"
    assert no_response == False, "Should parse 'no thanks' as no"

    print(f"  Parsed '1': {yes_response}")
    print(f"  Parsed 'no thanks': {no_response}")

    # Test reaction handling
    heart_result = adapter.handle_reaction(imessage_user, 'love', 'confirmation')
    thumbs_down_result = adapter.handle_reaction(imessage_user, 'thumbs_down', 'confirmation')

    assert heart_result == True, "Should interpret love as yes"
    assert thumbs_down_result == False, "Should interpret thumbs_down as no"

    print(f"  Love reaction: {heart_result}")
    print(f"  Thumbs down reaction: {thumbs_down_result}")

    # Test message splitting
    long_msg = "This is a test message. " * 20
    parts = adapter.split_long_message(sms_user, long_msg)

    if len(parts) > 1:
        print(f"  Split long message into {len(parts)} parts")
        assert all('(1/' in parts[0] or '1/' in parts[0] for _ in [1]), "Should add part indicators"
    else:
        print(f"  Message fits in one part")

    # Test typing indicator check
    can_use_typing_imessage = adapter.should_use_typing_indicator(imessage_user)
    can_use_typing_sms = adapter.should_use_typing_indicator(sms_user)

    assert can_use_typing_imessage == True, "iMessage should support typing"
    assert can_use_typing_sms == False, "SMS should not support typing"

    print(f"  iMessage typing indicator: {can_use_typing_imessage}")
    print(f"  SMS typing indicator: {can_use_typing_sms}")

    print("  [PASS]")


def test_human_behavior_integration():
    """Test integrated human behavior"""
    print("\nTesting Human Behavior Integration...")

    simulator = HumanBehaviorSimulator()

    # Test typing variance
    message = "Got it! Let me search..."
    delays = [simulator.calculate_typing_delay(message, 2) for _ in range(10)]

    # Should have variance
    assert len(set(delays)) > 1, "Should have variance in typing delays"
    avg_delay = sum(delays) / len(delays)

    print(f"  10 typing delays for same message: {min(delays):.2f}s - {max(delays):.2f}s (avg: {avg_delay:.2f}s)")

    # Test natural variance
    base = 5.0
    varied = [simulator.add_natural_variance(base, 0.2) for _ in range(10)]

    assert all(4.0 <= v <= 6.0 for v in varied), "Variance should be within ±20%"
    print(f"  Natural variance (±20% of 5.0s): {min(varied):.2f}s - {max(varied):.2f}s")

    # Test read time calculation
    short_msg = "ok"
    long_msg = "This is a much longer message that takes more time to read and comprehend properly."

    short_read = simulator.calculate_read_time(len(short_msg))
    long_read = simulator.calculate_read_time(len(long_msg))

    assert long_read > short_read, "Longer messages should take longer to read"
    print(f"  Read time - Short: {short_read:.2f}s, Long: {long_read:.2f}s")

    print("  [PASS]")


if __name__ == "__main__":
    print("="*60)
    print("Phase 3: Human-Like Interaction Tests")
    print("="*60)

    test_typing_delays()
    test_message_editing()
    test_platform_detection()
    test_platform_adapter()
    test_human_behavior_integration()

    print("\n" + "="*60)
    print("All Phase 3 tests passed!")
    print("="*60)
