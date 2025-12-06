"""
End-to-End Test: Catalyst-Enhanced Conversation Flow
Tests that conversation extracts Catalyst fields and feeds them into matching
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'catalyst_pairing'))

from catalyst_profile_enhancer import CatalystProfileEnhancer
from network_generator import NetworkGenerator
from hybrid_matcher import HybridMatcher
import logging

logging.basicConfig(level=logging.INFO, format='%(message)s')

print("="*70)
print("END-TO-END TEST: Catalyst-Enhanced Conversation Flow")
print("="*70)

# Simulate a conversation where user describes themselves
enhancer = CatalystProfileEnhancer()

user_profile = {
    'phone': '+1234567890',
    'name': 'Alice',
    'skills': ['Python', 'Django'],
    'interests': ['AI']
}

print("\n📱 CONVERSATION SIMULATION")
print("-"*70)

conversation = [
    "Hey, I'm Alice and I'm trying to learn React for my startup",
    "I've been coding for 3 years and recently picked up TypeScript",
    "I love teaching junior developers and helping them grow",
    "I've successfully scaled databases to handle millions of users",
    "I'm also working on raising a seed round right now"
]

for i, message in enumerate(conversation, 1):
    print(f"\n💬 User: {message}")
    updates = enhancer.enhance_profile(user_profile, message, 'skill_share')
    if updates:
        print(f"   ✅ Extracted: {', '.join(updates.keys())}")

print("\n" + "="*70)
print("📊 FINAL PROFILE (Catalyst-Enhanced)")
print("="*70)

print(f"\n🎯 Goals: {user_profile.get('current_goals', [])}")
print(f"📈 Trajectory: {user_profile.get('trajectory', 'N/A')}")
print(f"🏆 Problems Solved: {user_profile.get('problems_solved', [])}")
print(f"👨‍🏫 Willing to Mentor: {user_profile.get('willing_to_mentor', 'N/A')}")
print(f"📅 Skill Dates: {user_profile.get('skill_acquisition_dates', {})}")

# Now test matching with this enhanced profile
print("\n" + "="*70)
print("🔍 TESTING CATALYST MATCHING")
print("="*70)

gen = NetworkGenerator()
network = gen.generate_network(50)

matcher = HybridMatcher(network)

# User is looking for a React developer
requirements = {
    'technology': ['React'],
    'seniority': 'senior'
}

print(f"\n🔎 Searching for: {requirements}")

matches = matcher.find_best_matches(
    requirements, network, user_profile,
    top_n=3, use_catalyst=True
)

if matches:
    print(f"\n✨ Found {len(matches)} Catalyst matches:")
    for i, match in enumerate(matches, 1):
        print(f"\n   {i}. {match.user['name']}")
        print(f"      Score: {match.total_score:.2f}")
        print(f"      Why: {match.explanation[:80]}...")
        
        # Show Catalyst components
        if 'reciprocal_value' in match.component_scores:
            print(f"      Reciprocal Value: {match.component_scores['reciprocal_value']:.2f}")
        if 'complementarity' in match.component_scores:
            print(f"      Complementarity: {match.component_scores['complementarity']:.2f}")
else:
    print("\n⚠️  No matches found")

print("\n" + "="*70)
print("✅ END-TO-END TEST COMPLETE")
print("="*70)
print("\n💡 The conversation flow now:")
print("   1. Extracts Catalyst fields from natural conversation")
print("   2. Builds rich user profiles with goals, trajectory, etc.")
print("   3. Feeds this data into Catalyst Pairing Algorithm")
print("   4. Returns matches based on bidirectional value & momentum")
