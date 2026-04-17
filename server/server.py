import socket
import os
import json
from canvasapi import Canvas
from dotenv import load_dotenv
from google import genai
from google.genai import types
from datetime import datetime

# Load dot environment
load_dotenv() 
print("Loaded .env values:")
print("CANVAS_API_URL:", os.getenv("CANVAS_API_URL"))

# Client will pull from the SDSU local Canvas URL to use for collecting data
CANVAS_API_URL = os.getenv("CANVAS_API_URL")
token_saved = ""

# Client will pull API Key from the environmental variable
client = genai.Client()

# Ask AI a question to assist with Canvas
def ask_ai_question(prompt):
    # For comparing today's date to the other assignments with a due date
    now = datetime.now() 
    # Convert the list of assignment dicts into a readable string for Gemini
    # Regex-like conversion of our JSON file into a string for it to parse properly
    if isinstance(prompt, list):
        prompt = "\n".join(
            f"- {a['name']} (due: {a['due_at']})" for a in prompt 
        )
    # Will state prompt and generate user response to their question
    print(f"Question received: {prompt}")
    print("Generating response to user's question!")
    result = client.models.generate_content(
        model="gemini-2.5-flash",
        config=types.GenerateContentConfig(
            system_instruction= "You are an online advisor for students "
            "attending San Diego State University, you will be given a list of their assignments within an individual course, and you will need to list which assignments "
            "take priority over others. Use the specific courses they give you, and order them from 1 to however many there are. The current date is " + str(now) + ". Thus, only "
            "talk about assignments that are due after this date. Place some emojis where you see fit. Rank the difficulty based on how long the submission was from the due date"
            "and estimate how long certain assignments may take based on the difference between submitted_at and due_date. If the difference is small, then it will likely be more difficult"
            "Respond in a supportive demeanor, please."),
        contents=prompt)
    print(result.text)
    return result.text

# Retrieve our global token
def getToken(token_value):
    global token_saved
    token_saved = token_value
    print(f"Token received and saved: {token_saved}")
    return f"Token '{token_saved}' saved successfully."

# Fetch specific Canvas data from the user token so they know what they're receiving. 
def fetch_canvas_data():
    if not token_saved:
        return "Canvas token never acquired, please retry."
    if not CANVAS_API_URL:
        return "Canvas API is not correct, please change."
    canvas = Canvas(CANVAS_API_URL, token_saved)

    # Grab courses that are currently active for the user
    courses = fetch_courses_data(canvas)
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

# Begin local host server to allow for two programs to communicate with one another
def start_server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(('localhost', 12345))
    server_socket.listen(1)
    print("Server listening on localhost:12345")
    
    while True:
        # Create a client socket and what we'll be adding
        client_socket, addr = server_socket.accept()
        print(f"Connection from {addr}")
        # Allows us to transmit more bytes to allow for quicker transfer of larger data
        raw = client_socket.recv(65536).decode('utf-8')
        print(f"Raw data received: {raw}") 
        # Response allows us to obtain a token
        data = json.loads(raw)

        # Convert our data into JSON for our course information
        try:
            if data["type"] == "courses":
                getToken(data["token"])
                canvas_result = fetch_canvas_data()
                response = {
                    "courses": [
                    {
                        "name": course.name,
                        "course_code": course.course_code,
                        # For submission times later
                        "id": course.id
                    }
                        for course in canvas_result
                    ]
                }

            # Grab course assignments and filter to only unfinished ones
            elif data["type"] == "assignments":
                getToken(data["token"])
                canvas = Canvas(CANVAS_API_URL, token_saved)
                course = canvas.get_course(data["course_id"])
                assignment_result = list(course.get_assignments())
                user_data = fetch_user_data(canvas)
                submission_result = fetch_submission_time(assignment_result, user_data)

                # Build a lookup map from assignment_id -> assignment object
                # so we can go from submission -> assignment name/due_at
                assignment_map = {assignment.id: assignment for assignment in assignment_result}

                # Filter submissions not yet submitted
                unfinished_submissions = [
                    submission for submission in submission_result
                    if submission.submitted_at is None
                ]

                # Finished submissions already submitted
                finished_submissions = [
                    submission for submission in submission_result
                    if submission.submitted_at is not None
                ]

                # Use submission.assignment_id to pull the matching assignment details
                response = {
                    "assignments": [
                        {
                            "assignment_id": submission.assignment_id,
                            "name": assignment_map[submission.assignment_id].name
                                if submission.assignment_id in assignment_map else "Unknown",
                            "due_at": assignment_map[submission.assignment_id].due_at
                                if submission.assignment_id in assignment_map else None,
                            "submitted_at": submission.submitted_at
                        }
                        for submission in finished_submissions
                    ]
                }

            # Will ask the AI a question and print in the server terminal for now
            elif data["type"] == "ai_question":
                print("AI question handler reached")  # does it get here?
                ai_response = ask_ai_question(data["response"])
                response = {"ai_response": ai_response}
        except Exception as e:
            # In case there is an error within gemini, this will let us know. 
            print(f"Server error: {e}") 
            response = {"error": str(e)}

        # Convert JSON with data
        final_response = json.dumps(response)
        client_socket.send(final_response.encode('utf-8'))
        client_socket.close()

if __name__ == "__main__":
    start_server()