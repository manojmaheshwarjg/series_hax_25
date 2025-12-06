"""
Demo: Context-Aware Conversational Bot
Shows how the bot handles vague answers with quirky follow-ups
"""

print("="*70)
print("DEMO: Context-Aware Conversational Bot")
print("="*70)
print()
print("Watch how the bot handles vague answers!")
print()
print("="*70)
print()

# Simulate conversation with vague answers
conversation = [
    ("User", "Hey!"),
    ("Bot", "Hey! What brings you here?"),
    ("", ""),
    ("User", "I need a React developer"),
    ("Bot", "On it 🔍\n\nQuick question first: What are you working towards right now?"),
    ("", ""),
    ("User", "stuff"),  # VAGUE!
    ("Bot", "[Detects vague answer]"),
    ("Bot", "C'mon, give me something to work with here 😅"),
    ("", ""),
    ("User", "I'm trying to scale my startup to 1M users"),
    ("Bot", "[Extracts goal: 'scale startup to 1M users']"),
    ("Bot", "That's fire 🔥\n\nHow long have you been in the game?"),
    ("", ""),
    ("User", "a while"),  # VAGUE!
    ("Bot", "[Detects vague answer]"),
    ("Bot", "How long we talking? 2 years? 10?"),
    ("", ""),
    ("User", "About 3 years"),
    ("Bot", "[Detects trajectory: 'early_career']"),
    ("Bot", "Got it 👍\n\nWhat's the hardest thing you've tackled recently?"),
    ("", ""),
    ("User", "idk"),  # VAGUE!
    ("Bot", "[Detects vague answer]"),
    ("Bot", "Even a small win counts!"),
    ("", ""),
    ("User", "I scaled our database to handle 10M requests/day"),
    ("Bot", "[Extracts problem solved]"),
    ("Bot", "Love it! Searching now with all this context..."),
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
print("KEY FEATURES")
print("="*70)
print()
print("✅ Detects vague answers: 'stuff', 'things', 'idk', 'a while'")
print("✅ Context-aware follow-ups based on what was asked")
print("✅ Quirky, playful tone (not annoying)")
print("✅ Maintains Well-Connected Insider persona")
print("✅ Progressively builds rich Catalyst profile")
print()
print("="*70)
print("RESULT: Natural conversation that collects quality data")
print("="*70)
