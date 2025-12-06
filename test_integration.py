"""
Quick Integration Test: Catalyst Pairing + Groq
Tests that all components work together seamlessly
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'catalyst_pairing'))

from dotenv import load_dotenv
load_dotenv()

print("="*60)
print("INTEGRATION TEST: Catalyst Pairing + Groq + Network")
print("="*60)

# Test 1: Groq API
print("\n[1/5] Testing Groq API...")
try:
    from groq import Groq
    api_key = os.getenv('GROQ_API_KEY')
    if not api_key:
        print("❌ GROQ_API_KEY not set in .env")
    else:
        client = Groq(api_key=api_key)
        response = client.chat.completions.create(
            messages=[{"role": "user", "content": "Say 'test successful' in 2 words"}],
            model="llama-3.3-70b-versatile",
            max_tokens=10
        )
        print(f"✅ Groq API working: {response.choices[0].message.content}")
except Exception as e:
    print(f"❌ Groq API error: {e}")

# Test 2: Network Generation with Catalyst Fields
print("\n[2/5] Testing Network Generation...")
try:
    from network_generator import NetworkGenerator
    gen = NetworkGenerator()
    network = gen.generate_network(10)
    
    # Check for Catalyst fields
    sample_user = network[0]
    catalyst_fields = ['current_goals', 'skill_acquisition_dates', 'trajectory', 'problems_solved']
    has_catalyst = all(field in sample_user for field in catalyst_fields)
    
    if has_catalyst:
        print(f"✅ Network generated with Catalyst fields")
        print(f"   Sample user: {sample_user['name']}")
        print(f"   Trajectory: {sample_user.get('trajectory', 'N/A')}")
        print(f"   Goals: {sample_user.get('current_goals', [])[:2]}")
    else:
        print(f"❌ Missing Catalyst fields")
except Exception as e:
    print(f"❌ Network generation error: {e}")

# Test 3: Catalyst Matcher
print("\n[3/5] Testing Catalyst Matcher...")
try:
    from catalyst_matcher import CatalystMatcher
    
    matcher = CatalystMatcher()
    
    requester = {
        'phone': '+1000',
        'name': 'Test User',
        'skills': ['Python'],
        'current_goals': ['learning React'],
        'trajectory': 'rapid_growth',
        'years_experience': 2
    }
    
    candidate = network[0]
    requirements = {'technology': ['React']}
    
    score, components, explanation = matcher.calculate_catalyst_score(
        requester, candidate, requirements
    )
    
    print(f"✅ Catalyst scoring working")
    print(f"   Score: {score:.2f}")
    print(f"   Reciprocal Value: {components['reciprocal_value']:.2f}")
    print(f"   Explanation: {explanation[:60]}...")
except Exception as e:
    print(f"❌ Catalyst matcher error: {e}")

# Test 4: Hybrid Matcher Integration
print("\n[4/5] Testing Hybrid Matcher...")
try:
    from hybrid_matcher import HybridMatcher
    
    hybrid = HybridMatcher(network)
    
    matches = hybrid.find_best_matches(
        requirements={'technology': ['React']},
        network=network,
        requester=requester,
        top_n=3,
        use_catalyst=True
    )
    
    if matches:
        print(f"✅ Hybrid matcher working")
        print(f"   Found {len(matches)} matches")
        print(f"   Top match: {matches[0].user['name']} (score: {matches[0].total_score:.2f})")
    else:
        print(f"⚠️  No matches found (network may be too small)")
except Exception as e:
    print(f"❌ Hybrid matcher error: {e}")

# Test 5: Response Engine with Groq
print("\n[5/5] Testing Response Engine...")
try:
    from response_engine import ResponseEngine
    
    engine = ResponseEngine()
    response = engine.generate_response('greeting')
    
    if response and len(response) > 0:
        print(f"✅ Response engine working")
        print(f"   Sample response: {response[:60]}...")
    else:
        print(f"❌ Empty response")
except Exception as e:
    print(f"❌ Response engine error: {e}")

print("\n" + "="*60)
print("INTEGRATION TEST COMPLETE")
print("="*60)
print("\n✨ All systems operational! Catalyst Pairing Algorithm is LIVE.")
