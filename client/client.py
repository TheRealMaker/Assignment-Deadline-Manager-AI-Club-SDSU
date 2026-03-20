import customtkinter

# Generates a basic app
app = customtkinter.CTk()

# Window resolution
app.geometry("400x300")

secret_token = None

# button 
def button_click_event():
    global secret_token
    dialog = customtkinter.CTkInputDialog(text="Type in your in your token below:", title="Test")
    secret_token = dialog.get_input()
    print("You are now logged in: ", secret_token)


# Button that allows for inputting login token
button = customtkinter.CTkButton(app, text="Open Login Request", command=button_click_event)
button.pack(padx=20, pady=20)

print("You are now logged in: ", secret_token)



app.mainloop()