"""
Catalyst Pairing Algorithm (Reciprocal Momentum Matching)
Novel matching strategy that scores bidirectional value and growth potential
"""

import logging
import math
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class CatalystScore:
    """Details about a catalyst match score"""

    def __init__(self, user: Dict[str, Any], total_score: float, 
                 component_scores: Dict[str, float], explanation: str):
        self.user = user
        self.total_score = total_score
        self.component_scores = component_scores
        self.explanation = explanation

    def __repr__(self):
        return f"CatalystScore({self.user['name']}, score={self.total_score:.2f})"


class CatalystMatcher:
    """
    Catalyst Pairing Algorithm - Reciprocal Momentum Matching
    
    Matches people not just on what they need, but on what happens when they meet.
    Evaluates bidirectional value, skill complementarity, trajectory alignment,
    and serendipity potential.
    """

    def __init__(self):
        # Component weights (must sum to 1.0)
        self.weights = {
            'primary_value': 0.25,       # Can candidate help requester?
            'reciprocal_value': 0.30,    # Can requester help candidate? (BOOSTED)
            'complementarity': 0.25,     # Teaching opportunity score (BOOSTED)
            'trajectory_alignment': 0.10, # Momentum match
            'serendipity': 0.10          # Breakthrough potential
        }
        
        # Minimum score threshold
        self.min_score_threshold = 0.5

    def calculate_catalyst_score(self, requester: Dict[str, Any], 
                                 candidate: Dict[str, Any],
                                 requirements: Dict[str, Any]) -> Tuple[float, Dict[str, float], str]:
        """
        Calculate comprehensive catalyst score
        
        Args:
            requester: The person requesting intro
            candidate: Potential match
            requirements: What requester is looking for
            
        Returns:
            Tuple of (total_score, component_scores, explanation)
        """
        scores = {}
        
        # 1. Primary Value: Can candidate help requester?
        scores['primary_value'] = self._score_primary_value(requirements, candidate)
        
        # 2. Reciprocal Value: Can requester help candidate?
        scores['reciprocal_value'] = self._score_reciprocal_value(requester, candidate)
        
        # 3. Skill Complementarity: Teaching opportunity
        scores['complementarity'] = self._score_skill_complementarity(requester, candidate, requirements)
        
        # 4. Trajectory Alignment: Momentum match
        scores['trajectory_alignment'] = self._score_trajectory(requester, candidate)
        
        # 5. Serendipity: Breakthrough potential
        scores['serendipity'] = self._score_serendipity(requester, candidate)
        
        # Calculate weighted total
        total_score = sum(scores[key] * self.weights[key] for key in scores)
        
        # Generate explanation
        explanation = self._generate_explanation(requester, candidate, scores)
        
        return total_score, scores, explanation

    def _normalize_list(self, data: Any) -> List[str]:
        """Helper to ensure we have a flat list of strings"""
        if not data:
            return []
        if isinstance(data, str):
            return [data]
        if isinstance(data, list):
            flat_list = []
            for item in data:
                if isinstance(item, list):
                    flat_list.extend(self._normalize_list(item))
                elif isinstance(item, str):
                    flat_list.append(item)
            return flat_list
        return []

    def _score_primary_value(self, requirements: Dict[str, Any], 
                            candidate: Dict[str, Any]) -> float:
        """
        Score how well candidate meets requester's needs
        (Similar to traditional skill overlap but streamlined)
        """
        score = 0.0
        hits = 0
        total_requirements = 0
        
        # Check role match
        required_role = requirements.get('role', '').lower()
        if required_role and required_role in candidate.get('role', '').lower():
            score += 0.4
            hits += 1
        total_requirements += 1 if required_role else 0
        
        # Check skill/technology overlap
        required_skills = self._normalize_list(requirements.get('technology', [])) + \
                         self._normalize_list(requirements.get('skills', []))
        
        candidate_skills = [s.lower() for s in self._normalize_list(candidate.get('skills', []))]
        
        for req_skill in required_skills:
            if isinstance(req_skill, str):
                req_skill_lower = req_skill.lower()
                # Exact match or fuzzy match
                for cand_skill in candidate_skills:
                    if req_skill_lower in cand_skill or cand_skill in req_skill_lower:
                        score += 0.15
                        hits += 1
                        break
                total_requirements += 1
        
        # Check industry match
        required_industry = requirements.get('industry', '')
        if required_industry:
            candidate_interests = [i.lower() for i in self._normalize_list(candidate.get('interests', []))]
            if required_industry.lower() in ' '.join(candidate_interests):
                score += 0.2
                hits += 1
            total_requirements += 1
        
        # Normalize to 0-1 range
        if total_requirements > 0:
            normalized_score = min(score, 1.0)
        else:
            normalized_score = 0.5  # Neutral if no specific requirements
        
        return normalized_score

    def _score_reciprocal_value(self, requester: Dict[str, Any], 
                                candidate: Dict[str, Any]) -> float:
        """
        Score what candidate gains from helping requester
        This is the KEY INNOVATION of Catalyst Pairing
        """
        score = 0.0
        
        # Get candidate's goals safely
        candidate_goals = self._normalize_list(candidate.get('current_goals', []))
        requester_skills = set(s.lower() for s in self._normalize_list(requester.get('skills', [])))
        requester_interests = set(i.lower() for i in self._normalize_list(requester.get('interests', [])))
        requester_problems_solved = set(p.lower() for p in self._normalize_list(requester.get('problems_solved', [])))
        
        # 1. Can requester help with candidate's goals?
        for goal in candidate_goals:
            goal_lower = goal.lower()
            # Check if requester has relevant experience
            if 'fundraising' in goal_lower or 'raising' in goal_lower:
                if any('investor' in s or 'vc' in s or 'fundraising' in s for s in requester_skills):
                    score += 0.3
            if 'scaling' in goal_lower:
                if 'scaling to 1m users' in requester_problems_solved or any('scale' in s for s in requester_skills):
                    score += 0.3
            if 'learning' in goal_lower:
                # Extract what they're learning
                for word in goal_lower.split():
                    if word in requester_skills:
                        score += 0.2
        
        # 2. Skill exchange potential
        # What skills does candidate want that requester has?
        candidate_interests_set = set(i.lower() for i in self._normalize_list(candidate.get('interests', [])))
        skill_overlap = requester_skills & candidate_interests_set
        if skill_overlap:
            score += 0.2 * min(len(skill_overlap), 3)  # Cap at 0.6
        
        # 3. Network value
        # If requester has more connections or is more experienced, that's valuable
        requester_intros = requester.get('successful_intros_made', 0)
        if requester_intros > 10:
            score += 0.2
        
        # 4. Company value
        # Being introduced to someone at a prestigious company has value
        requester_company = requester.get('current_company', '')
        prestigious_companies = {'Google', 'Meta', 'Amazon', 'Apple', 'Microsoft', 
                                'Stripe', 'Netflix', 'Airbnb', 'Uber'}
        if requester_company in prestigious_companies:
            score += 0.15
        
        return min(score, 1.0)

    def _score_skill_complementarity(self, requester: Dict[str, Any],
                                    candidate: Dict[str, Any],
                                    requirements: Dict[str, Any]) -> float:
        """
        Score based on skill acquisition recency and teaching opportunity
        NOVEL: People who recently learned X are the best teachers for X
        """
        score = 0.0
        
        required_skills = self._normalize_list(requirements.get('technology', [])) + \
                         self._normalize_list(requirements.get('skills', []))
        candidate_skill_dates = candidate.get('skill_acquisition_dates', {})
        
        # 1. Recent learning bonus (IMPROVED LOGIC)
        for req_skill in required_skills:
            if isinstance(req_skill, str):
                req_skill_lower = req_skill.lower()
                for cand_skill, acquisition_date in candidate_skill_dates.items():
                    if req_skill_lower in cand_skill.lower() or cand_skill.lower() in req_skill_lower:
                        # Parse acquisition date
                        try:
                            acq_date = datetime.strptime(acquisition_date, '%Y-%m')
                            months_ago = (datetime.utcnow() - acq_date).days / 30
                            
                            if months_ago <= 12:
                                # Learned within last year = PERFECT teacher
                                score += 0.8  # BOOSTED from 0.5
                                logger.debug(f"Perfect teacher bonus: {cand_skill} learned {months_ago:.0f} months ago")
                            elif months_ago <= 24:
                                # Learned within last 2 years = good teacher
                                score += 0.5  # BOOSTED from 0.3
                            else:
                                # Older = decent teacher
                                score += 0.2
                        except:
                            score += 0.2  # Default if date parsing fails
                        break  # Only count each skill once
        
        # 2. Reciprocal teaching opportunity
        # Can requester teach candidate something?
        requester_skills = set(s.lower() for s in self._normalize_list(requester.get('skills', [])))
        candidate_interests = set(i.lower() for i in self._normalize_list(candidate.get('interests', [])))
        
        teaching_opportunities = requester_skills & candidate_interests
        if teaching_opportunities:
            score += 0.3 * min(len(teaching_opportunities), 2)  # Cap at 0.6
        
        return min(score, 1.0)

    def _score_trajectory(self, requester: Dict[str, Any], 
                         candidate: Dict[str, Any]) -> float:
        """
        Score based on career trajectory alignment
        Match momentum, not just current position
        """
        score = 0.0
        
        requester_trajectory = requester.get('trajectory', 'steady')
        candidate_trajectory = candidate.get('trajectory', 'steady')
        
        # 1. Mutual growth multiplier
        if requester_trajectory == 'rapid_growth' and candidate_trajectory == 'rapid_growth':
            score += 0.4  # Both accelerating = compound effect
        
        # 2. Mentor-mentee potential
        requester_exp = requester.get('years_experience', 5)
        candidate_exp = candidate.get('years_experience', 5)
        
        if candidate.get('willing_to_mentor', False):
            if requester_trajectory == 'early_career' and candidate_exp > requester_exp + 3:
                score += 0.4  # Experienced person willing to mentor
        
        # 3. Peer learning
        if abs(requester_exp - candidate_exp) <= 2:
            score += 0.3  # Similar experience = peer learning
        
        # 4. Complementary trajectories
        if requester_trajectory == 'early_career' and candidate_trajectory == 'experienced':
            score += 0.2
        
        return min(score, 1.0)

    def _score_serendipity(self, requester: Dict[str, Any], 
                          candidate: Dict[str, Any]) -> float:
        """
        Score serendipity potential - \"weird\" matches with breakthrough potential
        """
        score = 0.0
        
        requester_industry = set(i.lower() for i in self._normalize_list(requester.get('interests', [])))
        candidate_industry = set(i.lower() for i in self._normalize_list(candidate.get('interests', [])))
        
        # 1. Cross-pollination: Different industries but overlapping problems
        requester_problems = set(p.lower() for p in self._normalize_list(requester.get('problems_solved', [])))
        candidate_challenges = []
        for project in candidate.get('current_projects', []):
            candidate_challenges.extend(c.lower() for c in project.get('challenges', []))
        candidate_challenges_set = set(candidate_challenges)
        
        # If from different domains but candidate is facing problems requester solved
        industry_overlap = requester_industry & candidate_industry
        if len(industry_overlap) < 2:  # Different domains
            problem_overlap = requester_problems & candidate_challenges_set
            if problem_overlap:
                score += 0.5  # Cross-pollination gold
        
       # 2. Complementary skill sets (1+1=3 potential)
        requester_skills = set(s.lower() for s in self._normalize_list(requester.get('skills', [])))
        candidate_skills = set(s.lower() for s in self._normalize_list(candidate.get('skills', [])))
        
        skill_intersection = requester_skills & candidate_skills
        skill_union = requester_skills | candidate_skills
        
        if len(skill_union) > 0:
            overlap_ratio = len(skill_intersection) / len(skill_union)
            if overlap_ratio < 0.3:  # Less than 30% overlap
                # Check for breakthrough potential combinations
                tech_combos = [
                    ({'ai', 'ml', 'machine learning'}, {'web3', 'blockchain', 'crypto'}),
                    ({'design', 'ui', 'ux'}, {'data science', 'analytics'}),
                    ({'healthcare', 'medical'}, {'ai', 'ml'}),
                    ({'legal', 'law'}, {'fintech', 'finance'}),
                ]
                
                for combo_a, combo_b in tech_combos:
                    has_a = bool(requester_skills & combo_a)
                    has_b = bool(candidate_skills & combo_b)
                    if has_a and has_b:
                        score += 0.4
                        break
        
        # 3. Project stage complementarity
        requester_projects = requester.get('current_projects', [])
        candidate_projects = candidate.get('current_projects', [])
        
        if requester_projects and candidate_projects:
            req_stage = requester_projects[0].get('stage', '')
            cand_stage = candidate_projects[0].get('stage', '')
            
            # Both in same stage = can share learnings
            if req_stage == cand_stage and req_stage in ['mvp', 'beta', 'scaling']:
                score += 0.2
        
        return min(score, 1.0)

    def _generate_explanation(self, requester: Dict[str, Any],
                             candidate: Dict[str, Any],
                             scores: Dict[str, float]) -> str:
        """Generate human-readable explanation of the catalyst match"""
        
        reasons = []
        
        # Highlight top scoring components
        sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        
        for component, score in sorted_scores[:3]:  # Top 3 reasons
            if score > 0.3:  # Only mention significant factors
                if component == 'primary_value':
                    reasons.append(f"has the skills you're looking for")
                elif component == 'reciprocal_value':
                    reasons.append(f"can benefit from your expertise in return")
                elif component == 'complementarity':
                    reasons.append(f"recently learned these skills (perfect teacher!)")
                elif component == 'trajectory_alignment':
                    if requester.get('trajectory') == candidate.get('trajectory') == 'rapid_growth':
                        reasons.append(f"both on rapid growth trajectories")
                    else:
                        reasons.append(f"career momentum aligns well")
                elif component == 'serendipity':
                    reasons.append(f"unexpected breakthrough potential (different domains, complementary skills)")
        
        if not reasons:
            reasons = ["solid match across multiple dimensions"]
        
        explanation = "This is a catalyst pairing because " + ", ".join(reasons) + "."
        return explanation


