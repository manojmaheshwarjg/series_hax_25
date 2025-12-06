"""
Human Behavior Simulation
Makes the AI feel more human through realistic timing and patterns
"""

import random
import time
import logging
from typing import Optional, Dict, Any, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)


class HumanBehaviorSimulator:
    """Simulates human-like messaging behaviors"""

    def __init__(self):
        # Typing speed ranges (words per minute)
        self.wpm_min = 40
        self.wpm_max = 80

        # Message editing probability
        self.edit_probability = 0.12  # 12% of messages get edited

        # Thinking time multipliers based on complexity
        self.thinking_time_multipliers = {
            1: (0.5, 1.5),    # Simple acknowledgments
            2: (1.0, 2.5),    # Normal responses
            3: (2.0, 4.0),    # Complex requests
            4: (3.0, 5.0),    # Very complex
            5: (4.0, 6.0),    # Deep thinking required
        }

    def calculate_typing_delay(self, text: str, complexity: int = 2,
                               user_is_fast_typer: bool = False) -> float:
        """
        Calculate realistic typing delay

        Args:
            text: The message to be sent
            complexity: Message complexity (1-5)
            user_is_fast_typer: If True, uses faster WPM

        Returns:
            Total delay in seconds
        """
        words = len(text.split())

        # Adjust WPM based on user typing speed
        if user_is_fast_typer:
            wpm = random.uniform(self.wpm_max - 10, self.wpm_max + 10)
        else:
            wpm = random.uniform(self.wpm_min, self.wpm_max)

        # Base typing time
        typing_time = (words / wpm) * 60

        # Thinking time based on complexity
        complexity = max(1, min(5, complexity))
        min_think, max_think = self.thinking_time_multipliers[complexity]
        thinking_time = random.uniform(min_think, max_think)

        # Pause time for punctuation (natural reading pauses)
        punctuation_count = text.count('.') + text.count('?') + text.count('!')
        pause_time = punctuation_count * random.uniform(0.3, 0.8)

        # Add occasional longer pause (distraction/interruption)
        if random.random() < 0.1:  # 10% chance
            distraction_time = random.uniform(1.0, 3.0)
        else:
            distraction_time = 0

        total_delay = typing_time + thinking_time + pause_time + distraction_time

        # Cap at reasonable maximum (15 seconds)
        total_delay = min(total_delay, 15.0)

        # Minimum delay (0.5 seconds)
        total_delay = max(total_delay, 0.5)

        logger.debug(f"Typing delay: {total_delay:.2f}s (typing: {typing_time:.2f}s, "
                    f"thinking: {thinking_time:.2f}s, pauses: {pause_time:.2f}s)")

        return total_delay

    def calculate_typing_indicator_duration(self, text: str, complexity: int = 2) -> int:
        """
        Calculate how long to show typing indicator (in milliseconds)

        Args:
            text: The message to be sent
            complexity: Message complexity

        Returns:
            Duration in milliseconds
        """
        delay_seconds = self.calculate_typing_delay(text, complexity)

        # Show typing for 70-90% of the total delay
        # (the rest is "thinking" before starting to type)
        typing_percentage = random.uniform(0.70, 0.90)
        typing_duration = delay_seconds * typing_percentage

        return int(typing_duration * 1000)

    def should_edit_message(self) -> bool:
        """
        Decide if message should be edited after sending

        Returns:
            True if message should be edited
        """
        return random.random() < self.edit_probability

    def generate_edit_delay(self) -> float:
        """
        Generate delay before editing a message (2-5 seconds)

        Returns:
            Delay in seconds
        """
        return random.uniform(2.0, 5.0)

    def create_message_edit(self, original: str) -> Tuple[str, str]:
        """
        Create a realistic edit of a message

        Args:
            original: Original message

        Returns:
            Tuple of (edited_message, edit_type)
        """
        edit_types = [
            'typo_fix',
            'rephrase',
            'add_detail',
            'tone_adjustment',
        ]

        edit_type = random.choice(edit_types)

        if edit_type == 'typo_fix':
            # Simulate fixing a typo
            edited = self._fix_typo(original)

        elif edit_type == 'rephrase':
            # Rephrase slightly
            edited = self._rephrase(original)

        elif edit_type == 'add_detail':
            # Add a bit more info
            edited = self._add_detail(original)

        elif edit_type == 'tone_adjustment':
            # Adjust tone
            edited = self._adjust_tone(original)

        else:
            edited = original

        return edited, edit_type

    def _fix_typo(self, text: str) -> str:
        """Simulate fixing a typo"""
        # Common typo patterns
        typos = {
            'the': 'teh',
            'and': 'adn',
            'you': 'yuo',
            'for': 'fro',
            'can': 'cna',
            'with': 'wiht',
        }

        # Reverse: fix the typo
        for correct, typo in typos.items():
            if typo in text.lower():
                return text.replace(typo, correct)

        # If no typo to fix, return original
        return text

    def _rephrase(self, text: str) -> str:
        """Slightly rephrase the message"""
        rephrases = [
            ("I think", "I believe"),
            ("probably", "likely"),
            ("a bit", "a little"),
            ("really", "very"),
            ("might", "could"),
        ]

        for old, new in rephrases:
            if old in text.lower():
                return text.replace(old, new)

        return text

    def _add_detail(self, text: str) -> str:
        """Add a small detail"""
        additions = [
            " btw",
            " actually",
            " I think",
            " probably",
        ]

        if random.random() < 0.5 and len(text) < 100:
            return text + random.choice(additions)

        return text

    def _adjust_tone(self, text: str) -> str:
        """Adjust tone (more/less formal)"""
        if random.random() < 0.5:
            # Make more casual
            text = text.replace("!", "")
            text = text.replace("Hello", "Hey")
        else:
            # Make more formal
            text = text.replace("Hey", "Hello")

        return text

    def calculate_read_time(self, message_length: int) -> float:
        """
        Estimate how long it takes to read a message

        Args:
            message_length: Number of characters

        Returns:
            Read time in seconds
        """
        # Average reading speed: 200-250 words per minute
        # Average word length: 5 characters
        words = message_length / 5
        read_wpm = random.uniform(200, 250)
        read_time = (words / read_wpm) * 60

        # Add comprehension time
        comprehension_time = random.uniform(0.5, 1.5)

        total = read_time + comprehension_time

        # Minimum 0.5 seconds, maximum 10 seconds
        return max(0.5, min(total, 10.0))

    def add_natural_variance(self, base_delay: float, variance: float = 0.2) -> float:
        """
        Add natural variance to a delay

        Args:
            base_delay: Base delay time
            variance: Variance percentage (0.2 = ±20%)

        Returns:
            Adjusted delay
        """
        multiplier = random.uniform(1 - variance, 1 + variance)
        return base_delay * multiplier

    def simulate_conversation_gap(self, last_message_time: datetime) -> float:
        """
        Calculate appropriate delay based on time since last message

        Args:
            last_message_time: When the last message was sent

        Returns:
            Additional delay in seconds
        """
        time_since_last = (datetime.utcnow() - last_message_time).total_seconds()

        # If been a while, add a "just saw this" delay
        if time_since_last > 300:  # 5 minutes
            return random.uniform(2.0, 5.0)
        elif time_since_last > 60:  # 1 minute
            return random.uniform(1.0, 3.0)
        else:
            return 0.0


