from flask import Flask, jsonify, request
from flask_cors import CORS
from analytics_engine import initialize_analytics
import logging

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Initialize analytics engine
analytics_engine = initialize_analytics()

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@app.route('/api/v1/analytics/task-completion', methods=['GET'])
def get_task_completion_metrics():
    """
    Endpoint to retrieve task completion metrics
    
    Returns:
        JSON: Task completion analytics
    """
    try:
        # In a real scenario, you'd fetch tasks from a database or task management system
        sample_tasks = [
            {'status': 'completed', 'duration': 3600},
            {'status': 'in_progress', 'duration': 1800},
            {'status': 'completed', 'duration': 7200}
        ]
        metrics = analytics_engine.collect_task_completion_metrics(sample_tasks)
        return jsonify(metrics), 200
    except Exception as e:
        logger.error(f"Error retrieving task completion metrics: {e}")
        return jsonify({"error": "Unable to retrieve metrics"}), 500

@app.route('/api/v1/analytics/agent-performance', methods=['GET'])
def get_agent_performance():
    """
    Endpoint to retrieve agent performance metrics
    
    Returns:
        JSON: Agent performance analytics
    """
    try:
        # In a real scenario, you'd fetch agent logs from a database
        sample_agent_logs = [
            {'agent_name': 'CustomerSupportAgent', 'status': 'completed'},
            {'agent_name': 'SalesAgent', 'status': 'in_progress'},
            {'agent_name': 'CustomerSupportAgent', 'status': 'completed'}
        ]
        performance = analytics_engine.analyze_agent_performance(sample_agent_logs)
        return jsonify(performance), 200
    except Exception as e:
        logger.error(f"Error retrieving agent performance: {e}")
        return jsonify({"error": "Unable to retrieve performance data"}), 500

@app.route('/api/v1/analytics/executive-dashboard', methods=['GET'])
def get_executive_dashboard():
    """
    Endpoint to retrieve executive-level dashboard
    
    Returns:
        JSON: High-level business metrics and insights
    """
    try:
        dashboard = analytics_engine.generate_executive_dashboard()
        return jsonify(dashboard), 200
    except Exception as e:
        logger.error(f"Error generating executive dashboard: {e}")
        return jsonify({"error": "Unable to generate dashboard"}), 500

@app.errorhandler(404)
def not_found(error):
    """
    Custom 404 error handler
    
    Returns:
        JSON: Error message
    """
    return jsonify({"error": "Endpoint not found"}), 404

@app.errorhandler(500)
def server_error(error):
    """
    Custom 500 error handler
    
    Returns:
        JSON: Error message
    """
    return jsonify({"error": "Internal server error"}), 500

def create_analytics_app():
    """
    Create and configure Flask application for analytics
    
    Returns:
        Flask: Configured Flask application
    """
    return app

if __name__ == '__main__':
    analytics_app = create_analytics_app()
    # In production, use gunicorn or another WSGI server
    analytics_app.run(host='0.0.0.0', port=5000, debug=False)