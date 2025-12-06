"""
Profile Builder
Intelligently builds and updates user profiles from natural language conversations
ENTERPRISE-GRADE: Prevents profile pollution from search requests
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import re
from message_context_analyzer import MessageContextAnalyzer, MessageContext

logger = logging.getLogger(__name__)


class ProfileBuilder:
    """
    Builds rich user profiles from conversation data

    CRITICAL: Only updates profile when user is describing THEMSELVES,
    never when they're searching for others.
    """

    def __init__(self, nlp_engine=None):
        self.nlp_engine = nlp_engine

        # Temporal decay weights (newer info is more relevant)
        self.decay_half_life_days = 30

        # Context analyzer to prevent profile pollution
        self.context_analyzer = MessageContextAnalyzer()

    def update_profile_from_message(self, profile: Dict[str, Any], message: str,
                                    entities: Dict[str, List[str]],
                                    nlp_analysis: Optional[Any] = None,
                                    intent: str = 'other') -> Dict[str, str]:
        """
        Update user profile based on message content

        ENTERPRISE-GRADE SAFETY: Uses context analysis to prevent profile pollution.
        Only updates when user is describing themselves, not when searching.

        Args:
            profile: Current user profile
            message: User's message
            entities: Extracted entities
            nlp_analysis: Optional NLP analysis
            intent: Classified intent

        Returns:
            Dictionary of updates made
        """
        updates = {}
        message_lower = message.lower()

        # CRITICAL: Check if this message should update profile
        should_update = self.context_analyzer.should_update_profile(message, intent, entities)

        if not should_update:
            logger.info(f"[PROFILE-GUARD] Skipping profile update for search/non-profile message")
            # Still update activity status
            profile['last_active'] = datetime.utcnow().isoformat()
            return {}

        # Safe to update profile - user is describing themselves
        logger.info(f"[PROFILE-UPDATE] Updating profile from self-description message")

        # Extract skills (only if self-describing)
        skills_added = self._extract_and_add_skills(profile, entities, message_lower, intent)
        if skills_added:
            updates['skills'] = f"Added {len(skills_added)} skills"

        # Extract interests
        interests_added = self._extract_and_add_interests(profile, entities, message_lower, intent)
        if interests_added:
            updates['interests'] = f"Added {len(interests_added)} interests"

        # Extract current project
        project = self._extract_current_project(message_lower)
        if project:
            if 'projects' not in profile:
                profile['projects'] = []
            if project not in profile['projects']:
                profile['projects'].insert(0, project)  # Add to front
                profile['projects'] = profile['projects'][:5]  # Keep last 5
                updates['projects'] = f"Added project: {project}"

        # Extract location
        location = self._extract_location(entities, message_lower)
        if location and location != profile.get('location'):
            profile['location'] = location
            updates['location'] = f"Updated to {location}"

        # Extract name if mentioned
        name = self._extract_name(message_lower)
        if name and not profile.get('name'):
            profile['name'] = name
            updates['name'] = f"Set name to {name}"

        # Extract current company
        company = self._extract_company(entities, message_lower)
        if company:
            if 'current_company' not in profile or profile['current_company'] != company:
                profile['current_company'] = company
                updates['company'] = f"Working at {company}"

        # Detect communication style
        style = self._detect_communication_style(message)
        if style != profile.get('communication_style', 'neutral'):
            profile['communication_style'] = style
            updates['communication_style'] = f"Style: {style}"

        # Update activity status
        profile['last_active'] = datetime.utcnow().isoformat()
        profile['availability'] = 'active'

        return updates

    def _extract_and_add_skills(self, profile: Dict[str, Any],
                                entities: Dict[str, List[str]],
                                message_lower: str,
                                intent: str) -> List[str]:
        """
        Extract and add skills to profile

        CONSERVATIVE: Only extracts from explicit self-description patterns,
        never from bare entities (which could be search requirements)
        """
        if 'skills' not in profile:
            profile['skills'] = []

        added = []

        # ONLY add skills from explicit self-description patterns
        # Never blindly add entities - they could be search requirements!
        skill_patterns = [
            r"i know (\w+(?:\s+\w+)?)",
            r"i['']m good at (\w+(?:\s+\w+)?)",
            r"i can (\w+(?:\s+\w+)?)",
            r"i work with (\w+(?:\s+\w+)?)",
            r"i use (\w+(?:\s+\w+)?)",
            r"i['']m experienced (?:in|with) (\w+(?:\s+\w+)?)",
            r"i['']m an? expert in (\w+(?:\s+\w+)?)",
            r"i['']m an? (\w+(?:\s+\w+)?) (?:developer|engineer|designer|analyst)",
            r"my (?:skill|expertise|background) (?:is|includes) (\w+(?:\s+\w+)?)",
            r"i specialize in (\w+(?:\s+\w+)?)",
        ]

        for pattern in skill_patterns:
            matches = re.finditer(pattern, message_lower)
            for match in matches:
                skill = match.group(1).strip()
                if skill and skill not in profile['skills'] and skill not in added:
                    # Validate skill length
                    if len(skill) > 1 and skill not in ['a', 'an', 'the', 'at', 'in']:
                        profile['skills'].append(skill)
                        added.append(skill)
                        logger.info(f"[SKILL-ADDED] '{skill}' from pattern match")

        # ONLY add entities if intent is explicitly 'skill_share' or 'update_profile'
        if intent in ['skill_share', 'update_profile']:
            skill_types = ['technology', 'tool']  # Removed 'role' to be more conservative
            for skill_type in skill_types:
                if skill_type in entities:
                    for skill in entities[skill_type]:
                        if skill not in profile['skills'] and skill not in added:
                            profile['skills'].append(skill)
                            added.append(skill)
                            logger.info(f"[SKILL-ADDED] '{skill}' from entity (safe intent)")

        return added

    def _extract_and_add_interests(self, profile: Dict[str, Any],
                                   entities: Dict[str, List[str]],
                                   message_lower: str,
                                   intent: str) -> List[str]:
        """
        Extract and add interests to profile

        CONSERVATIVE: Only from explicit patterns, never bare entities
        """
        if 'interests' not in profile:
            profile['interests'] = []

        added = []

        # Interests from explicit self-description patterns
        interest_patterns = [
            r"i['']m interested in (\w+(?:\s+\w+)?)",
            r"i['']m passionate about (\w+(?:\s+\w+)?)",
            r"i love (\w+(?:\s+\w+)?)",
            r"i['']m into (\w+(?:\s+\w+)?)",
            r"my interest(?:s)? (?:is|are|include) (\w+(?:\s+\w+)?)",
        ]

        for pattern in interest_patterns:
            matches = re.finditer(pattern, message_lower)
            for match in matches:
                interest = match.group(1).strip()
                if interest and interest not in profile['interests'] and interest not in added:
                    # Filter out common words
                    if len(interest) > 3 and interest not in ['that', 'this', 'them', 'working', 'looking']:
                        profile['interests'].append(interest)
                        added.append(interest)
                        logger.info(f"[INTEREST-ADDED] '{interest}' from pattern match")

        # Only add industry entities for safe intents
        if intent in ['skill_share', 'update_profile']:
            if 'industry' in entities:
                for industry in entities['industry']:
                    if industry not in profile['interests'] and industry not in added:
                        profile['interests'].append(industry)
                        added.append(industry)
                        logger.info(f"[INTEREST-ADDED] '{industry}' from entity (safe intent)")

        return added

    def _extract_current_project(self, message_lower: str) -> Optional[str]:
        """Extract what the user is currently working on"""
        project_patterns = [
            r"working on (.+?)(?:\.|,|$)",
            r"building (.+?)(?:\.|,|$)",
            r"developing (.+?)(?:\.|,|$)",
            r"creating (.+?)(?:\.|,|$)",
            r"started (.+?)(?:\.|,|$)",
        ]

        for pattern in project_patterns:
            match = re.search(pattern, message_lower)
            if match:
                project = match.group(1).strip()
                # Clean up the project description
                if len(project) > 10 and len(project) < 100:
                    return project

        return None

    def _extract_location(self, entities: Dict[str, List[str]],
                         message_lower: str) -> Optional[str]:
        """Extract location information"""
        # First check entities
        if 'location' in entities and entities['location']:
            return entities['location'][0]

        # Check for common location patterns
        location_patterns = [
            r"(?:in|from|based in|located in) ([a-z\s]+?)(?:\.|,|$)",
            r"(new york|san francisco|los angeles|boston|seattle|austin|chicago|nyc|sf|la)",
        ]

        for pattern in location_patterns:
            match = re.search(pattern, message_lower)
            if match:
                return match.group(1).strip()

        return None

    def _extract_name(self, message_lower: str) -> Optional[str]:
        """Extract user's name if they introduce themselves"""
        name_patterns = [
            r"i['']m (\w+)",
            r"my name is (\w+)",
            r"call me (\w+)",
            r"this is (\w+)",
        ]

        for pattern in name_patterns:
            match = re.search(pattern, message_lower)
            if match:
                name = match.group(1).strip().title()
                # Filter out common words
                if name.lower() not in ['working', 'looking', 'trying', 'going', 'interested']:
                    return name

        return None

    def _extract_company(self, entities: Dict[str, List[str]],
                        message_lower: str) -> Optional[str]:
        """Extract current company"""
        # Check entities first
        if 'ORG' in entities and entities['ORG']:
            # Look for "at/work at" patterns
            for org in entities['ORG']:
                if f"at {org.lower()}" in message_lower or f"work at {org.lower()}" in message_lower:
                    return org

        # Check for explicit patterns
        company_patterns = [
            r"work(?:ing)? at (\w+(?:\s+\w+)?)",
            r"employed at (\w+(?:\s+\w+)?)",
            r"(?:i|i'm) at (\w+(?:\s+\w+)?)",
        ]

        for pattern in company_patterns:
            match = re.search(pattern, message_lower)
            if match:
                company = match.group(1).strip().title()
                if len(company) > 2:
                    return company

        return None

    def _detect_communication_style(self, message: str) -> str:
        """
        Detect user's communication style

        Returns:
            'formal', 'casual', or 'neutral'
        """
        message_lower = message.lower()

        # Formal indicators
        formal_indicators = [
            'would you', 'could you', 'please', 'thank you very much',
            'i would appreciate', 'kindly', 'regards'
        ]

        # Casual indicators
        casual_indicators = [
            'hey', 'yeah', 'yep', 'nah', 'gonna', 'wanna', 'kinda',
            'lol', 'haha', 'cool', 'awesome', 'btw', 'thx', 'pls'
        ]

        # Emoji usage (casual)
        has_emoji = bool(re.search(r'[\U0001F600-\U0001F64F]', message))

        formal_score = sum(1 for indicator in formal_indicators if indicator in message_lower)
        casual_score = sum(1 for indicator in casual_indicators if indicator in message_lower)

        if has_emoji:
            casual_score += 1

        # Exclamation marks and questions
        exclamations = message.count('!')
        if exclamations > 1:
            casual_score += 1

        if formal_score > casual_score:
            return 'formal'
        elif casual_score > formal_score:
            return 'casual'
        else:
            return 'neutral'

    def build_profile_summary(self, profile: Dict[str, Any]) -> str:
        """
        Create a human-readable profile summary

        Args:
            profile: User profile

        Returns:
            Formatted summary string
        """
        parts = []

        if profile.get('name'):
            parts.append(f"{profile['name']}")

        if profile.get('current_company'):
            parts.append(f"works at {profile['current_company']}")

        if profile.get('location'):
            parts.append(f"in {profile['location']}")

        if profile.get('skills'):
            skills = profile['skills'][:3]  # Top 3 skills
            parts.append(f"skilled in {', '.join(skills)}")

        if profile.get('interests'):
            interests = profile['interests'][:2]  # Top 2 interests
            parts.append(f"interested in {', '.join(interests)}")

        if profile.get('projects'):
            parts.append(f"currently working on {profile['projects'][0]}")

        return '. '.join(parts) if parts else "New user"

    def calculate_profile_completeness(self, profile: Dict[str, Any]) -> float:
        """
        Calculate how complete a profile is (0.0 to 1.0)

        Args:
            profile: User profile

        Returns:
            Completeness score
        """
        fields = {
            'name': 0.1,
            'skills': 0.3,
            'interests': 0.2,
            'location': 0.1,
            'projects': 0.15,
            'current_company': 0.1,
            'conversation_history': 0.05,
        }

        score = 0.0

        for field, weight in fields.items():
            if field in profile and profile[field]:
                if isinstance(profile[field], list):
                    if len(profile[field]) > 0:
                        score += weight
                else:
                    score += weight

        return min(score, 1.0)

    def get_profile_gaps(self, profile: Dict[str, Any]) -> List[str]:
        """
        Identify what's missing from a profile

        Args:
            profile: User profile

        Returns:
            List of missing fields
        """
        gaps = []

        if not profile.get('skills') or len(profile['skills']) == 0:
            gaps.append('skills')

        if not profile.get('interests') or len(profile['interests']) == 0:
            gaps.append('interests')

        if not profile.get('location'):
            gaps.append('location')

        if not profile.get('projects') or len(profile['projects']) == 0:
            gaps.append('current_project')

        return gaps


if __name__ == "__main__":
    # Test profile builder
    logging.basicConfig(level=logging.INFO)

    builder = ProfileBuilder()

    # Sample profile
    profile = {
        'phone': '+17167509384',
        'skills': [],
        'interests': [],
        'projects': [],
    }

    # Test messages
    messages = [
        ("Hey, I'm Alex and I'm working on a SaaS product", {'PERSON': ['Alex']}),
        ("I know Python and React really well", {'technology': ['python', 'react']}),
        ("Based in San Francisco, working at Stripe", {'GPE': ['San Francisco'], 'ORG': ['Stripe']}),
        ("I'm interested in AI and machine learning", {'industry': ['ai']}),
    ]

    print("Initial profile completeness:", builder.calculate_profile_completeness(profile))

    for message, entities in messages:
        print(f"\nMessage: {message}")
        updates = builder.update_profile_from_message(profile, message, entities)
        print(f"Updates: {updates}")

    print(f"\nFinal profile summary: {builder.build_profile_summary(profile)}")
    print(f"Profile completeness: {builder.calculate_profile_completeness(profile):.1%}")
    print(f"Profile gaps: {builder.get_profile_gaps(profile)}")
