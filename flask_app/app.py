"""
Enterprise Retail Analytics Engine
====================================
Flask Application - Main Entry Point
Usage: python app.py  (development)
       gunicorn -w 4 app:app  (production)
"""

import os
import sys
import logging
from datetime import datetime
from dotenv import load_dotenv
from flask import Flask, render_template, jsonify

# Vercel/serverless: run from flask_app so routes and templates resolve
_APP_DIR = os.path.dirname(os.path.abspath(__file__))
if _APP_DIR not in sys.path:
    sys.path.insert(0, _APP_DIR)
os.chdir(_APP_DIR)

# Fix Windows Unicode encoding for terminal output
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

load_dotenv()


def create_app() -> Flask:
    app = Flask(__name__)

    app.config["SECRET_KEY"]    = os.getenv("FLASK_SECRET_KEY", "dev-secret-change-in-production")
    app.config["DEBUG"]         = os.getenv("FLASK_DEBUG", "False").lower() == "true"
    app.config["JSON_SORT_KEYS"] = False

    # Logging (file handler skipped on Vercel — read-only filesystem)
    log_level = logging.DEBUG if app.config["DEBUG"] else logging.INFO
    handlers = [logging.StreamHandler()]
    if not os.getenv("VERCEL"):
        try:
            handlers.append(
                logging.FileHandler(
                    f"flask_app_{datetime.now().strftime('%Y%m%d')}.log",
                    encoding="utf-8",
                )
            )
        except OSError:
            pass
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
        handlers=handlers,
        force=True,
    )
    app.logger.setLevel(log_level)

    # Register Blueprints
    from routes.dashboard import dashboard_bp
    from routes.revenue   import revenue_bp
    from routes.products  import products_bp
    from routes.customers import customers_bp
    from routes.pivot     import pivot_bp
    from routes.ai_sql    import ai_sql_bp

    app.register_blueprint(dashboard_bp)
    app.register_blueprint(revenue_bp,   url_prefix="/revenue")
    app.register_blueprint(products_bp,  url_prefix="/products")
    app.register_blueprint(customers_bp, url_prefix="/customers")
    app.register_blueprint(pivot_bp,     url_prefix="/pivot")
    app.register_blueprint(ai_sql_bp,    url_prefix="/ai")

    # Error Handlers
    @app.errorhandler(404)
    def not_found(e):
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def server_error(e):
        app.logger.error("500 Error: %s", str(e))
        return render_template("errors/500.html"), 500

    # Health Check
    @app.route("/health")
    def health():
        return jsonify({
            "status": "healthy",
            "app":    "Enterprise Retail Analytics Engine",
            "time":   datetime.now().isoformat()
        })

    app.logger.info("Flask app created - Enterprise Retail Analytics Engine")
    return app


app = create_app()

if __name__ == "__main__":
    port = int(os.getenv("FLASK_PORT", 5000))
    app.logger.info("Starting server on http://0.0.0.0:%d", port)
    app.run(host="0.0.0.0", port=port, debug=app.config["DEBUG"])
