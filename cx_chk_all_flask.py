# cx_chk_all_flask.py

from flask import Flask, request, jsonify, send_file
from cx_chk_all import cx_chk_all  # assumes this is in the same folder

app = Flask(__name__)

@app.route("/")
def serve_test_page():
    return send_file("cx_chk_all.html")

@app.route("/check", methods=["POST"])
def check_code():
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
        return jsonify({
            "valid": False,
            "errors": [{"message": f"Checker failed: {str(e)}"}]
        }), 500

if __name__ == "__main__":
    app.run(debug=True)
