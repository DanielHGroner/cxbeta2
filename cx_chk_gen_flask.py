# cx_chk_gen_flask.py

import sys
import logging
import os

from flask import Flask, request, Response, jsonify, send_file, send_from_directory
from cx_chk_all import cx_chk_all
from cx_gen_src2html import cx_gen_src2html

app = Flask(__name__)

def setup_logging():
    log_level = os.environ.get('LOG_LEVEL', 'INFO').upper()
    log_level_num = getattr(logging, log_level, logging.INFO)
    logger = logging.getLogger()
    logger.setLevel(log_level_num)
    console_handler = logging.StreamHandler(sys.stderr)
    logger.addHandler(console_handler)
    return logger

logger = setup_logging()

@app.route("/")
def serve_test_page():
    app.logger.info('Entering serve_test_page()')
    return send_file("cx_chk_gen.html")

@app.route("/check", methods=["POST"])
def check_code():
    app.logger.info('Entering check_code()')
    data = request.get_json()
    source_code = data.get("code", "")

    if not source_code.strip():
        return jsonify({"valid": False, "errors": [{"message": "No code submitted."}]}), 400

    try:
        issues = cx_chk_all(source_code)
        if not issues:
            return jsonify({"valid": True, "errors": []})
        else:
            return jsonify({
                "valid": False,
                "errors": [
                    {
                        "line": getattr(err, "line", None),
                        "message": str(err)
                    }
                    for err in issues
                ]
            })
    except Exception as e:
        app.logger.info('check_code(): Exception')
        return jsonify({
            "valid": False,
            "errors": [{"message": f"Checker failed: {str(e)}"}]
        }), 500

@app.route("/generate", methods=["POST"])
def generate_html():
    app.logger.info('Entering generate_html()')
    data = request.get_json()
    source_code = data.get("code", "")

    if not source_code.strip():
        return jsonify({"error": "No code submitted."}), 400

    try:
        html = cx_gen_src2html(source_code)
        return jsonify({"html": html})
    except Exception as e:
        app.logger.exception('generate_html(): Exception')
        return jsonify({"error": f"HTML generation failed: {str(e)}"}), 500

@app.route("/render_visualizer", methods=["POST"])
def render_visualizer():
    app.logger.info('Entering render_visualizer()')
    source = request.form.get("code", "")
    try:
        html = cx_gen_src2html(source)
        return Response(html, mimetype='text/html')
    except Exception as e:
        app.logger.exception('render_visualizer(): Exception')
        return f"Error: {str(e)}", 400

@app.route("/p4damenu")
def serve_p4da_menu():
    app.logger.info('Entering serve_p4da_menu()')
    return send_from_directory("static", "cx_poc_menu.html")

if __name__ == "__main__":
    app.run(debug=True)
