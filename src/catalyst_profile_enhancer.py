"""
Catalyst Profile Enhancer
Extracts Catalyst Pairing fields from natural conversation
"""

import logging
import re
from typing import Dict, List, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class CatalystProfileEnhancer:
    """
    Enhances user profiles with Catalyst Pairing fields by extracting:
    - current_goals
    - trajectory
    - problems_solved
    - willing_to_mentor
    - skill_acquisition_dates
    """

    def __init__(self):
        # Goal extraction patterns
        self.goal_patterns = [
            r"(?:i'm|i am|im) (?:trying to|looking to|wanting to|hoping to) (.+?)(?:\.|,|$)",
            r"(?:i want to|i'd like to|i need to) (.+?)(?:\.|,|$)",
            r"my goal is to (.+?)(?:\.|,|$)",
            r"(?:learning|studying|picking up) (.+?)(?:\.|,|$)",
            r"(?:i'm|i am) (?:working on|focused on) (.+?)(?:\.|,|$)",
            r"(?:raising|seeking|finding) (.+?)(?:\.|,|$)",
            r"(?:building|creating|launching) (.+?)(?:\.|,|$)",
        ]

        # Trajectory indicators
        self.trajectory_indicators = {
            'early_career': [
                'just started', 'new to', 'junior', 'learning', 'first job',
                'entry level', 'recently graduated', 'bootcamp', 'intern'
            ],
            'rapid_growth': [
                'scaling', 'growing fast', 'expanding', 'raising', 'hiring',
                'launching', 'building', 'startup', 'founder', 'explosive growth'
            ],
            'steady': [
                'stable', 'consistent', 'maintaining', 'established',
                'senior', 'experienced', 'veteran'
            ],
            'experienced': [
                'years of experience', 'decade', 'veteran', 'expert',
                'lead', 'principal', 'director', 'vp', 'c-level'
            ]
        }

        # Problem-solving patterns
        self.problem_patterns = [
            r"(?:i've|i have|i) (?:solved|fixed|handled|dealt with) (.+?)(?:\.|,|$)",
            r"(?:i've|i have|i) (?:scaled|grew|built|launched) (.+?)(?:\.|,|$)",
            r"(?:successfully|managed to) (.+?)(?:\.|,|$)",
            r"(?:i helped|i led) (.+?)(?:\.|,|$)",
        ]

        # Mentorship indicators
        self.mentorship_indicators = [
            'love teaching', 'enjoy mentoring', 'happy to help', 'willing to mentor',
            'teach', 'mentor', 'help others', 'share knowledge', 'guide',
            'coach', 'train'
        ]

    def enhance_profile(self, profile: Dict[str, Any], message: str,
                       intent: str) -> Dict[str, Any]:
        """
        Extract Catalyst fields from message and update profile

        Args:
            profile: User profile to enhance
            message: User's message
            intent: Classified intent

        Returns:
            Dictionary of updates made
        """
        updates = {}
        message_lower = message.lower()

        # Extract goals
        goals = self._extract_goals(message_lower)
        if goals:
            if 'current_goals' not in profile:
                profile['current_goals'] = []
            for goal in goals:
                if goal not in profile['current_goals']:
                    profile['current_goals'].append(goal)
                    logger.info(f"[CATALYST] Added goal: {goal}")
            # Keep only last 5 goals
            profile['current_goals'] = profile['current_goals'][-5:]
            updates['goals'] = f"Added {len(goals)} goals"

        # Detect trajectory
        trajectory = self._detect_trajectory(message_lower, profile)
        if trajectory and trajectory != profile.get('trajectory'):
            profile['trajectory'] = trajectory
            updates['trajectory'] = f"Detected: {trajectory}"
            logger.info(f"[CATALYST] Trajectory: {trajectory}")

        # Extract problems solved
        problems = self._extract_problems_solved(message_lower)
        if problems:
            if 'problems_solved' not in profile:
                profile['problems_solved'] = []
            for problem in problems:
                if problem not in profile['problems_solved']:
                    profile['problems_solved'].append(problem)
                    logger.info(f"[CATALYST] Problem solved: {problem}")
            profile['problems_solved'] = profile['problems_solved'][-10:]
            updates['problems'] = f"Added {len(problems)} problems solved"

        # Detect mentorship willingness
        willing_to_mentor = self._detect_mentorship_willingness(message_lower)
        if willing_to_mentor is not None:
            profile['willing_to_mentor'] = willing_to_mentor
            updates['mentorship'] = f"Willing to mentor: {willing_to_mentor}"
            logger.info(f"[CATALYST] Willing to mentor: {willing_to_mentor}")

        # Track skill acquisition dates (when user mentions learning something)
        skill_dates = self._extract_skill_acquisition_dates(message_lower, profile)
        if skill_dates:
            if 'skill_acquisition_dates' not in profile:
                profile['skill_acquisition_dates'] = {}
            profile['skill_acquisition_dates'].update(skill_dates)
            updates['skill_dates'] = f"Tracked {len(skill_dates)} skill dates"

        return updates

    def _extract_goals(self, message_lower: str) -> List[str]:
        """Extract current goals from message"""
        goals = []

        for pattern in self.goal_patterns:
            matches = re.finditer(pattern, message_lower)
            for match in matches:
                goal = match.group(1).strip()
                # Clean and validate
                if len(goal) > 5 and len(goal) < 100:
                    # Remove common filler words
                    goal = re.sub(r'\b(just|really|very|quite)\b', '', goal).strip()
                    if goal:
                        goals.append(goal)

        return goals[:3]  # Max 3 goals per message

    def _detect_trajectory(self, message_lower: str,
                          profile: Dict[str, Any]) -> Optional[str]:
        """Detect career trajectory from message"""
        scores = {trajectory: 0 for trajectory in self.trajectory_indicators}

        for trajectory, indicators in self.trajectory_indicators.items():
            for indicator in indicators:
                if indicator in message_lower:
                    scores[trajectory] += 1

        # Get trajectory with highest score
        max_score = max(scores.values())
        if max_score > 0:
            for trajectory, score in scores.items():
                if score == max_score:
                    return trajectory

        # Infer from years of experience if mentioned
        years_match = re.search(r'(\d+)\s*(?:years?|yrs?) (?:of )?experience', message_lower)
        if years_match:
            years = int(years_match.group(1))
            if years < 2:
                return 'early_career'
            elif years < 5:
                return 'steady'
            else:
                return 'experienced'

        return None

    def _extract_problems_solved(self, message_lower: str) -> List[str]:
        """Extract problems the user has solved"""
        problems = []

        for pattern in self.problem_patterns:
            matches = re.finditer(pattern, message_lower)
            for match in matches:
                problem = match.group(1).strip()
                if len(problem) > 10 and len(problem) < 150:
                    problems.append(problem)

        return problems[:5]  # Max 5 per message

    def _detect_mentorship_willingness(self, message_lower: str) -> Optional[bool]:
        """Detect if user is willing to mentor"""
        for indicator in self.mentorship_indicators:
            if indicator in message_lower:
                return True

        # Check for negative indicators
        negative_indicators = [
            "don't have time to mentor", "not interested in mentoring",
            "too busy to teach", "can't mentor"
        ]
        for indicator in negative_indicators:
            if indicator in message_lower:
                return False

        return None  # No clear signal

    def _extract_skill_acquisition_dates(self, message_lower: str,
                                        profile: Dict[str, Any]) -> Dict[str, str]:
        """Extract when skills were learned"""
        skill_dates = {}
        current_month = datetime.now().strftime('%Y-%m')

        # Pattern: "learned X [time ago]"
        learned_patterns = [
            r"(?:learned|picked up|started) (\w+(?:\s+\w+)?) (?:(\d+) (?:months?|years?) ago)",
            r"(?:recently|just) (?:learned|picked up) (\w+(?:\s+\w+)?)",
        ]

        for pattern in learned_patterns:
            matches = re.finditer(pattern, message_lower)
            for match in matches:
                skill = match.group(1).strip()
                
                # Calculate date
                if len(match.groups()) > 1 and match.group(2):
                    # Has time ago
                    time_ago = int(match.group(2))
                    if 'month' in pattern:
                        date = datetime.now()
                        # Subtract months (approximate)
                        year = date.year
                        month = date.month - time_ago
                        while month <= 0:
                            month += 12
                            year -= 1
                        skill_dates[skill] = f"{year:04d}-{month:02d}"
                    elif 'year' in pattern:
                        year = datetime.now().year - time_ago
                        skill_dates[skill] = f"{year:04d}-01"
                else:
                    # Recently learned = current month
                    skill_dates[skill] = current_month

        return skill_dates

    def generate_catalyst_questions(self, profile: Dict[str, Any]) -> List[str]:
        """
        Generate questions to fill in missing Catalyst fields

        Args:
            profile: User profile

        Returns:
            List of questions to ask
        """
        questions = []

        # Check what's missing
        if not profile.get('current_goals'):
            questions.append("What are you currently working towards?")

        if not profile.get('trajectory'):
            questions.append("How would you describe your career stage right now?")

        if not profile.get('problems_solved'):
            questions.append("What's a challenge you've successfully tackled recently?")

        if profile.get('willing_to_mentor') is None:
            questions.append("Are you open to mentoring others in your areas of expertise?")

        return questions[:2]  # Max 2 questions


