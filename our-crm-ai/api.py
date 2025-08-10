from flask import Flask, request, jsonify
import sys
import os

# Add project root to path to allow sibling imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), ".")))
from agents.pm_agent import handle_command

app = Flask(__name__)

@app.route("/api/command", methods=["POST"])
def command():
    """
    API endpoint to receive and execute natural language commands.
    """
    data = request.get_json()
    if not data or "command" not in data:
        return jsonify({"error": "Invalid request. 'command' field is required."}), 400

    command_text = data["command"]

    try:
        # Call the refactored PM agent logic
        result = handle_command(command_text)
        return jsonify({"response": result})
    except Exception as e:
        return jsonify({"error": f"An unexpected error occurred: {e}"}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