if __name__ == "__main__":
    # Quick test
    logging.basicConfig(level=logging.INFO)
    
    matcher = CatalystMatcher()
    
    # Test profiles
    requester = {
        'phone': '+1111111111',
        'name': 'Alice',
        'skills': ['Python', 'Django'],
        'interests': ['AI', 'startups'],
        'current_goals': ['learning React', 'scaling infrastructure'],
        'trajectory': 'rapid_growth',
        'years_experience': 3,
        'problems_solved': ['scaling to 1M users'],
        'current_projects': [{'stage': 'mvp', 'challenges': ['hiring engineers']}]
    }
    
    candidate = {
        'phone': '+2222222222',
        'name': 'Bob',
        'role': 'Senior Frontend Engineer',
        'skills': ['React', 'TypeScript', 'Node.js'],
        'interests': ['startups', 'AI'],
        'current_goals': ['learning Python', 'mentoring others'],
        'skill_acquisition_dates': {'React': '2024-06', 'TypeScript': '2023-01'},
        'trajectory': 'rapid_growth',
        'years_experience': 5,
        'problems_solved': ['team building'],
        'willing_to_mentor': True,
        'current_projects': [{'stage': 'mvp', 'challenges': ['scaling database']}]
    }
    
    requirements = {
        'role': 'developer',
        'technology': ['React'],
        'seniority': 'senior'
    }
    
    total_score, component_scores, explanation = matcher.calculate_catalyst_score(
        requester, candidate, requirements
    )
    
    print(f"\n=== Catalyst Match Test ===")
    print(f"Total Score: {total_score:.2f}")
    print(f"\nComponent Breakdown:")
    for component, score in component_scores.items():
        print(f"  {component}: {score:.2f}")
    print(f"\nExplanation: {explanation}")
