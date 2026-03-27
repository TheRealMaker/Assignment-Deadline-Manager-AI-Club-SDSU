import socket
import os
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
    print("This is an attempt on this object!")
    # Intialize the Canvas object:
    canvas = Canvas(CANVAS_API_URL, token_saved)
    user = canvas.get_user('self')
    print(user)
    courses = user.get_courses('self')
    for course in courses:
        print(course)
    return f"Canvas user: {user}"


# Begin local host server to allow for two programs to run at once
def start_server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(('localhost', 12345))
    server_socket.listen(1)
    print("Server listening on localhost:12345")
    
    while True:
        client_socket, addr = server_socket.accept()
        print(f"Connection from {addr}")
        token = client_socket.recv(1024).decode('utf-8')
        print(f"Raw token received: {token}") 
        response = getToken(token)
        # Optionally fetch and print Canvas data
        canvas_result = fetch_canvas_data()
        print(f"Canvas result: {canvas_result}")
        full_response = f"{response}\n{canvas_result}"
        client_socket.send(full_response.encode('utf-8'))
        client_socket.close()

if __name__ == "__main__":
    start_server()

