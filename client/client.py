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

# Function to send token to the server
def send_assignments_to_server(course_id):
    try: 
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect(('localhost', 12345))
        # Need to adjust the course_id to include an extra string index to parse different requests
        request = json.dumps({"type": "assignments", "course_id": course_id})
        client_socket.send(request.encode('utf-8'))
        # Increase the amount of data passed from client to server significantly
        response = client_socket.recv(65536).decode('utf-8') 
        print("Server response for assignments:", response)
        data = json.loads(response)
        client_socket.close()
        return data["assignments"]
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
    print(f"The {course} button was clicked!")
    course_code = course_table.get(course)
    print(f"The course id is: {course_code}.")
    # Verify that the course assignments have been obtained for the specific course
    course_assignments = send_assignments_to_server(course_code)
    print(course_assignments)

# Creates new window to generate new courses to the user
def open_new_window():
    # Initialize a key-value pair hash function to allow for instant access and for fetching assignments
    course_table = {}
    for course in final_result:
        course_table[course["name"]] = course["course_code"]

    # Fetch from the assignments
    new_window = customtkinter.CTkToplevel()
    new_window.title("New Window")
    new_window.geometry("800x600")

# Obtain courses that only pertain to what the user is currently taking
    for course in course_table:
      if "Homeroom" not in course and "Tech How-to" not in course:
            label = customtkinter.CTkButton(new_window, text = course, command = lambda c=course: couse_click_event(c, course_table))
            label.pack(pady = 20)

    # Textbox that allows you to ask a question to the LLM
    textbox = customtkinter.CTkTextbox(new_window, width = 400, height = 200)
    textbox.pack(padx = 20, pady=20)

    textbox.insert("0.0", "Please enter your inqueries here!")
    content = textbox.get("0.0", "end")

# Button that allows for inputting login token
button = customtkinter.CTkButton(app, text="Open Login Request", command=token_click_event)
button.pack(padx=20, pady=20)

print("You are now logged in via your token: ", secret_token)

app.mainloop()