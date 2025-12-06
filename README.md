# Catalyst Pairing Algorithm: Reciprocal Momentum Matching

**The foundation for the future of social networking.**

An AI-powered system that matches people based on bidirectional value and growth velocity, not just skills. This is how professional networking should work in the age of AI.

Built for Series Hax 25.

---

## Strategic Innovation: The Catalyst Pairing Algorithm

Traditional networking algorithms are one-dimensional: *Person A needs X → Person B has X.*

I built **Catalyst Pairing (Reciprocal Momentum Matching)**, a novel algorithm that orchestrates introductions based on bidirectional value and growth velocity. It matches people not just on what they need, but on the *chemistry of their combined momentum*.

### The 5 Dimensions of Catalyst Scoring

1.  **Reciprocal Value (30% weight)**
    *Does the requester have something the candidate implicitly needs?*
    I analyze candidate goals to find hidden value exchanges (e.g., a junior developer who can offer "fresh perspective on Gen Z trends" to a senior VP).

2.  **Complementarity & Teaching (25% weight)**
    *Recent learners are the best teachers.*
    The system tracks *when* a skill was acquired. A user who learned React 6 months ago (fresh struggle) is scored higher for a beginner than a 10-year veteran (expert blind spot).

3.  **Primary Value (25% weight)**
    *Standard skill matching.*
    Does the candidate possess the specific hard skills requested?

4.  **Trajectory Alignment (10% weight)**
    *Matching momentum, not just position.*
    The algorithm detects "Rapid Growth" states and pairs users to create compound velocity.

5.  **Serendipity (10% weight)**
    *Algorithmically engineered luck.*
    Surfaces "weird" high-potential matches—cross-domain problem solvers (e.g., "Healthcare Founder" matched with "Fintech Engineer" who solved the exact same regulatory scaling problem).

---

## Key Innovation: "Well-Connected Insider" Persona

I moved beyond generic AI assistants. The AI adopts a specific, distinct persona:
-   **Concise & punchy**: Responds like a busy, high-net-worth individual.
-   **Culturally aware**: Uses "On it," "That's fire," and industry vernacular appropriately.
-   **Anti-robot**: Explicitly programmed to avoid "How can I assist you today?" cliches.

---

## Technical Implementation

### Open-Source LLM Integration
-   **Groq API with Llama 3.3 70B**: Powers intent classification and response generation
-   **Zero vendor lock-in**: Open-source model ensures long-term viability
-   **Sub-200ms latency**: Fast inference for real-time conversations

### Event-Driven Architecture
-   **Confluent Kafka**: Real-time event streaming for message processing
-   **Series API**: iMessage/SMS integration with typing indicators and reactions
-   **Async processing**: Non-blocking message handling at scale

### Work Involved

**Knowledge Graph Expansion**
To validate the algorithm, I built a synthetic network of 200+ diverse profiles:
-   Global reach (London, Berlin, Singapore, Tel Aviv, Sydney)
-   Cross-industry coverage (Finance, Legal, Tech, Creative)
-   Rich metadata (`trajectory`, `recent_projects`, `skill_acquisition_dates`, `mentor_status`)

**Comprehensive Testing**
Built a robust E2E test suite covering:
-   Happy path intro requests (100% pass rate)
-   "No match" scenario handling
-   Network quality validation
-   Catalyst vs Traditional algorithm comparison

---

## Architecture

```
Kafka (Event Stream)
    ↓
Event Consumer (kafka_consumer.py)
    ↓
Intent Classifier (intent_classifier.py)
    ↓
Hybrid Matcher (Traditional + Catalyst Re-ranking)
    ↓
Response Generator (main.py)
    ↓
Series API Client (api_client.py)
```

## Setup & Usage

### 1. Installation
```bash
git clone https://github.com/manojmaheshwarjg/series_hax_25.git
cd series_hax_25
python -m venv venv
# Windows: venv\Scripts\activate
# Mac/Linux: source venv/bin/activate
pip install -r requirements.txt
```

### 2. Configuration
Copy `.env.example` to `.env` and populate:
```
KAFKA_BOOTSTRAP_SERVERS=...
API_KEY=...
```

### 3. Run Application
```bash
python src/main.py
```

### 4. Run Catalyst Algorithm Tests
```bash
python catalyst_pairing/tests/test_catalyst_pairing.py
```

## Project Structure

```
series_hax_25/
├── catalyst_pairing/           # [NEW] The Catalyst Algorithm
│   ├── catalyst_matcher.py     # 5-Dimension Scoring Engine
│   ├── hybrid_matcher.py       # Two-Stage Matcher
│   └── tests/                  # Algorithm Validation
├── src/
│   ├── network_generator.py    # Expanded Knowledge Graph
│   ├── response_engine.py      # New Persona Logic
│   └── ...
└── tests/                      # E2E Test Suite
```

---

**Built by Manoj Maheshwar Jagadeesan**
