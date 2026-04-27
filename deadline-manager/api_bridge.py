"""
api_bridge.py  —  HTTP wrapper around your Canvas + Gemini logic.
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from canvasapi import Canvas
from dotenv import load_dotenv
from google import genai
from google.genai import types
from datetime import datetime, timezone
import os

load_dotenv()

# Middleware
app = Flask(__name__)
CORS(app)

CANVAS_API_URL = os.getenv("CANVAS_API_URL")
gemini_client = genai.Client()

session_store = {}


def fetch_courses(token):
    canvas = Canvas(CANVAS_API_URL, token)
    courses = canvas.get_courses(enrollment_state="active", enrollment_type="student")
    return [
        {"name": c.name, "course_code": c.course_code, "id": c.id}
        # Monitors the courses found and names them, even if buggy
        for c in courses
        if hasattr(c, "name")
    ]


def estimate_difficulty(pending_name, finished):
    """
    Looks through finished assignments for name similarity.
    Returns a difficulty label based on the average submission gap of similar past work.
    """
    pending_words = set(pending_name.lower().split())
    ignore = {"the", "a", "an", "of", "and", "or", "for", "to", "in", "on", "with"}

# Obtains data from already complete assignments such as when it was due and finds the gap
    similar = []
    for f in finished:
        if not f["due_at"] or not f["submitted_at"] or f["due_at"] == "No due date":
            continue
        finished_words = set(f["name"].lower().split())
        overlap = (pending_words & finished_words) - ignore
        if not overlap:
            continue
        due = datetime.fromisoformat(f["due_at"].replace("Z", "+00:00"))
        sub = datetime.fromisoformat(str(f["submitted_at"]).replace("Z", "+00:00"))
        gap_hours = (due - sub).total_seconds() / 3600
        similar.append(gap_hours)

    if not similar:
        return {"label": "Unknown", "cls": "diff-unknown"}

# Uses the gap of time before assignments were due to leverage difficulty for assignments
    avg_gap = sum(similar) / len(similar)
    if avg_gap < 0:
        return {"label": "Late", "cls": "diff-late"}
    if avg_gap < 6:
        return {"label": "Hard", "cls": "diff-hard"}
    if avg_gap < 48:
        return {"label": "Medium", "cls": "diff-medium"}
    return {"label": "Easy", "cls": "diff-easy"}

# Fetches assignments condensing all the functions we used earlier
def fetch_assignments(token, course_id):
    canvas = Canvas(CANVAS_API_URL, token)
    course = canvas.get_course(course_id)
    user = canvas.get_user("self")

    assignments = list(course.get_assignments())
    assignment_map = {a.id: a for a in assignments}
    submissions = [a.get_submission(user) for a in assignments]

    now = datetime.now(timezone.utc)

    # Build finished first so estimate_difficulty can use it
    finished = []
    for s in submissions:
        a = assignment_map.get(s.assignment_id)
        if not a or s.submitted_at is None:
            continue
        finished.append({
            "assignment_id": s.assignment_id,
            "name": a.name,
            "due_at": a.due_at or "No due date",
            "submitted_at": s.submitted_at,
        })

    # Pending not submitted, due date in the future OR no due date at all
    pending = []
    for s in submissions:
        a = assignment_map.get(s.assignment_id)
        if not a:
            continue
        if s.submitted_at is not None:
            continue

        if a.due_at:
            due = datetime.fromisoformat(a.due_at.replace("Z", "+00:00"))
            if due <= now:
                continue

        pending.append({
            "assignment_id": s.assignment_id,
            "name": a.name,
            "due_at": a.due_at or "No due date",
            "submitted_at": None,
            "difficulty": estimate_difficulty(a.name, finished),
        })

    return {"pending": pending, "finished": finished}

# Grabs the pending and already completed assignments to make predictions about upcoming assignments
def ask_ai(pending, finished, history):
    now = datetime.now()

    pending_prompt = "\n".join(
        f"- {a['name']} (due: {a['due_at']}, estimated difficulty: {a.get('difficulty', {}).get('label', 'Unknown')})"
        for a in pending
    ) or "None"

    finished_prompt = "\n".join(
        f"- {a['name']} (due: {a['due_at']}, submitted: {a['submitted_at']})"
        for a in finished
    ) or "None"

    context_block = (
        f"UPCOMING (needs prioritization):\n{pending_prompt}\n\n"
        f"COMPLETED (use as difficulty reference):\n{finished_prompt}"
    )

    messages = [
        {"role": "user", "parts": [{"text": context_block}]},
        {"role": "model", "parts": [{"text": "Got it! I have your assignment data. What would you like to know?"}]},
    ]

# History from the messages
    for entry in history:
        messages.append({
            "role": "user" if entry["role"] == "user" else "model",
            "parts": [{"text": entry["content"]}]
        })

# Actual LLM function that helps generate the response from the AI.
    result = gemini_client.models.generate_content(
        model="gemini-2.5-flash",
        config=types.GenerateContentConfig(
            system_instruction=(
                "You are an online advisor for students attending San Diego State University. "
                "You will be given two lists: upcoming assignments that need to be prioritized, "
                "and completed assignments to use as a difficulty reference. "
                "Each upcoming assignment has an estimated difficulty based on similar past work. "
                "Rank the UPCOMING assignments from most to least urgent, numbered 1 to however many there are. "
                "If an assignment has no due date, list it at the end and note that no deadline was set. "
                "Use both the estimated difficulty and the completed assignments to inform your ranking. "
                "The current date is " + str(now) + ". "
                "Only discuss upcoming assignments. "
                "Place some emojis where you see fit. "
                "Respond in a supportive demeanor, please."
            )
        ),
        contents=messages,
    )
    return result.text


# Routes

# Course content is obtained and is used to obtain assignment data later.
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

# Grab all information in relation to the data assignments
@app.route("/api/assignments", methods=["POST"])
def assignments():
    body = request.get_json()
    token = body.get("token", "")
    course_id = body.get("course_id")
    if not token or not course_id:
        return jsonify({"error": "Missing token or course_id"}), 400
    try:
        return jsonify(fetch_assignments(token, course_id))
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Ask a question for the AI so it can respond to it.
@app.route("/api/ai", methods=["POST"])
def ai_question():
    body = request.get_json()
    token = body.get("token", "")
    pending = body.get("pending", [])
    finished = body.get("finished", [])
    user_message = body.get("message", "")

    if not pending and not finished:
        return jsonify({"error": "No assignments provided"}), 400

    if token not in session_store:
        session_store[token] = []

    session_store[token].append({"role": "user", "content": user_message})

    try:
        response_text = ask_ai(pending, finished, session_store[token])
        session_store[token].append({"role": "assistant", "content": response_text})
        return jsonify({"ai_response": response_text})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(port=5000, debug=True)