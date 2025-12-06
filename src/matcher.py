"""
Matching Algorithm
Finds the best matches from the network based on requirements
"""

import logging
import math
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class MatchScore:
    """Details about a match score"""

    def __init__(self, user: Dict[str, Any], score: float, explanation: Dict[str, float]):
        self.user = user
        self.score = score
        self.explanation = explanation

    def __repr__(self):
        return f"MatchScore({self.user['name']}, score={self.score:.2f})"


class Matcher:
    """Intelligent matching algorithm"""

    def __init__(self):
        # Scoring weights (must sum to 1.0)
        self.weights = {
            'skill_overlap': 0.35,
            'interest_alignment': 0.20,
            'recency': 0.15,
            'historical_success': 0.20,
            'network_proximity': 0.10,
        }

        # Learned pattern weights (updated by learning engine)
        self.pattern_weights = {}

        # Minimum score threshold
        self.min_score_threshold = 0.6

    def find_matches(self, requirements: Dict[str, Any], network: List[Dict[str, Any]],
                    requester: Dict[str, Any], top_n: int = 3) -> List[MatchScore]:
        """
        Find best matches from network

        Args:
            requirements: What the requester is looking for
            network: List of potential matches
            requester: The person requesting the intro
            top_n: Number of top matches to return

        Returns:
            List of MatchScore objects
        """
        logger.info(f"Finding matches for requirements: {requirements}")

        matches = []

        for candidate in network:
            # Skip if candidate is the requester
            if candidate.get('phone') == requester.get('phone'):
                continue

            # Calculate match score
            score, explanation = self._calculate_match_score(requirements, candidate, requester)

            if score >= self.min_score_threshold:
                matches.append(MatchScore(candidate, score, explanation))

        # Sort by score (descending)
        matches.sort(key=lambda m: m.score, reverse=True)

        logger.info(f"Found {len(matches)} matches above threshold {self.min_score_threshold}")

        return matches[:top_n]

    def _calculate_match_score(self, requirements: Dict[str, Any],
                               candidate: Dict[str, Any],
                               requester: Dict[str, Any]) -> Tuple[float, Dict[str, float]]:
        """
        Calculate match score between requirements and candidate

        Returns:
            Tuple of (total_score, score_breakdown)
        """
        scores = {}

        # 1. Skill overlap (0.35 weight)
        scores['skill_overlap'] = self._score_skill_overlap(requirements, candidate)

        # 2. Interest alignment (0.20 weight)
        scores['interest_alignment'] = self._score_interest_alignment(requirements, candidate, requester)

        # 3. Recency (0.15 weight)
        scores['recency'] = self._score_recency(candidate)

        # 4. Historical success (0.20 weight)
        scores['historical_success'] = self._score_historical_success(candidate)

        # 5. Network proximity (0.10 weight)
        scores['network_proximity'] = self._score_network_proximity(candidate, requester)

        # Calculate weighted total
        total_score = sum(scores[key] * self.weights[key] for key in scores)

        # Apply learned pattern weights
        pattern_multiplier = self._get_pattern_multiplier(requirements, candidate)
        total_score *= pattern_multiplier

        # Apply availability boost
        if candidate.get('availability') == 'active':
            total_score *= 1.1

        # Cap at 1.0
        total_score = min(total_score, 1.0)

        return total_score, scores

    def _score_skill_overlap(self, requirements: Dict[str, Any], candidate: Dict[str, Any]) -> float:
        """
        Score based on skill overlap using Jaccard similarity

        Returns:
            Score between 0 and 1
        """
        required_skills = set()

        # Extract skills from requirements
        if 'technology' in requirements:
            tech = requirements['technology']
            if isinstance(tech, list):
                required_skills.update([t.lower() for t in tech])
            else:
                required_skills.add(tech.lower())

        if 'role' in requirements:
            role = requirements['role']
            if isinstance(role, list):
                required_skills.update([r.lower() for r in role])
            else:
                required_skills.add(role.lower())

        if 'skills' in requirements:
            skills = requirements['skills']
            if isinstance(skills, list):
                required_skills.update([s.lower() for s in skills])

        candidate_skills = set([s.lower() for s in candidate.get('skills', [])])

        # Also check role
        if candidate.get('role'):
            candidate_skills.add(candidate['role'].lower())

        if not required_skills:
            return 0.5  # Neutral if no requirements

        if not candidate_skills:
            return 0.0

        # Jaccard similarity
        intersection = required_skills & candidate_skills
        union = required_skills | candidate_skills

        if not union:
            return 0.0

        jaccard = len(intersection) / len(union)

        return jaccard

    def _score_interest_alignment(self, requirements: Dict[str, Any],
                                  candidate: Dict[str, Any],
                                  requester: Dict[str, Any]) -> float:
        """
        Score based on interest alignment

        Returns:
            Score between 0 and 1
        """
        # Combine requester's interests with requirement topics
        requester_interests = set([i.lower() for i in requester.get('interests', [])])

        if 'industry' in requirements:
            industries = requirements['industry']
            if isinstance(industries, list):
                requester_interests.update([i.lower() for i in industries])
            else:
                requester_interests.add(industries.lower())

        candidate_interests = set([i.lower() for i in candidate.get('interests', [])])

        if not requester_interests or not candidate_interests:
            return 0.5  # Neutral if no data

        # Calculate overlap
        intersection = requester_interests & candidate_interests
        union = requester_interests | candidate_interests

        if not union:
            return 0.5

        return len(intersection) / len(union)

    def _score_recency(self, candidate: Dict[str, Any]) -> float:
        """
        Score based on how recently candidate was active

        Returns:
            Score between 0 and 1
        """
        last_active_str = candidate.get('last_active')

        if not last_active_str:
            return 0.5  # Neutral if no data

        try:
            last_active = datetime.fromisoformat(last_active_str)
        except:
            return 0.5

        # Calculate days since last active
        days_since = (datetime.utcnow() - last_active).total_seconds() / 86400

        # Exponential decay with 30-day half-life
        half_life = 30
        decay_score = math.exp(-0.693 * days_since / half_life)

        return decay_score

    def _score_historical_success(self, candidate: Dict[str, Any]) -> float:
        """
        Score based on past successful introductions

        Returns:
            Score between 0 and 1
        """
        successful_intros = candidate.get('successful_intros_made', 0)
        successful_received = candidate.get('successful_intros_received', 0)

        total_success = successful_intros + successful_received

        # Normalize to 0-1 scale (20+ intros = 1.0)
        normalized = min(total_success / 20.0, 1.0)

        return normalized

    def _score_network_proximity(self, candidate: Dict[str, Any], requester: Dict[str, Any]) -> float:
        """
        Score based on network proximity (mutual connections)

        Returns:
            Score between 0 and 1
        """
        candidate_network = set(candidate.get('network', []))
        requester_network = set(requester.get('network', []))

        if not candidate_network or not requester_network:
            return 0.5  # Neutral if no network data

        # Find mutual connections
        mutual = candidate_network & requester_network

        # Score based on mutual connections (5+ = 1.0)
        score = min(len(mutual) / 5.0, 1.0)

        return score

    def _get_pattern_multiplier(self, requirements: Dict[str, Any], candidate: Dict[str, Any]) -> float:
        """
        Get learned pattern weight multiplier

        Returns:
            Multiplier between 0.5 and 1.5
        """
        # Generate pattern key from requirements + candidate attributes
        pattern_key = self._generate_pattern_key(requirements, candidate)

        # Get learned weight (default to 1.0)
        multiplier = self.pattern_weights.get(pattern_key, 1.0)

        # Ensure within bounds
        return max(0.5, min(1.5, multiplier))

    def _generate_pattern_key(self, requirements: Dict[str, Any], candidate: Dict[str, Any]) -> str:
        """Generate key for pattern matching"""
        parts = []

        if 'role' in requirements:
            parts.append(f"role:{requirements['role']}")

        if 'seniority' in requirements:
            parts.append(f"seniority:{requirements['seniority']}")

        if candidate.get('location'):
            parts.append(f"location:{candidate['location']}")

        return "|".join(sorted(parts))

    def update_pattern_weight(self, pattern_key: str, outcome: str, magnitude: float):
        """
        Update pattern weight based on outcome

        Args:
            pattern_key: Pattern identifier
            outcome: 'success' or 'failure'
            magnitude: How much to adjust (0.0 to 1.0)
        """
        current_weight = self.pattern_weights.get(pattern_key, 1.0)

        if outcome == 'success':
            adjustment = magnitude * 0.1  # Max +10% per success
            new_weight = min(current_weight + adjustment, 1.5)
        else:
            adjustment = magnitude * 0.1  # Max -10% per failure
            new_weight = max(current_weight - adjustment, 0.5)

        self.pattern_weights[pattern_key] = new_weight

        logger.info(f"Updated pattern weight for '{pattern_key}': {current_weight:.2f} -> {new_weight:.2f}")

    def explain_match(self, match_score: MatchScore) -> str:
        """
        Generate human-readable explanation of match

        Args:
            match_score: MatchScore object

        Returns:
            Explanation string
        """
        user = match_score.user
        explanation = match_score.explanation

        parts = []

        # Add name and role
        parts.append(f"{user['name']}")

        if user.get('role'):
            parts.append(f"works as {user['role']}")

        if user.get('current_company'):
            parts.append(f"at {user['current_company']}")

        # Top scoring factors
        top_factors = sorted(explanation.items(), key=lambda x: x[1] * self.weights.get(x[0], 0), reverse=True)

        for factor, score in top_factors[:2]:
            weighted_score = score * self.weights.get(factor, 0)

            if weighted_score > 0.15:  # Only mention significant factors
                if factor == 'skill_overlap':
                    skills = user.get('skills', [])[:3]
                    parts.append(f"expert in {', '.join(skills)}")
                elif factor == 'historical_success':
                    intros = user.get('successful_intros_made', 0)
                    if intros > 5:
                        parts.append(f"helped {intros} people successfully")
                elif factor == 'network_proximity':
                    parts.append("you have mutual connections")
                elif factor == 'recency':
                    parts.append("very active recently")

        return ". ".join(parts)


