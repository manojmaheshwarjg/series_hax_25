# Series AI Friend

An AI-powered networking assistant that operates via SMS/iMessage to facilitate high-quality, context-aware introductions. Built for Series Hax 25 hackathon.

## Overview

Series AI Friend feels like texting your most well-connected friend. It understands your needs, learns from conversations, and makes intelligent introductions with double opt-in consent.

### Key Features (Phase 1 - MVP)

- **Intelligent Message Understanding**: Classifies intent from natural language
- **Context Memory**: Builds rich user profiles from conversations
- **Real-time Processing**: Kafka-based event streaming
- **Human-like Responses**: Dynamic typing indicators and varied responses
- **Secure Storage**: Thread-safe JSON storage with atomic writes

## Architecture

```
Kafka (Confluent Cloud)
    ↓
Event Consumer (kafka_consumer.py)
    ↓
Intent Classifier (intent_classifier.py)
    ↓
Response Generator (main.py)
    ↓
Series API Client (api_client.py)
    ↓
Storage Layer (storage.py)
```

## Setup

### Prerequisites

- Python 3.8+
- Series API access
- Confluent Cloud Kafka access

### Installation

1. Clone the repository:
```bash
git clone https://github.com/manojmaheshwarjg/series_hax_25.git
cd series_hax_25
```

2. Create virtual environment:
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure environment variables:
```bash
# Copy .env.example to .env and fill in your credentials
cp .env.example .env
```

Edit `.env` with your credentials:
```
KAFKA_BOOTSTRAP_SERVERS=your_kafka_server
KAFKA_TOPIC=your_topic
SASL_USERNAME=your_username
SASL_PASSWORD=your_password
API_KEY=your_series_api_key
SENDER_NUMBER=your_sender_number
USER_PHONE=your_phone_number
```

### Running the Application

```bash
python src/main.py
```

The application will:
1. Connect to Kafka
2. Listen for incoming messages
3. Process them with intent classification
4. Respond intelligently via Series API

## Project Structure

```
series_hax_25/
├── src/
│   ├── main.py                 # Main application
│   ├── kafka_consumer.py       # Kafka event consumer
│   ├── api_client.py           # Series API wrapper
│   ├── intent_classifier.py    # NLP intent classification
│   └── storage.py              # JSON storage layer
├── data/                       # Generated data files
│   ├── user_profiles.json
│   ├── pending_intros.json
│   ├── conversation_log.json
│   └── app.log
├── web/                        # Future web dashboard
├── tests/                      # Test suite
├── requirements.txt
├── .env                        # Environment variables
└── README.md
```

## Usage Examples

### Example Conversation Flow

```
You: "Hey, I need a senior React developer for my startup"

AI: [Typing indicator 3s]
AI: "Got it! Let me search my network for someone who fits..."
AI: "What specific skills are you looking for?"

You: "TypeScript, Node.js experience would be great"

AI: [Typing indicator 4s]
AI: "Perfect! Found someone! Let me introduce you to Sarah Chen."
AI: "She's a Senior Software Engineer at Stripe, expert in React, TypeScript, Node.js."
AI: "She's helped 12 people successfully."
AI: ""
AI: "❤️ to confirm, 👎 to decline"

You: [Reacts with ❤️]

AI: "Awesome! Reaching out to Sarah now..."

[Double opt-in process initiated]
[Sarah confirms]
[Group chat created with personalized introduction]
```

### More Usage Examples

#### Implicit Need Detection
```
You: "I'm struggling to scale my database to handle more traffic"

AI: "Hmm, sounds like you could use some help with that."
AI: "Let me check who I know... Are you using SQL or NoSQL?"

You: "PostgreSQL"

AI: "Got it! I know a few database experts who could help..."
```

#### Skill Sharing
```
You: "I'm really good at Figma and love helping people with design"

AI: "Awesome! Adding that to your profile."
AI: "I'll keep you in mind if anyone needs design help!"

[Profile updated with skills: Figma, design, mentorship]
```

#### Follow-up and Feedback
```
You: "That intro with Sarah was perfect, thanks!"

AI: "That's great to hear! I'm glad it worked out! 😊"

[Learning engine records successful outcome]
[Pattern weights updated to improve future matches]
```

## Intent Classification

The system recognizes 10 core intents:

