"""
Demo: Proactive Catalyst Conversation Flow
Shows how the bot guides conversation to collect Catalyst data
"""

print("="*70)
print("DEMO: Proactive Catalyst Conversation Flow")
print("="*70)
print()
print("This demonstrates how the bot PROACTIVELY collects Catalyst data")
print("through natural conversation before making introductions.")
print()
print("="*70)
print()

# Simulate conversation
conversation = [
    ("User", "Hey!"),
    ("Bot", "Hey! What brings you here?"),
    ("", ""),
    ("User", "I need a React developer"),
    ("Bot", "On it 🔍\n\nQuick question first: What are you working towards right now?"),
    ("", ""),
    ("User", "I'm trying to scale my startup to 1M users"),
    ("Bot", "[Extracts goal: 'scale startup to 1M users']"),
    ("Bot", "[Detects trajectory: 'rapid_growth']"),
    ("Bot", "That's fire 🔥\n\nHow long have you been in the game?"),
    ("", ""),
    ("User", "About 3 years of coding"),
    ("Bot", "[Detects trajectory: 'early_career' (3 years)]"),
    ("Bot", "Got it 👍\n\nSearching for React developers now..."),
    ("Bot", "[Uses Catalyst Algorithm with collected data]"),
    ("", ""),
    ("Bot", "Found someone perfect for you:\n\n**Sarah Chen**\nSenior Frontend Engineer\n\nWhy this match:\n- Recently learned React 8 months ago (perfect teacher!)\n- Wants to learn scaling (you can help!)\n- Both on rapid growth trajectories\n\nThis isn't just a hire — it's a catalyst pairing. 🚀"),
]

for speaker, message in conversation:
    if speaker and message:
        if speaker == "User":
            print(f"💬 {speaker}: {message}")
        else:
            print(f"🤖 {speaker}: {message}")
    else:
        print()  # Empty line for spacing

print()
print("="*70)
print("KEY DIFFERENCES FROM TRADITIONAL MATCHING")
print("="*70)
print()
print("Traditional Bot:")
print("  User: 'I need a React developer'")
print("  Bot: 'Here's Sarah, she knows React.'")
print()
print("Catalyst Bot:")
print("  User: 'I need a React developer'")
print("  Bot: 'On it 🔍 Quick question first: What are you working towards?'")
print("  User: 'Scaling my startup to 1M users'")
print("  Bot: 'That's fire 🔥 How long have you been in the game?'")
print("  User: 'About 3 years'")
print("  Bot: 'Found Sarah - recently learned React (perfect teacher!),")
print("       wants to learn scaling (you can help!), both rapid growth.'")
print()
print("="*70)
print("RESULT: Bidirectional value match, not just skill match")
print("="*70)
