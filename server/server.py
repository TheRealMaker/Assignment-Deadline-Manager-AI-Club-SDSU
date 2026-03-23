import socket
import os
from canvasapi import Canvas
from dotenv import load_dotenv

load_dotenv()
print("Loaded .env values:")
print("CANVAS_API_URL:", os.getenv("CANVAS_API_URL"))

CANVAS_API_URL = os.getenv("CANVAS_API_URL")
token_saved = ""

def getToken(token_value):
    global token_saved
    token_saved = token_value
    print(f"Token received and saved: {token_saved}")  # Added print
    return f"Token '{token_saved}' saved successfully."

def fetch_canvas_data():
    if not token_saved:
        return "Canvas token never acquired, please retry."
    if not CANVAS_API_URL:
        return "Canvas API is not correct, please change."
    try:
        print("This is an attempt on this object!")
        # Intialize the Canvas object:
        canvas = Canvas(CANVAS_API_URL, token_saved)
        print(canvas)
        user = canvas.get_user('self')
        print(user)
        print(user.name)
        return f"Canvas user: {user}"
    except Exception as e:
        return f"Canvas Error detected! Program has ended."

def start_server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(('localhost', 12345))
    server_socket.listen(1)
    print("Server listening on localhost:12345")
    
    while True:
        client_socket, addr = server_socket.accept()
        print(f"Connection from {addr}")
        token = client_socket.recv(1024).decode('utf-8')
        print(f"Raw token received: {token}")  # Added print for raw input
        response = getToken(token)
        # Optionally fetch and print Canvas data
        canvas_result = fetch_canvas_data()
        print(f"Canvas result: {canvas_result}")  # Added print
        full_response = f"{response}\n{canvas_result}"
        client_socket.send(full_response.encode('utf-8'))
        client_socket.close()

if __name__ == "__main__":
    start_server()

