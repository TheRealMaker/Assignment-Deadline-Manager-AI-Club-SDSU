"""
api_bridge.py  —  HTTP wrapper around your Canvas + Gemini logic.
Run this instead of server.py when using the React frontend.

Usage:
    pip install flask flask-cors canvasapi google-genai python-dotenv
    python api_bridge.py
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from canvasapi import Canvas
from dotenv import load_dotenv
from google import genai
from google.genai import types
from datetime import datetime
import os

load_dotenv()

app = Flask(__name__)
CORS(app)

CANVAS_API_URL = os.getenv("CANVAS_API_URL")
gemini_client = genai.Client()


# ── helpers ───────────────────────────────────────────────────────────────────

def fetch_courses(token):
    canvas = Canvas(CANVAS_API_URL, token)
    courses = canvas.get_courses(enrollment_state="active", enrollment_type="student")
    return [
        {"name": c.name, "course_code": c.course_code, "id": c.id}
        for c in courses
        if hasattr(c, "name")
    ]


def fetch_assignments(token, course_id):
    """
    Returns FINISHED submissions (submitted_at is not None),
    matching the updated server.py logic.
    Includes submitted_at so the AI can rank difficulty.
    """
    canvas = Canvas(CANVAS_API_URL, token)
    course = canvas.get_course(course_id)
    user = canvas.get_user("self")

    assignments = list(course.get_assignments())
    assignment_map = {a.id: a for a in assignments}

    submissions = [a.get_submission(user) for a in assignments]

    # Only finished submissions (submitted_at is not None)
    finished = [s for s in submissions if s.submitted_at is not None]

    return [
        {
            "assignment_id": s.assignment_id,
            "name": assignment_map[s.assignment_id].name
                    if s.assignment_id in assignment_map else "Unknown",
            "due_at": assignment_map[s.assignment_id].due_at
                      if s.assignment_id in assignment_map else None,
            "submitted_at": s.submitted_at,
        }
        for s in finished
    ]


def ask_ai(assignments):
    """
    Updated prompt: ranks difficulty by how close submitted_at was to due_at.
    Shorter gap = harder assignment.
    """
    now = datetime.now()
    prompt = "\n".join(
        f"- {a['name']} (due: {a['due_at']}, submitted: {a.get('submitted_at', 'not submitted')})"
        for a in assignments
    )
    result = gemini_client.models.generate_content(
        model="gemini-2.5-flash",
        config=types.GenerateContentConfig(
            system_instruction=(
                "You are an online advisor for students attending San Diego State University. "
                "You will be given a list of their assignments within an individual course, and you will need to list which assignments "
                "take priority over others. Use the specific courses they give you, and order them from 1 to however many there are. "
                "The current date is " + str(now) + ". Thus, only talk about assignments that are due after this date. "
                "Place some emojis where you see fit. "
                "Rank the difficulty based on how long the submission was from the due date — "
                "estimate how long certain assignments may take based on the difference between submitted_at and due_date. "
                "If the difference is small, then it will likely be more difficult. "
                "Respond in a supportive demeanor, please."
            )
        ),
        contents=prompt,
    )
    return result.text


# ── routes ────────────────────────────────────────────────────────────────────

@app.route("/api/courses", methods=["POST"])
def courses():
    body = request.get_json()
    token = body.get("token", "")
    if not token:
        return jsonify({"error": "No token provided"}), 400
    try:
        return jsonify({"courses": fetch_courses(token)})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/assignments", methods=["POST"])
def assignments():
    body = request.get_json()
    token = body.get("token", "")
    course_id = body.get("course_id")
    if not token or not course_id:
        return jsonify({"error": "Missing token or course_id"}), 400
    try:
        return jsonify({"assignments": fetch_assignments(token, course_id)})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/ai", methods=["POST"])
def ai_question():
    body = request.get_json()
    assignments_data = body.get("assignments", [])
    if not assignments_data:
        return jsonify({"error": "No assignments provided"}), 400
    try:
        return jsonify({"ai_response": ask_ai(assignments_data)})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(port=5000, debug=True)
