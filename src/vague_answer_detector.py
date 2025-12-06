"""
Vague Answer Detector
Detects when users give vague/generic answers and generates quirky follow-ups
"""

import logging
import random
from typing import Optional

logger = logging.getLogger(__name__)


class VagueAnswerDetector:
    """
    Detects vague answers and generates context-aware follow-ups
    Maintains "Well-Connected Insider" persona
    """

    def __init__(self):
        # Vague answer patterns
        self.vague_patterns = {
            'generic_stuff': ['stuff', 'things', 'something', 'whatever'],
            'uncertain': ['idk', 'not sure', 'dunno', 'maybe', 'i guess'],
            'too_short': [],  # Detected by length
            'evasive': ['just', 'kinda', 'sorta', 'like'],
        }

        # Context-aware follow-ups
        self.follow_ups = {
            'goals': {
                'generic': [
                    "C'mon, give me something to work with here 😅 What specifically?",
                    "Need more than that! What's the actual goal?",
                    "Be specific - what are you trying to achieve?",
                ],
                'uncertain': [
                    "No worries! What's your best guess?",
                    "Take a shot - what feels right?",
                    "Even a rough idea helps!",
                ],
                'too_short': [
                    "Tell me more - what does that look like?",
                    "Expand on that a bit?",
                    "Give me the full picture",
                ]
            },
            'trajectory': {
                'generic': [
                    "How long we talking? 2 years? 10?",
                    "Give me a number - years of experience?",
                    "Early days or been at this a while?",
                ],
                'uncertain': [
                    "Ballpark it for me",
                    "Roughly how long?",
                    "Your best estimate?",
                ]
            },
            'problems': {
                'generic': [
                    "What kind of stuff? Be specific",
                    "Like what? Give me an example",
                    "Name one thing you've crushed",
                ],
                'uncertain': [
                    "Think of your biggest win recently",
                    "What's something you're proud of?",
                    "Even a small win counts!",
                ]
            },
            'default': {
                'generic': [
                    "I need a bit more detail to help you out",
                    "Can you be more specific?",
                    "Give me something concrete to work with",
                ],
                'uncertain': [
                    "No pressure - just your best guess",
                    "What feels right to you?",
                    "Take a stab at it",
                ]
            }
        }

    def is_vague(self, answer: str, context: str = 'default') -> bool:
        """
        Check if an answer is too vague
        
        Args:
            answer: User's answer
            context: What question was asked (goals, trajectory, problems, etc.)
            
        Returns:
            True if answer is vague
        """
        answer_lower = answer.lower().strip()
        
        # Check for vague patterns
        for pattern_type, patterns in self.vague_patterns.items():
            if pattern_type == 'too_short':
                # Answer is too short (less than 3 words, excluding common short valid answers)
                word_count = len(answer.split())
                if word_count < 3 and answer_lower not in ['yes', 'no', 'sure', 'okay']:
                    return True
            else:
                # Check if answer contains vague words
                if any(pattern in answer_lower for pattern in patterns):
                    return True

        # Context-specific vague checks
        if context == 'goals':
            # "grow" without specifics is vague
            if answer_lower in ['grow', 'improve', 'get better', 'learn']:
                return True
        
        elif context == 'trajectory':
            # "a while" or "some time" is vague
            if any(phrase in answer_lower for phrase in ['a while', 'some time', 'long time']):
                return True

        return False

    def generate_follow_up(self, vague_answer: str, context: str = 'default',
                          original_question: str = "") -> str:
        """
        Generate a quirky follow-up for a vague answer
        
        Args:
            vague_answer: The vague answer given
            context: What was being asked about
            original_question: The original question
            
        Returns:
            Follow-up question
        """
        answer_lower = vague_answer.lower().strip()
        
        # Determine vagueness type
        vague_type = 'generic'
        if any(word in answer_lower for word in self.vague_patterns['uncertain']):
            vague_type = 'uncertain'
        elif len(vague_answer.split()) < 3:
            vague_type = 'too_short'

        # Get context-specific follow-ups
        context_follow_ups = self.follow_ups.get(context, self.follow_ups['default'])
        
        # Get follow-ups for this vagueness type
        follow_ups = context_follow_ups.get(vague_type, context_follow_ups.get('generic', []))
        
        if follow_ups:
            return random.choice(follow_ups)
        
        # Fallback
        return "Can you be more specific?"

    def get_context_from_question(self, question: str) -> str:
        """
        Determine context from the question that was asked
        
        Args:
            question: The question that was asked
            
        Returns:
            Context type (goals, trajectory, problems, default)
        """
        question_lower = question.lower()
        
        if any(word in question_lower for word in ['goal', 'working towards', 'focused on', 'trying to']):
            return 'goals'
        elif any(word in question_lower for word in ['how long', 'experience', 'years', 'career']):
            return 'trajectory'
        elif any(word in question_lower for word in ['challenge', 'problem', 'solved', 'tackled', 'win']):
            return 'problems'
        
        return 'default'


if __name__ == "__main__":
    # Test vague answer detector
    detector = VagueAnswerDetector()

    test_cases = [
        ("What are you working towards?", "stuff", "goals"),
        ("How long have you been coding?", "a while", "trajectory"),
        ("What challenges have you solved?", "idk", "problems"),
        ("What are your goals?", "grow", "goals"),
        ("What are you focused on?", "I'm trying to scale my startup to 1M users", "goals"),
    ]

    print("=== Vague Answer Detector Test ===\n")

    for question, answer, expected_context in test_cases:
        print(f"Q: {question}")
        print(f"A: {answer}")
        
        context = detector.get_context_from_question(question)
        is_vague = detector.is_vague(answer, context)
        
        print(f"Context: {context}")
        print(f"Is vague: {is_vague}")
        
        if is_vague:
            follow_up = detector.generate_follow_up(answer, context, question)
            print(f"Follow-up: {follow_up}")
        
        print()
