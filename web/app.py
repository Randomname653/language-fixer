"""
Flask Web UI for Language-Fixer
Simple dashboard for monitoring and controlling the media processing
"""
from flask import Flask, render_template, jsonify, request
import sqlite3
import os
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)

# Global state from main app
_main_app_state = {
    'status': 'idle',
    'last_scan': None,
    'current_file': None,
    'db_path': '/config/langfixer.db',
    'scan_callback': None,  # Will be set by main app
}

def set_app_state(state_dict):
    """Update app state from main application"""
    _main_app_state.update(state_dict)

def get_db_connection():
    """Get database connection"""
    db_path = _main_app_state.get('db_path', '/config/langfixer.db')
    if not os.path.exists(db_path):
        return None
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def get_stats():
    """Get processing statistics"""
    conn = get_db_connection()
    if not conn:
        return {
            'total_processed': 0,
            'total_failed': 0,
            'success_rate': 0,
            'last_24h': 0,
        }
    
    try:
        cursor = conn.cursor()
        
        # Total processed successfully
        cursor.execute("SELECT COUNT(*) as count FROM processed_files WHERE status = 'done'")
        total_processed = cursor.fetchone()['count']
        
        # Total failed
        cursor.execute("SELECT COUNT(*) as count FROM processed_files WHERE status = 'failed'")
        total_failed = cursor.fetchone()['count']
        
        # Success rate
        total = total_processed + total_failed
        success_rate = (total_processed / total * 100) if total > 0 else 0
        
        # Last 24 hours
        yesterday = (datetime.now() - timedelta(days=1)).isoformat()
        cursor.execute("SELECT COUNT(*) as count FROM processed_files WHERE last_attempt >= ?", (yesterday,))
        last_24h = cursor.fetchone()['count']
        
        return {
            'total_processed': total_processed,
            'total_failed': total_failed,
            'success_rate': round(success_rate, 1),
            'last_24h': last_24h,
        }
    finally:
        conn.close()

@app.route('/')
def index():
    """Dashboard page"""
    stats = get_stats()
    return render_template('index.html', 
                         stats=stats,
                         status=_main_app_state.get('status', 'idle'),
                         last_scan=_main_app_state.get('last_scan'),
                         current_file=_main_app_state.get('current_file'))

@app.route('/files')
def files():
    """Recent processed files page"""
    conn = get_db_connection()
    if not conn:
        return render_template('files.html', files=[])
    
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT file_path, status, last_attempt, failure_count
            FROM processed_files
            WHERE status = 'done'
            ORDER BY last_attempt DESC
            LIMIT 100
        """)
        files = cursor.fetchall()
        return render_template('files.html', files=files)
    finally:
        conn.close()

@app.route('/failed')
def failed():
    """Failed files page"""
    conn = get_db_connection()
    if not conn:
        return render_template('failed.html', files=[])
    
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT file_path, status, last_attempt, failure_count
            FROM processed_files
            WHERE status = 'failed'
            ORDER BY last_attempt DESC
        """)
        files = cursor.fetchall()
        return render_template('failed.html', files=files)
    finally:
        conn.close()

@app.route('/settings')
def settings():
    """Settings page (read-only config view)"""
    config = {
        'DRY_RUN': os.getenv('DRY_RUN', 'true'),
        'KEEP_AUDIO_LANGS': os.getenv('KEEP_AUDIO_LANGS', 'jpn,deu,eng,und'),
        'DEFAULT_AUDIO_LANG': os.getenv('DEFAULT_AUDIO_LANG', 'jpn'),
        'KEEP_SUBTITLE_LANGS': os.getenv('KEEP_SUBTITLE_LANGS', 'jpn,deu,eng'),
        'DEFAULT_SUBTITLE_LANG': os.getenv('DEFAULT_SUBTITLE_LANG', 'deu'),
        'REMOVE_AUDIO': os.getenv('REMOVE_AUDIO', 'auto'),
        'REMOVE_SUBTITLES': os.getenv('REMOVE_SUBTITLES', 'auto'),
        'RENAME_AUDIO_TRACKS': os.getenv('RENAME_AUDIO_TRACKS', 'true'),
        'RUN_INTERVAL_SECONDS': os.getenv('RUN_INTERVAL_SECONDS', '43200'),
        'WHISPER_API_URL': os.getenv('WHISPER_API_URL', 'Not configured'),
        'SONARR_URL': os.getenv('SONARR_URL', 'Not configured'),
        'RADARR_URL': os.getenv('RADARR_URL', 'Not configured'),
    }
    return render_template('settings.html', config=config)

@app.route('/api/status')
def api_status():
    """API endpoint for current status"""
    return jsonify({
        'status': _main_app_state.get('status', 'idle'),
        'last_scan': _main_app_state.get('last_scan'),
        'current_file': _main_app_state.get('current_file'),
    })

@app.route('/api/stats')
def api_stats():
    """API endpoint for statistics"""
    return jsonify(get_stats())

@app.route('/api/scan', methods=['POST'])
def api_scan():
    """API endpoint to trigger manual scan"""
    callback = _main_app_state.get('scan_callback')
    if callback:
        threading.Thread(target=callback, daemon=True).start()
        return jsonify({'success': True, 'message': 'Scan started'})
    return jsonify({'success': False, 'message': 'Scan callback not configured'}), 500

@app.route('/api/retry/<path:file_path>', methods=['POST'])
def api_retry(file_path):
    """API endpoint to retry a failed file"""
    conn = get_db_connection()
    if not conn:
        return jsonify({'success': False, 'message': 'Database not available'}), 500
    
    try:
        cursor = conn.cursor()
        cursor.execute("UPDATE processed_files SET status = 'pending', failure_count = 0 WHERE file_path = ?", (file_path,))
        conn.commit()
        return jsonify({'success': True, 'message': f'Reset {file_path} for retry'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        conn.close()

def run_web_ui(host='0.0.0.0', port=8080):
    """Run Flask web server"""
    app.run(host=host, port=port, debug=False, use_reloader=False)

if __name__ == '__main__':
    run_web_ui()
