"""
Learning Engine
Monitors post-introduction outcomes and improves matching over time
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from storage import intro_storage, conversation_storage
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class OutcomeSignal:
    """Signal about introduction outcome"""
    signal_type: str  # 'continued_conversation', 'meeting_scheduled', 'positive_feedback', etc.
    weight: float  # Weight of this signal (-0.5 to 0.35)
    confidence: float  # Confidence in detection (0.0 to 1.0)
    detected_at: str  # ISO timestamp


class OutcomeDetector:
    """Detects outcome signals from post-introduction interactions"""

    def __init__(self):
        # Signal weights from PRD
        self.signal_weights = {
            'continued_conversation': 0.20,  # 48+ hours, 5+ messages
            'meeting_scheduled': 0.35,  # Calendar keywords
            'positive_feedback': 0.30,  # Sentiment > 0.7
            'no_response': -0.15,  # 24h silence
            'one_sided_conversation': -0.20,  # 80/20 ratio
            'negative_feedback': -0.30,  # Sentiment < -0.5
            'contact_blocked': -0.50,  # System event
        }

        # Keywords for detecting different signals
        self.meeting_keywords = [
            'calendar', 'zoom', 'meet', 'coffee', 'lunch', 'dinner',
            'schedule', 'available', 'free', 'call', 'video chat',
            'monday', 'tuesday', 'wednesday', 'thursday', 'friday',
            'tomorrow', 'next week', 'this week'
        ]

        self.positive_keywords = [
            'great', 'awesome', 'perfect', 'excellent', 'helpful',
            'thanks', 'appreciate', 'glad', 'happy', 'love'
        ]

        self.negative_keywords = [
            'not a fit', 'not relevant', 'not helpful', 'waste',
            'disappointed', 'wrong', 'bad match'
        ]

    def analyze_intro_outcome(self, intro_id: str) -> List[OutcomeSignal]:
        """
        Analyze outcome of an introduction

        Args:
            intro_id: Introduction ID

        Returns:
            List of detected outcome signals
        """
        intro = intro_storage.get_intro(intro_id)

        if not intro or intro['state'] != 'complete':
            return []

        signals = []

        # Get group chat ID
        group_chat_id = intro.get('group_chat_id')
        if not group_chat_id:
            return []

        # Get conversation in group chat
        requester_phone = intro['requester']
        match_phone = intro['match']

        # Get messages from both parties
        requester_messages = self._get_user_messages(requester_phone, since_intro=intro['completed_at'])
        match_messages = self._get_user_messages(match_phone, since_intro=intro['completed_at'])

        all_messages = requester_messages + match_messages
        all_messages.sort(key=lambda m: m['timestamp'])

        # Detect signals
        signals.extend(self._detect_conversation_signals(all_messages, intro))
        signals.extend(self._detect_meeting_signals(all_messages))
        signals.extend(self._detect_sentiment_signals(all_messages))
        signals.extend(self._detect_engagement_signals(requester_messages, match_messages, intro))

        logger.info(f"Detected {len(signals)} outcome signals for intro {intro_id}")

        return signals

    def _get_user_messages(self, phone: str, since_intro: str) -> List[Dict]:
        """Get messages from a user since introduction"""
        conversation = conversation_storage.get_conversation(phone, limit=100)

        intro_time = datetime.fromisoformat(since_intro)

        messages = []
        for msg in conversation:
            msg_time = datetime.fromisoformat(msg['timestamp'])
            if msg_time >= intro_time:
                messages.append(msg)

        return messages

    def _detect_conversation_signals(self, messages: List[Dict], intro: Dict) -> List[OutcomeSignal]:
        """Detect continued conversation signals"""
        signals = []

        if not messages:
            # No response signal
            completed_at = datetime.fromisoformat(intro['completed_at'])
            time_since = (datetime.utcnow() - completed_at).total_seconds()

            if time_since > 86400:  # 24 hours
                signals.append(OutcomeSignal(
                    signal_type='no_response',
                    weight=self.signal_weights['no_response'],
                    confidence=0.9,
                    detected_at=datetime.utcnow().isoformat()
                ))

            return signals

        # Check for continued conversation (48+ hours, 5+ messages)
        first_msg_time = datetime.fromisoformat(messages[0]['timestamp'])
        last_msg_time = datetime.fromisoformat(messages[-1]['timestamp'])

        duration_hours = (last_msg_time - first_msg_time).total_seconds() / 3600

        if duration_hours >= 48 and len(messages) >= 5:
            signals.append(OutcomeSignal(
                signal_type='continued_conversation',
                weight=self.signal_weights['continued_conversation'],
                confidence=0.95,
                detected_at=datetime.utcnow().isoformat()
            ))

        return signals

    def _detect_meeting_signals(self, messages: List[Dict]) -> List[OutcomeSignal]:
        """Detect meeting scheduling signals"""
        signals = []

        for msg in messages:
            text = msg.get('message', '').lower()

            # Check for meeting keywords
            if any(keyword in text for keyword in self.meeting_keywords):
                signals.append(OutcomeSignal(
                    signal_type='meeting_scheduled',
                    weight=self.signal_weights['meeting_scheduled'],
                    confidence=0.8,
                    detected_at=msg['timestamp']
                ))
                break  # Only count once

        return signals

    def _detect_sentiment_signals(self, messages: List[Dict]) -> List[OutcomeSignal]:
        """Detect sentiment-based signals"""
        signals = []

        for msg in messages:
            text = msg.get('message', '').lower()

            # Check for positive feedback
            positive_count = sum(1 for kw in self.positive_keywords if kw in text)
            if positive_count >= 2:
                signals.append(OutcomeSignal(
                    signal_type='positive_feedback',
                    weight=self.signal_weights['positive_feedback'],
                    confidence=0.85,
                    detected_at=msg['timestamp']
                ))

            # Check for negative feedback
            if any(kw in text for kw in self.negative_keywords):
                signals.append(OutcomeSignal(
                    signal_type='negative_feedback',
                    weight=self.signal_weights['negative_feedback'],
                    confidence=0.9,
                    detected_at=msg['timestamp']
                ))

        return signals

    def _detect_engagement_signals(self, requester_msgs: List[Dict],
                                   match_msgs: List[Dict], intro: Dict) -> List[OutcomeSignal]:
        """Detect one-sided conversation signals"""
        signals = []

        total_msgs = len(requester_msgs) + len(match_msgs)

        if total_msgs < 3:
            return signals

        # Calculate ratio
        if total_msgs > 0:
            requester_ratio = len(requester_msgs) / total_msgs
            match_ratio = len(match_msgs) / total_msgs

            # Check for 80/20 imbalance
            if requester_ratio >= 0.8 or match_ratio >= 0.8:
                signals.append(OutcomeSignal(
                    signal_type='one_sided_conversation',
                    weight=self.signal_weights['one_sided_conversation'],
                    confidence=0.85,
                    detected_at=datetime.utcnow().isoformat()
                ))

        return signals


class LearningEngine:
    """Updates matching weights based on outcomes"""

    def __init__(self, matcher):
        self.matcher = matcher
        self.outcome_detector = OutcomeDetector()

        # Track metrics
        self.metrics = {
            'total_intros': 0,
            'successful_intros': 0,
            'failed_intros': 0,
            'patterns_updated': 0,
        }

    def process_completed_intros(self) -> Dict[str, int]:
        """
        Process all completed introductions and update weights

        Returns:
            Dictionary with processing stats
        """
        # Get completed intros from storage
        all_intros = intro_storage.storage.read()

        completed_intros = [
            intro for intro in all_intros.values()
            if intro.get('state') == 'complete'
        ]

        stats = {
            'processed': 0,
            'successful': 0,
            'failed': 0,
            'weights_updated': 0
        }

        for intro in completed_intros:
            # Check if already processed
            if intro.get('outcome_processed'):
                continue

            # Analyze outcome
            signals = self.outcome_detector.analyze_intro_outcome(intro['id'])

            if not signals:
                continue

            # Calculate overall outcome score
            outcome_score = sum(s.weight * s.confidence for s in signals)

            # Determine if success or failure
            is_success = outcome_score > 0.1
            is_failure = outcome_score < -0.1

            if is_success:
                stats['successful'] += 1
                self._update_weights_for_success(intro, outcome_score)
                stats['weights_updated'] += 1

            elif is_failure:
                stats['failed'] += 1
                self._update_weights_for_failure(intro, abs(outcome_score))
                stats['weights_updated'] += 1

            # Mark as processed
            intro_storage.update_intro_state(
                intro['id'],
                intro['state'],
                outcome_processed=True,
                outcome_score=outcome_score,
                outcome_signals=[s.__dict__ for s in signals]
            )

            stats['processed'] += 1

        logger.info(f"Processed {stats['processed']} intros: "
                   f"{stats['successful']} successful, {stats['failed']} failed")

        # Update metrics
        self.metrics['total_intros'] += stats['processed']
        self.metrics['successful_intros'] += stats['successful']
        self.metrics['failed_intros'] += stats['failed']
        self.metrics['patterns_updated'] += stats['weights_updated']

        return stats

    def _update_weights_for_success(self, intro: Dict, magnitude: float):
        """Update pattern weights for successful introduction"""
        context = intro.get('context', {})
        requirements = context.get('requirements', {})

        # Generate pattern key
        pattern_key = self._generate_pattern_key(intro)

        # Update matcher's pattern weights
        self.matcher.update_pattern_weight(pattern_key, 'success', magnitude)

        logger.info(f"Updated weights for successful intro: {pattern_key}")

    def _update_weights_for_failure(self, intro: Dict, magnitude: float):
        """Update pattern weights for failed introduction"""
        pattern_key = self._generate_pattern_key(intro)

        # Update matcher's pattern weights
        self.matcher.update_pattern_weight(pattern_key, 'failure', magnitude)

        logger.info(f"Updated weights for failed intro: {pattern_key}")

    def _generate_pattern_key(self, intro: Dict) -> str:
        """Generate pattern key from introduction"""
        context = intro.get('context', {})
        requirements = context.get('requirements', {})

        parts = []

        if 'role' in requirements:
            role = requirements['role']
            if isinstance(role, list):
                role = role[0]
            parts.append(f"role:{role}")

        if 'seniority' in requirements:
            parts.append(f"seniority:{requirements['seniority']}")

        match_name = context.get('match_name', '')
        if match_name:
            # This is simplified - in production would use more match attributes
            parts.append(f"match_type:professional")

        return "|".join(sorted(parts))

    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get summary of learning metrics"""
        total = self.metrics['total_intros']
        successful = self.metrics['successful_intros']

        success_rate = (successful / total * 100) if total > 0 else 0

        return {
            'total_intros_processed': total,
            'successful_intros': successful,
            'failed_intros': self.metrics['failed_intros'],
            'success_rate': f"{success_rate:.1f}%",
            'patterns_updated': self.metrics['patterns_updated'],
            'current_pattern_weights': self.matcher.pattern_weights
        }

    def should_run_learning_cycle(self) -> bool:
        """Determine if learning cycle should run"""
        # Run every 6 hours or after 10 new completed intros
        # For now, simplified check
        return True


if __name__ == "__main__":
    # Test learning engine
    logging.basicConfig(level=logging.INFO)

    from matcher import Matcher

    matcher = Matcher()
    learning_engine = LearningEngine(matcher)

    # Process completed intros
    stats = learning_engine.process_completed_intros()

    print(f"\nProcessing stats: {stats}")

    # Get metrics
    metrics = learning_engine.get_metrics_summary()
    print(f"\nMetrics: {metrics}")