if __name__ == "__main__":
    # Test matcher
    logging.basicConfig(level=logging.INFO)

    matcher = Matcher()

    # Sample requester
    requester = {
        'phone': '+11111111111',
        'name': 'Test User',
        'interests': ['AI', 'startups'],
        'network': ['+15551001', '+15551002']
    }

    # Sample candidates
    candidates = [
        {
            'phone': '+15551001',
            'name': 'Sarah Chen',
            'role': 'Senior Software Engineer',
            'current_company': 'Stripe',
            'skills': ['React', 'TypeScript', 'Node.js', 'PostgreSQL'],
            'interests': ['fintech', 'startups'],
            'location': 'San Francisco',
            'availability': 'active',
            'last_active': datetime.utcnow().isoformat(),
            'successful_intros_made': 12,
            'successful_intros_received': 8,
            'network': ['+11111111111', '+15551003']
        },
        {
            'phone': '+15551002',
            'name': 'Alex Kim',
            'role': 'Product Manager',
            'current_company': 'Google',
            'skills': ['Product Strategy', 'Analytics', 'User Research'],
            'interests': ['AI', 'SaaS'],
            'location': 'New York',
            'availability': 'active',
            'last_active': (datetime.utcnow() - timedelta(days=2)).isoformat(),
            'successful_intros_made': 5,
            'successful_intros_received': 3,
            'network': ['+11111111111']
        }
    ]

    # Test matching
    requirements = {
        'role': ['developer', 'engineer'],
        'technology': ['react', 'typescript'],
        'seniority': 'senior'
    }

    matches = matcher.find_matches(requirements, candidates, requester)

    print(f"\nFound {len(matches)} matches:\n")

    for i, match in enumerate(matches, 1):
        print(f"{i}. {match.user['name']} (score: {match.score:.2f})")
        print(f"   Explanation: {matcher.explain_match(match)}")
        print(f"   Breakdown: {match.explanation}")
        print()
