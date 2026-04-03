import socket
import os
import json
from canvasapi import Canvas
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()
print("Loaded .env values:")
print("CANVAS_API_URL:", os.getenv("CANVAS_API_URL"))

# Client will pull from the SDSU local Canvas URL to use for collecting data
CANVAS_API_URL = os.getenv("CANVAS_API_URL")
token_saved = ""

# Client will pull API Key from the environmental variable
client = genai.Client()

# Ask AI a question to assist with Canvas
def ask_ai_question(instructions, response):
    response = client.models.generate_content(
        model="gemini-3-flash-preview", config = types.GenerateContentConfig(system_instruction = instructions),
        contents = response)
    
    print(response.text)

# Retrieve our global token
def getToken(token_value):
    global token_saved
    token_saved = token_value
    print(f"Token received and saved: {token_saved}")  # Added print
    return f"Token '{token_saved}' saved successfully."

# Fetch specific Canvas data from the user token so they know what they're receiving. 
def fetch_canvas_data():
    if not token_saved:
        return "Canvas token never acquired, please retry."
    if not CANVAS_API_URL:
        return "Canvas API is not correct, please change."
    canvas = Canvas(CANVAS_API_URL, token_saved)

    user = fetch_user_data(canvas)

    # Grab courses that are currently active for the user
    courses = fetch_courses_data(canvas)

    # Grab all the submission dates for each
    assignments = fetch_assignment_data(courses)

    submissions = fetch_submission_time(assignments, user)

    unlock_dates = fetch_unlock_date(assignments)

    return courses

def fetch_user_data(canvas_data):
    user = canvas_data.get_user('self')
    return user

def fetch_courses_data(canvas):
    courses = canvas.get_courses(enrollment_state='active',
    enrollment_type='student')
    return list(courses)

def fetch_assignment_data(courses):
    all_assignments = []
    for course in courses:
        # This needs to be here because some courses are no longer used
        if not hasattr(course, 'name'):
            continue
        # Grab all the assignments for each course 
        assignments = course.get_assignments()
        all_assignments.extend(assignments)
    return all_assignments

def fetch_submission_time(assignments, user):
    all_submissions = []
    for assignment in assignments:
        submission = assignment.get_submission(user)
        all_submissions.append(submission)
    return all_submissions

def fetch_unlock_date(assignments):
    all_due_dates = []
    for assignment in assignments:
        all_due_dates.append(assignment.created_at)
    return all_due_dates
    


# Begin local host server to allow for two programs to run at once
def start_server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(('localhost', 12345))
    server_socket.listen(1)
    print("Server listening on localhost:12345")
    
    while True:
        client_socket, addr = server_socket.accept()
        print(f"Connection from {addr}")
        token = client_socket.recv(4096).decode('utf-8')
        print(f"Raw token received: {token}") 
        response = getToken(token)
        # Optionally fetch and print Canvas data
        canvas_result = fetch_canvas_data()
        print(type(canvas_result))
        print(f"Canvas result: {canvas_result}")

        data = {
            "response": response,
            "courses": [
                {
                    "name": course.name,
                    "course_code": course.course_code
                }
                for course in canvas_result
            ]
        }
        response = json.dumps(data)
        client_socket.send(response.encode('utf-8'))
        client_socket.close()

if __name__ == "__main__":
    start_server()

