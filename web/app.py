"""
Web Dashboard for Series AI Friend
Simple Flask app to visualize metrics and conversations
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from flask import Flask, render_template, jsonify
from flask_cors import CORS
from storage import intro_storage, conversation_storage, user_storage
from datetime import datetime
import json

app = Flask(__name__)
CORS(app)


@app.route('/')
def index():
    """Main dashboard page"""
    return render_template('dashboard.html')


@app.route('/api/metrics')
def get_metrics():
    """Get overall metrics"""
    all_intros = intro_storage.storage.read()

    total_intros = len(all_intros)
    completed = sum(1 for i in all_intros.values() if i.get('state') == 'complete')
    pending = sum(1 for i in all_intros.values() if i.get('state', '').startswith('pending'))
    rejected = sum(1 for i in all_intros.values() if i.get('state') == 'rejected')

    # Calculate success rate from processed outcomes
    successful = sum(1 for i in all_intros.values()
                    if i.get('outcome_processed') and i.get('outcome_score', 0) > 0.1)

    processed = sum(1 for i in all_intros.values() if i.get('outcome_processed'))

    success_rate = (successful / processed * 100) if processed > 0 else 0

    return jsonify({
        'total_introductions': total_intros,
        'completed': completed,
        'pending': pending,
        'rejected': rejected,
        'success_rate': f"{success_rate:.1f}%",
        'processed_outcomes': processed,
        'successful_outcomes': successful
    })


@app.route('/api/recent_intros')
def get_recent_intros():
    """Get recent introductions"""
    all_intros = intro_storage.storage.read()

    # Sort by created_at
    intros_list = list(all_intros.values())
    intros_list.sort(key=lambda x: x.get('created_at', ''), reverse=True)

    # Get top 10
    recent = intros_list[:10]

    # Format for display
    formatted = []
    for intro in recent:
        context = intro.get('context', {})

        formatted.append({
            'id': intro['id'],
            'requester_name': context.get('requester_name', 'Unknown'),
            'match_name': context.get('match_name', 'Unknown'),
            'state': intro['state'],
            'created_at': intro.get('created_at', ''),
            'outcome_score': intro.get('outcome_score'),
            'explanation': context.get('match_explanation', '')
        })

    return jsonify(formatted)


@app.route('/api/user_profiles')
def get_user_profiles():
    """Get user profile stats"""
    all_profiles = user_storage.storage.read()

    total_users = len(all_profiles)

    # Count profiles with different completeness
    complete = sum(1 for p in all_profiles.values()
                  if len(p.get('skills', [])) > 0 and p.get('location'))

    return jsonify({
        'total_users': total_users,
        'profiles_with_skills': sum(1 for p in all_profiles.values() if p.get('skills')),
        'profiles_with_location': sum(1 for p in all_profiles.values() if p.get('location')),
        'complete_profiles': complete
    })


@app.route('/api/conversation_activity')
def get_conversation_activity():
    """Get conversation activity"""
    logs = conversation_storage.storage.read()

    total_conversations = len(logs)
    total_messages = sum(len(conv) for conv in logs.values())

    # Recent activity (last 24 hours)
    from datetime import timedelta

    now = datetime.utcnow()
    recent_cutoff = now - timedelta(hours=24)

    recent_messages = 0
    for conv in logs.values():
        for msg in conv:
            try:
                msg_time = datetime.fromisoformat(msg['timestamp'])
                if msg_time >= recent_cutoff:
                    recent_messages += 1
            except:
                pass

    return jsonify({
        'total_conversations': total_conversations,
        'total_messages': total_messages,
        'messages_last_24h': recent_messages
    })


if __name__ == '__main__':
    print("Starting Series AI Friend Dashboard...")
    print("Open http://localhost:5000 in your browser")
    app.run(debug=True, host='0.0.0.0', port=5000)
