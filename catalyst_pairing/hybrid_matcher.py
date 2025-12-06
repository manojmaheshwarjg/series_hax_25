"""
Hybrid Matcher - Combines Traditional + Catalyst Pairing
Two-stage matching: Traditional filtering → Catalyst re-ranking
"""

import logging
from typing import List, Dict, Any, Optional
from matcher import Matcher, MatchScore
from catalyst_matcher import CatalystMatcher, CatalystScore

logger = logging.getLogger(__name__)


class HybridMatcher:
    """
    Hybrid matching strategy combining traditional skill-based matching
    with novel Catalyst Pairing algorithm for superior match quality
    """

    def __init__(self, network: List[Dict[str, Any]] = None):
        self.traditional_matcher = Matcher(network)
        self.catalyst_matcher = CatalystMatcher()
        self.network = network or []

    def find_best_matches(self, requirements: Dict[str, Any],
                         network: List[Dict[str, Any]],
                         requester: Dict[str, Any],
                         top_n: int = 3,
                         use_catalyst: bool = True) -> List[CatalystScore]:
        """
        Find best matches using hybrid approach
        
        Args:
            requirements: What requester is looking for
            network: List of potential matches
            requester: The person requesting intro
            top_n: Number of final matches to return
            use_catalyst: Whether to use Catalyst re-ranking (default: True)
            
        Returns:
            List of CatalystScore objects with enhanced scoring
        """
        # Stage 1: Traditional matching to filter candidates
        # Get top 10-15 candidates using proven traditional algorithm
        initial_pool_size = min(max(top_n * 5, 10), len(network))
        
        logger.info(f"Stage 1: Traditional matching (filtering to top {initial_pool_size})")
        traditional_matches = self.traditional_matcher.find_matches(
            requirements, network, requester, 
            top_n=initial_pool_size
        )
        
        if not traditional_matches:
            logger.warning("No traditional matches found")
            return []
        
        logger.info(f"Found {len(traditional_matches)} candidates from traditional matcher")
        
        # Stage 2: Catalyst Pairing re-ranking
        if not use_catalyst:
            # Convert MatchScore to CatalystScore for consistent return type
            catalyst_results = []
            for match_score in traditional_matches[:top_n]:
                catalyst_score = CatalystScore(
            except Exception as e:
                # Fail-safe: If Catalyst scoring fails, fall back to traditional
                logger.warning(f"Catalyst scoring failed for {candidate.get('name', 'Unknown')}: {e}")
                catalyst_score_obj = CatalystScore(
                    user=candidate,
                    total_score=match_score.score,
                    component_scores={'traditional': match_score.score, 'error': 1.0},
                    explanation="Traditional match (Catalyst scoring unavailable)"
                )
                catalyst_scored.append(catalyst_score_obj)
        
        # Sort by hybrid score
        catalyst_scored.sort(key=lambda x: x.total_score, reverse=True)
        
        # Log top matches
        # Log top matches with detailed breakdown
        logger.info(f"Top {min(top_n, len(catalyst_scored))} Catalyst matches:")
        for i, match in enumerate(catalyst_scored[:top_n]):
            logger.info(f"  {i+1}. {match.user['name']} - Score: {match.total_score:.2f}")
            logger.info(f"     Breakdown: {match.component_scores}")
            logger.info(f"     Explanation: {match.explanation}")
        
        return catalyst_scored[:top_n]


if __name__ == "__main__":
    # Test hybrid matcher
    import sys
    import os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
    
    from network_generator import NetworkGenerator
    
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    
    print("="*60)
    print("Testing Hybrid Matcher (Traditional + Catalyst Pairing)")
    print("="*60)
    
    # Generate test network
    gen = NetworkGenerator()
    network = gen.generate_network(100)
    
    # Test requester
    requester = {
        'phone': '+1000000000',
        'name': 'Test Requester',
        'skills': ['Python', 'Django'],
        'interests': ['AI', 'startups'],
        'current_goals': ['learning React', 'scaling infrastructure'],
        'trajectory': 'rapid_growth',
        'years_experience': 3,
        'problems_solved': ['scaling to 1M users'],
        'current_projects': [{
            'description': 'building AI analytics platform',
            'stage': 'mvp',
            'challenges': ['hiring engineers', 'finding PMF']
        }]
    }
    
    # Test requirements  
    requirements = {
        'role': 'developer',
        'technology': ['React', 'TypeScript'],
        'seniority': 'senior'
    }
    
    # Create hybrid matcher
    hybrid_matcher = HybridMatcher(network)
    
    # Find matches
    print("\n📊 Finding matches...")
    matches = hybrid_matcher.find_best_matches(
        requirements, network, requester, top_n=3
    )
    
    # Display results
    print("\n" + "="*60)
    print("TOP 3 CATALYST MATCHES")
    print("="*60)
    
    for i, match in enumerate(matches, 1):
        print(f"\n🏆 Match #{i}: {match.user['name']}")
        print(f"   Role: {match.user['role']}")
        print(f"   Score: {match.total_score:.2f}")
        print(f"   Explanation: {match.explanation}")
        print(f"   Component Scores:")
        for component, score in match.component_scores.items():
            if component not in ['hybrid_score', 'traditional_score']:
                print(f"      - {component}: {score:.2f}")
    
    print("\n" + "="*60)
    print("✅ Hybrid Matcher Test Complete")
    print("="*60)
