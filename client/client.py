import customtkinter
import socket
import json

# Generates a basic app
app = customtkinter.CTk()

# Window resolution
app.geometry("400x300")

secret_token = None

# Function to send token to server
def send_token_to_server(token):
    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect(('localhost', 12345))
        client_socket.send(token.encode('utf-8'))
        response = client_socket.recv(4096).decode('utf-8')
        print("Server response:", response)
        data = json.loads(response)

        print("Courses:", data["courses"])

        client_socket.close()
        return data["courses"]
    except Exception as e:
        print("Error connecting to server:", e)

# Button that opens up the chance to respond 
def token_click_event():
    global secret_token
    global final_result 
    dialog = customtkinter.CTkInputDialog(text="Type in your token below:", title="Test")
    secret_token = dialog.get_input()
    print("You are now logged in: ", secret_token)
    if secret_token:
        final_result = send_token_to_server(secret_token)
    open_new_window()

def AI_click_event():
    print("Test")

def open_new_window():
    course_list = []
    for course in final_result:
        course_list.append(course["name"])
    new_window = customtkinter.CTkToplevel()
    new_window.title("New Window")
    new_window.geometry("800x600")

    for course in course_list:
      if "Homeroom" not in course and "Tech How-to" not in course:
            label = customtkinter.CTkLabel(new_window, text = course)
            label.pack(pady = 20)

    # Textbox that allows you to ask a question to the LLM
    textbox = customtkinter.CTkTextbox(new_window, width = 400, height = 200)
    textbox.pack(padx = 20, pady=20)

    textbox.insert("0.0", "Please enter your inqueries here!")
    content = textbox.get("0.0", "end")

# Button that allows for inputting login token
button = customtkinter.CTkButton(app, text="Open Login Request", command=token_click_event)
button.pack(padx=20, pady=20)

print("You are now logged in: ", secret_token)

app.mainloop()