class MessageEditSimulator:
    """Handles message editing simulation"""

    def __init__(self, api_client, behavior_simulator: HumanBehaviorSimulator):
        self.api_client = api_client
        self.behavior_simulator = behavior_simulator
        self.pending_edits = []

    def schedule_edit(self, message_id: str, original_text: str, chat_id: str, recipient: str):
        """
        Schedule a message edit

        Args:
            message_id: ID of the sent message
            original_text: Original message text
            chat_id: Chat ID
            recipient: Recipient phone number
        """
        if not self.behavior_simulator.should_edit_message():
            return

        edit_delay = self.behavior_simulator.generate_edit_delay()
        edited_text, edit_type = self.behavior_simulator.create_message_edit(original_text)

        # Only edit if the text actually changed
        if edited_text != original_text:
            self.pending_edits.append({
                'message_id': message_id,
                'original': original_text,
                'edited': edited_text,
                'edit_type': edit_type,
                'execute_at': time.time() + edit_delay,
                'chat_id': chat_id,
                'recipient': recipient
            })

            logger.info(f"Scheduled edit in {edit_delay:.1f}s: '{original_text}' → '{edited_text}'")

    def process_pending_edits(self):
        """Process any pending edits that are ready"""
        now = time.time()
        edits_to_process = [e for e in self.pending_edits if e['execute_at'] <= now]

        for edit in edits_to_process:
            try:
                # Note: Series API may not support editing
                # This is a placeholder for when it does
                logger.info(f"Executing edit ({edit['edit_type']}): "
                          f"'{edit['original']}' → '{edit['edited']}'")

                # If API supports editing:
                # self.api_client.edit_message(edit['message_id'], edit['edited'])

                # Otherwise, send a correction message:
                correction = f"*{edit['edited']}"  # Markdown style correction
                # self.api_client.send_message(edit['recipient'], correction, edit['chat_id'])

                self.pending_edits.remove(edit)

            except Exception as e:
                logger.error(f"Error processing edit: {e}")
                self.pending_edits.remove(edit)


if __name__ == "__main__":
    # Test human behavior simulation
    logging.basicConfig(level=logging.DEBUG)

    simulator = HumanBehaviorSimulator()

    test_messages = [
        ("ok", 1),
        ("Let me search my network for someone who fits...", 3),
        ("Hey! I found someone perfect - Sarah Chen. She's a senior React developer at Stripe with 8 years of experience.", 4),
    ]

    print("Testing typing delay simulation:\n")

    for msg, complexity in test_messages:
        delay = simulator.calculate_typing_delay(msg, complexity)
        indicator_duration = simulator.calculate_typing_indicator_duration(msg, complexity)

        print(f"Message: '{msg}'")
        print(f"Complexity: {complexity}/5")
        print(f"Total delay: {delay:.2f}s")
        print(f"Typing indicator: {indicator_duration}ms")
        print()

    print("\nTesting message editing:\n")

    for i in range(5):
        original = "I think I know someone who can help with that"
        if simulator.should_edit_message():
            edited, edit_type = simulator.create_message_edit(original)
            delay = simulator.generate_edit_delay()
            print(f"{i+1}. Edit scheduled ({edit_type}) after {delay:.1f}s")
            print(f"   Original: '{original}'")
            print(f"   Edited:   '{edited}'")
        else:
            print(f"{i+1}. No edit")
