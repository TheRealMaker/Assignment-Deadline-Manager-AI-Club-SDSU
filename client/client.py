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
        response = client_socket.recv(1024).decode('utf-8')
        print("Server response:", response)
        client_socket.close()
    except Exception as e:
        print("Error connecting to server:", e)

# Button that opens up the chance to respond 
def token_click_event():
    global secret_token
    dialog = customtkinter.CTkInputDialog(text="Type in your token below:", title="Test")
    secret_token = dialog.get_input()
    print("You are now logged in: ", secret_token)
    if secret_token:
        send_token_to_server(secret_token)

def AI_click_event():
    print("Test")

def open_new_window():
    new_window = customtkinter.CTkToplevel()
    new_window.title = ("New Window")
    new_window.geometry = ("400X300")

    label = customtkinter.CTkLabel(new_window, text = "This is our new window")
    label.pack(pady = 20)
# Button that allows for inputting login token
button = customtkinter.CTkButton(app, text="Open Login Request", command=token_click_event)
button.pack(padx=20, pady=20)

print("You are now logged in: ", secret_token)

# Textbox that allows you to ask a question to the LLM
textbox = customtkinter.CTkTextbox(app, width = 400, height = 200)
textbox.pack(padx = 20, pady=20)

textbox.insert("0.0", "Please enter your inqueries here!")

content = textbox.get("0.0", "end")

button = customtkinter.CTkButton(app, text="Open Window", command=open_new_window)
button.pack(pady=20)

app.mainloop()