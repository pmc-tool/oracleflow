"""Real-time WebSocket events and SSE stream for OracleFlow.

Provides two real-time transport layers:
1. WebSocket via Flask-SocketIO (for clients with socket.io-client)
2. Server-Sent Events (SSE) via native EventSource (no npm dependency)

The SSE approach is preferred for the frontend since it requires no
additional npm packages — the browser's native EventSource API is sufficient.
"""

import json
import logging
import time
import threading
from collections import deque
from datetime import datetime, timezone

from flask import Blueprint, Response, request
from flask_socketio import SocketIO, emit, join_room

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# WebSocket layer (Flask-SocketIO)
# ---------------------------------------------------------------------------

socketio = SocketIO(cors_allowed_origins="*")


def init_realtime(app):
    """Initialize both WebSocket and SSE on the Flask app."""
    socketio.init_app(app)

    # Register SSE blueprint
    app.register_blueprint(sse_bp, url_prefix='/api/events')

    logger.info("Real-time layer initialized (WebSocket + SSE)")


@socketio.on('connect')
def handle_connect():
    """Client connected via WebSocket."""
    logger.debug("WebSocket client connected: %s", request.sid)


@socketio.on('subscribe')
def handle_subscribe(data):
    """Client subscribes to an org-specific room."""
    org_id = data.get('org_id')
    if org_id:
        join_room(f'org_{org_id}')
        logger.debug("Client %s joined room org_%s", request.sid, org_id)
    user_id = data.get('user_id')
    if user_id:
        join_room(f'user_{user_id}')


def broadcast_signal(signal_data, org_id=None):
    """Broadcast a new signal to connected WebSocket clients and SSE subscribers."""
    if org_id:
        socketio.emit('new_signal', signal_data, room=f'org_{org_id}')
    else:
        socketio.emit('new_signal', signal_data)  # Global broadcast

    # Also push to SSE event buffer
    _push_sse_event('signal', signal_data)


def broadcast_notification(notification_data, user_id):
    """Broadcast notification to a specific user."""
    socketio.emit('notification', notification_data, room=f'user_{user_id}')
    _push_sse_event('notification', notification_data)


def broadcast_chaos_update(chaos_data):
    """Broadcast chaos index update to all clients."""
    socketio.emit('chaos_update', chaos_data)
    _push_sse_event('chaos_update', chaos_data)


# ---------------------------------------------------------------------------
# SSE layer (Server-Sent Events) -- no npm dependency needed on frontend
# ---------------------------------------------------------------------------

sse_bp = Blueprint('of_sse', __name__)

# Thread-safe ring buffer of recent events (kept small: last 200 events)
_sse_buffer = deque(maxlen=200)
_sse_lock = threading.Lock()
_sse_event_id = 0


def _push_sse_event(event_type, data):
    """Add an event to the SSE buffer for streaming to clients."""
    global _sse_event_id
    with _sse_lock:
        _sse_event_id += 1
        event = {
            'id': _sse_event_id,
            'type': event_type,
            'data': data,
            'timestamp': datetime.now(timezone.utc).isoformat(),
        }
        _sse_buffer.append(event)


@sse_bp.route('/stream')
def event_stream():
    """SSE endpoint: streams real-time signals, notifications, and chaos updates.

    Frontend usage:
        const evtSource = new EventSource('/api/events/stream')
        evtSource.onmessage = (event) => {
            const data = JSON.parse(event.data)
            // data.type is 'signal', 'notification', or 'chaos_update'
        }
    """
    last_id_header = request.headers.get('Last-Event-ID', '0')
    try:
        last_id = int(last_id_header)
    except (ValueError, TypeError):
        last_id = 0

    def generate():
        seen_id = last_id
        while True:
            # Snapshot the buffer under lock
            with _sse_lock:
                events = list(_sse_buffer)

            # Send any events newer than what the client has seen
            new_events = [e for e in events if e['id'] > seen_id]
            for evt in new_events:
                seen_id = evt['id']
                payload = json.dumps({
                    'type': evt['type'],
                    'data': evt['data'],
                    'timestamp': evt['timestamp'],
                })
                yield f"id: {evt['id']}\ndata: {payload}\n\n"

            # Sleep briefly before checking for more events
            time.sleep(3)

    return Response(
        generate(),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no',
            'Connection': 'keep-alive',
        },
    )
