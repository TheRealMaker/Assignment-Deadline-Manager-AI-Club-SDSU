import customtkinter
import socket
import json

# Generates a basic app
app = customtkinter.CTk()

# Window resolution
app.geometry("400x300")

secret_token = None

# Function to send token to the server
def send_token_to_server(token):
    try:
        # Begins socket_client and sends the token
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect(('localhost', 12345))
        # Need to adjust the token to include an extra string index to parse different requests
        request = json.dumps({"type": "courses", "token": token})
        # Encodes what we're sending and then decodes it afterwards
        client_socket.send(request.encode('utf-8'))
        # Increase the amount of data passed from client to server significantly
        response = client_socket.recv(65536).decode('utf-8') 
        print("Server response for courses:", response)
        data = json.loads(response)
        client_socket.close()
        return data["courses"]
    except Exception as e:
        print("Error connecting to server:", e)

# Function to send assignments and submissions to the server
def send_assignments_to_server(course_id):
    try: 
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect(('localhost', 12345))
        request = json.dumps({
            "type": "assignments",
            "token": secret_token, 
            "course_id": course_id
        })
        client_socket.send(request.encode('utf-8'))
        response = client_socket.recv(65536).decode('utf-8') 
        print("Server response for assignments:", response)
        data = json.loads(response)
        client_socket.close()
        return data["assignments"]
    except Exception as e:
        print("Error connecting to the server:", e)

def send_ai_question_to_server(prompt):
    try: 
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect(('localhost', 12345))
        request = json.dumps({"type": "ai_question", "response": prompt})
        client_socket.send(request.encode('utf-8'))
        raw_response = client_socket.recv(65536).decode('utf-8')  # no longer shadows prompt
        data = json.loads(raw_response)
        client_socket.close()
        return data["ai_response"]
    except Exception as e:
        print("Error connecting to the server:", e)

# Button that opens up the chance to respond 
def token_click_event():
    global secret_token
    global final_result 
    dialog = customtkinter.CTkInputDialog(text="Type in your token below:", title="")
    secret_token = dialog.get_input()
    print("You are now logged in: ", secret_token)
    if secret_token:
        final_result = send_token_to_server(secret_token)
    open_new_window()

# Will generate the list of assignments required for each course
def couse_click_event(course, course_table):
    # LLM will take this JSON information and apply it to its question
    global course_assignments
    print(f"The {course} button was clicked!")
    course_code = course_table.get(course)
    print(f"The course id is: {course_code}.")
    # Verify that the course assignments have been obtained for the specific course
    course_assignments = send_assignments_to_server(course_code)
    print(course_assignments)
    open_chat_window()

def open_new_window():
    course_table = {}
    for course in final_result:
        course_table[course["name"]] = course["id"]

    new_window = customtkinter.CTkToplevel()
    new_window.title("New Window")
    new_window.geometry("800x600")

    for course in course_table:
        if "Homeroom" not in course and "Tech How-to" not in course:
            label = customtkinter.CTkButton(new_window, text=course, command=lambda c=course: couse_click_event(c, course_table))
            label.pack(pady=20)

# Open a window that asks AI what we'll be doing
def open_chat_window():
    chat_window = customtkinter.CTkToplevel()  # fixed
    chat_window.title("Chat Window")
    chat_window.geometry("800x600")

    ai_button = customtkinter.CTkButton(chat_window, text = "Ask AI for Assignment Changes", command = ask_ai)
    ai_button.pack(padx=20, pady=20)


def ask_ai():
    print("\nGoing to ask a question!")
    send_ai_question_to_server(course_assignments)

# Button that allows for inputting login token
button = customtkinter.CTkButton(app, text="Open Login Request", command=token_click_event)
button.pack(padx=20, pady=20)

print("You are now logged in via your token: ", secret_token)

app.mainloop()