if __name__ == "__main__":
    # Test Catalyst Profile Enhancer
    logging.basicConfig(level=logging.INFO)

    enhancer = CatalystProfileEnhancer()

    profile = {
        'phone': '+1234567890',
        'name': 'Test User',
        'skills': ['Python']
    }

    # Test messages
    test_messages = [
        ("I'm trying to learn React and scale my startup to 1M users", 'skill_share'),
        ("I've been coding for 3 years and love teaching junior developers", 'skill_share'),
        ("Recently learned TypeScript, about 6 months ago", 'skill_share'),
        ("I've successfully scaled databases and handled regulatory compliance", 'skill_share'),
    ]

    print("Testing Catalyst Profile Enhancer\n")
    for message, intent in test_messages:
        print(f"Message: {message}")
        updates = enhancer.enhance_profile(profile, message, intent)
        print(f"Updates: {updates}\n")

    print("\nFinal Profile:")
    print(f"Goals: {profile.get('current_goals', [])}")
    print(f"Trajectory: {profile.get('trajectory', 'N/A')}")
    print(f"Problems Solved: {profile.get('problems_solved', [])}")
    print(f"Willing to Mentor: {profile.get('willing_to_mentor', 'N/A')}")
    print(f"Skill Dates: {profile.get('skill_acquisition_dates', {})}")