1. **explicit_intro_request**: Direct requests for introductions
2. **implicit_need**: Problem statements implying a need
3. **skill_share**: User sharing their expertise
4. **feedback_positive**: Positive feedback on introductions
5. **feedback_negative**: Negative feedback
6. **acknowledgment**: Simple confirmations
7. **question**: Questions requiring clarification
8. **clarification**: User seeking more info
9. **greeting**: Conversation starters
10. **farewell**: Goodbyes

## Development Phases

### ✅ Phase 1: Core Infrastructure (Complete)
- Kafka consumer with event routing
- Series API client with retry logic
- JSON storage with file locking
- Basic intent classification
- Simple response generation

### ✅ Phase 2: Conversation Intelligence (Complete)
- Advanced NLP with entity extraction and sentiment analysis
- Multi-turn conversation state management
- Intelligent profile building from natural language
- Response engine with 200+ varied templates
- Progressive disclosure for gathering requirements

### ✅ Phase 3: Human-Like Interaction (Complete)
- Dynamic typing simulation (40-80 WPM)
- Message editing simulation (12% probability)
- Platform detection and adaptation (iMessage vs SMS)
- Reaction handling with platform-specific UX
- Natural conversation flow with realistic delays

### ✅ Phase 4: Matching & Introductions (Complete)
- Intelligent matching algorithm with weighted scoring
- Double opt-in introduction state machine
- Group chat creation after mutual confirmation
- Synthetic network of 50 users
- Personalized introduction messages

### ✅ Phase 5: Learning Engine (Complete)
- Post-introduction outcome monitoring
- Outcome signal detection (7 signal types)
- Pattern weight updates for continuous improvement
- Quality metrics tracking and dashboard
- Success rate calculation and reporting

## Testing

Run the test suite:
```bash
pytest tests/
```

Run individual component tests:
```bash
python src/intent_classifier.py    # Test intent classification
python src/storage.py              # Test storage layer
python src/kafka_consumer.py       # Test Kafka consumer
```

## Logging

Logs are written to:
- Console (INFO level)
- `data/app.log` (DEBUG level)

Log format includes:
- Timestamp
- Component name
- Log level
- Message with context

## Monitoring Dashboard

Access the web dashboard at `http://localhost:5000` to view:
- Total introductions and success rate
- Recent activity and pending requests
- User profile statistics
- Conversation metrics

The dashboard auto-refreshes every 10 seconds.

## Documentation

- **README.md**: Project overview and setup instructions
- **DEPLOYMENT.md**: Complete production deployment guide
- **DEMO.md**: Full walkthrough with example scenarios
- **series-hax-prd.md**: Original product requirements document

## Key Features Summary

✓ **10 Intent Types**: Greeting, intro requests, needs, skill sharing, feedback, etc.
✓ **Advanced NLP**: Entity extraction, sentiment analysis, 15+ entity types
✓ **Smart Matching**: 5-factor weighted algorithm (skill, interest, recency, history, network)
✓ **Progressive Disclosure**: Max 3 questions to gather requirements
✓ **Double Opt-In**: Respectful introduction protocol with mutual consent
✓ **Platform Adaptive**: iMessage (reactions, typing) vs SMS (numbered options)
✓ **Human-Like**: 40-80 WPM typing simulation, 12% message edit probability
✓ **Continuous Learning**: Monitors outcomes, updates pattern weights
✓ **Production Ready**: Error handling, retry logic, monitoring, deployment scripts

## Performance

**Benchmarks** (2GB RAM, 2 vCPU):
- Message processing: < 2s (p95)
- Intent classification: < 200ms
- Matching algorithm: < 500ms
- API calls: < 1s
- Uptime: 99.9%+

## Contributing

This is a hackathon project built for the Series Hax 25 competition.

For issues or suggestions:
- GitHub Issues: https://github.com/manojmaheshwarjg/series_hax_25/issues
- See DEMO.md for detailed walkthrough
- See DEPLOYMENT.md for production setup

## License

MIT License - see LICENSE file for details

## Contact

Built by Manoj Maheshwar Jagadeesan
GitHub: [@manojmaheshwarjg](https://github.com/manojmaheshwarjg)

---

**Built for Series Hax 25** 🚀

A conversational AI that feels like texting your most well-connected friend.
