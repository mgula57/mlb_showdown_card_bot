import os
from flask import Flask, jsonify, send_from_directory, request
from flask_cors import CORS
from dotenv import load_dotenv
from config import Config

# LOAD ENVIRONMENT VARIABLES
load_dotenv()

# ----------------------------------------------------------
# MARK: - APP CONFIG
# ----------------------------------------------------------

app = Flask(__name__, static_folder='frontend/dist', static_url_path='/static')

# CORS SETUP FOR DEVELOPMENT
if Config.FLASK_ENV != 'production':
    CORS(app, resources={r"/*": {"origins": Config.FRONTEND_ORIGIN}})

# ----------------------------------------------------------
# MARK: - API
# ----------------------------------------------------------

# Register blueprints
from mlb_showdown_bot.api.cards import cards_bp
from mlb_showdown_bot.api.search import search_bp
from mlb_showdown_bot.api.card_db import card_db_bp
from mlb_showdown_bot.api.feature_status import feature_status_bp
from mlb_showdown_bot.api.seasons import seasons_bp

app.register_blueprint(cards_bp, url_prefix='/api')
app.register_blueprint(search_bp, url_prefix='/api')
app.register_blueprint(card_db_bp, url_prefix='/api')
app.register_blueprint(feature_status_bp, url_prefix='/api')
app.register_blueprint(seasons_bp, url_prefix='/api')

@app.route('/static/output/<path:filename>')
def serve_output_files(filename):
    """Serve generated card images"""
    
    # Check if file exists in static/output directory
    file_path = os.path.join('static', 'output', filename)
    if os.path.exists(file_path):
        return send_from_directory(os.path.join('static', 'output'), filename)
    
    # Fallback to output directory
    if os.path.exists(os.path.join('output', filename)):
        return send_from_directory('output', filename)
    
    return "File not found", 404

@app.errorhandler(413)
def too_large(e):
    """Handle file too large error"""
    return jsonify({
        'card': None,
        'error': 'File is too large',
        'error_for_user': 'The uploaded image is too large. Please use an image smaller than 16MB.'
    }), 413

@app.after_request
def add_cache_headers(resp):
    p = request.path

    # Set icons rarely change -> cache aggressively
    if p.startswith("/images/"):
        resp.headers["Cache-Control"] = "public, max-age=31536000, immutable"
        return resp

    return resp

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve_react(path):
    """Serve the react app within Flask"""
    
    # Check if we're in development and dist folder doesn't exist
    if not os.path.exists(app.static_folder):
        return f"""
        <h1>Frontend not built</h1>
        <p>Static folder looking for: {app.static_folder}</p>
        """
    
    # Handle API routes
    if path.startswith('api/'):
        return "API endpoint not found", 404
    
    # Handle static assets
    if path and os.path.exists(os.path.join(app.static_folder, path)):
        return send_from_directory(app.static_folder, path)
    
    # Serve index.html for all other routes
    try:
        return send_from_directory(app.static_folder, 'index.html')
    except FileNotFoundError:
        return "index.html not found in dist folder."

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug_mode = os.environ.get('FLASK_ENV') != 'production'    
    app.run(host='0.0.0.0', port=port, debug=debug_mode)
