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

### Example Conversation

```
You: "Hey, I need a senior React developer for my startup"

AI: [Typing indicator 3s]
AI: "Got it! Let me search my network for someone who fits..."

[AI classifies intent: explicit_intro_request]
[Extracts entities: role=developer, technology=react, seniority=senior]
[Updates your profile with this need]
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

## Contributing

This is a hackathon project. For the Series Hax 25 competition.

## License

MIT License - see LICENSE file for details

## Contact

Built by Manoj Maheshwar Jagadeesan
GitHub: [@manojmaheshwarjg](https://github.com/manojmaheshwarjg)
