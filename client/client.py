import customtkinter
import socket

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

# button 
def button_click_event():
    global secret_token
    dialog = customtkinter.CTkInputDialog(text="Type in your token below:", title="Test")
    secret_token = dialog.get_input()
    print("You are now logged in: ", secret_token)
    if secret_token:
        send_token_to_server(secret_token)

# Button that allows for inputting login token
button = customtkinter.CTkButton(app, text="Open Login Request", command=button_click_event)
button.pack(padx=20, pady=20)

print("You are now logged in: ", secret_token)

app.mainloop()