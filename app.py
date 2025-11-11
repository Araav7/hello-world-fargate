import os
import json
import logging
from datetime import datetime
from flask import Flask, jsonify, request
from pythonjsonlogger import jsonlogger
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Create Flask app
app = Flask(__name__)

# Configure JSON logging
class CustomJsonFormatter(jsonlogger.JsonFormatter):
    def add_fields(self, log_record, record, message_dict):
        super(CustomJsonFormatter, self).add_fields(log_record, record, message_dict)
        log_record['timestamp'] = datetime.utcnow().isoformat()
        log_record['level'] = record.levelname
        log_record['logger'] = record.name

# Set up logger
logHandler = logging.StreamHandler()
formatter = CustomJsonFormatter('%(timestamp)s %(level)s %(name)s %(message)s')
logHandler.setFormatter(formatter)
logger = logging.getLogger()
logger.addHandler(logHandler)
logger.setLevel(logging.INFO)

# Log application startup
logger.info("Application starting up", extra={
    "event": "startup",
    "port": os.getenv("PORT", "8080")
})


@app.route('/')
def hello_world():
    """Main hello world endpoint"""
    logger.info("Hello world endpoint accessed", extra={
        "event": "request",
        "path": "/",
        "method": request.method,
        "remote_addr": request.remote_addr
    })
    
    return """
    <html>
        <head>
            <title>Hello World</title>
            <style>
                body {
                    font-family: Arial, sans-serif;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    height: 100vh;
                    margin: 0;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                }
                .container {
                    text-align: center;
                    background: white;
                    padding: 50px;
                    border-radius: 10px;
                    box-shadow: 0 10px 25px rgba(0,0,0,0.2);
                }
                h1 {
                    color: #333;
                    font-size: 48px;
                    margin: 0;
                }
                p {
                    color: #666;
                    font-size: 18px;
                    margin-bottom: 30px;
                }
                .button-group {
                    display: flex;
                    gap: 15px;
                    justify-content: center;
                    flex-wrap: wrap;
                }
                .btn {
                    padding: 12px 30px;
                    font-size: 16px;
                    font-weight: bold;
                    text-decoration: none;
                    color: white;
                    border-radius: 5px;
                    transition: all 0.3s ease;
                    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                }
                .btn:hover {
                    transform: translateY(-2px);
                    box-shadow: 0 6px 12px rgba(0,0,0,0.2);
                }
                .btn-primary {
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                }
                .btn-success {
                    background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
                }
                .btn-info {
                    background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
                }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Hello World! 👋</h1>
                <p>Your Flask app is running successfully!</p>
                <div class="button-group">
                    <a href="/api/hello" class="btn btn-primary">API Endpoint</a>
                    <a href="/health" class="btn btn-success">Health Check</a>
                    <a href="/info" class="btn btn-info">App Info</a>
                </div>
            </div>
        </body>
    </html>
    """


@app.route('/api/hello')
def api_hello():
    """JSON API endpoint"""
    logger.info("API hello endpoint accessed", extra={
        "event": "api_request",
        "path": "/api/hello",
        "method": request.method
    })
    
    response = {
        "message": "Hello World!",
        "timestamp": datetime.utcnow().isoformat(),
        "status": "success"
    }
    
    return jsonify(response)


@app.route('/health')
def health_check():
    """Health check endpoint for AWS Fargate"""
    logger.info("Health check endpoint accessed", extra={
        "event": "health_check",
        "path": "/health"
    })
    
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat()
    }), 200


@app.route('/info')
def info():
    """Information endpoint showing environment details"""
    logger.info("Info endpoint accessed", extra={
        "event": "info_request",
        "path": "/info"
    })
    
    return jsonify({
        "app": "Hello World Flask App",
        "version": "1.0.0",
        "python_version": os.sys.version,
        "environment": os.getenv("ENVIRONMENT", "development")
    })


@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    logger.warning("404 error", extra={
        "event": "error",
        "error_code": 404,
        "path": request.path
    })
    
    return jsonify({
        "error": "Not found",
        "path": request.path
    }), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    logger.error("500 error", extra={
        "event": "error",
        "error_code": 500,
        "error_message": str(error)
    })
    
    return jsonify({
        "error": "Internal server error"
    }), 500


if __name__ == '__main__':
    port = int(os.getenv("PORT", "8080"))
    logger.info("Starting Flask application", extra={
        "event": "startup_complete",
        "port": port
    })
    
    app.run(host='0.0.0.0', port=port, debug=False)

