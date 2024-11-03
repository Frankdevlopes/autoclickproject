import tkinter as tk
from tkinter import Toplevel, messagebox, filedialog
from PIL import Image, ImageDraw, ImageTk
import pyautogui
import threading
import time
import keyboard
import json
from pynput.mouse import Listener
import pystray

# Variables to store the hotkey, theme status, clicking, click count, cursor position, recorded actions, and playback state
current_hotkey = "F2"  # Default hotkey
is_dark_theme = False  # Theme toggle
clicking = False  # To control clicking
click_count = 0  # To keep track of clicks
selected_coordinates = None  # To store the selected cursor position
recorded_actions = []  # List to store recorded actions
listener = None  # Mouse listener
is_recording = False  # To track if recording is in progress
is_playing = False  # To track if playback is in progress

# Function to create a rounded rectangle image
def create_rounded_rectangle(width, height, radius, color):
    image = Image.new("RGBA", (width, height), (255, 255, 255, 0))
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((0, 0, width, height), radius=radius, fill=color)
    return ImageTk.PhotoImage(image)

# Function to center the window on any screen
def center_window(window):
    window.update_idletasks()
    width, height = window.winfo_width(), window.winfo_height()
    x = (window.winfo_screenwidth() // 2) - (width // 2)
    y = (window.winfo_screenheight() // 2) - (height // 2)
    window.geometry(f"{width}x{height}+{x}+{y}")

# Function to toggle between dark and light themes
def toggle_theme():
    global is_dark_theme
    is_dark_theme = not is_dark_theme
    new_bg = "#303030" if is_dark_theme else "#f8f8f8"
    new_fg = "#FFFFFF" if is_dark_theme else "#1230AE"
    new_icon = "moon.png" if is_dark_theme else "sun (1).png"

    # Update background colors for main window and frames
    window.configure(bg=new_bg)
    header_frame.configure(bg=new_bg)
    close_icons_frame.configure(bg=new_bg)
    interval_frame.configure(bg=new_bg)
    options_frame.configure(bg=new_bg)
    repeat_frame.configure(bg=new_bg)
    cursor_container.configure(bg=new_bg)
    buttons_frame.configure(bg=new_bg)

    # Update foreground color for labels and text
    header_label.config(fg=new_fg, bg=new_bg)
    hotkey_label.config(fg=new_fg, bg=new_bg)

    # Update theme icon
    theme_image = Image.open(new_icon).resize((25, 25), Image.LANCZOS)
    theme_icon = ImageTk.PhotoImage(theme_image)
    theme_label.config(image=theme_icon)
    theme_label.image = theme_icon  # Keep reference to avoid garbage collection

# Function to open the hotkey popup
def open_hotkey_popup():
    hotkey_popup = Toplevel(window)
    hotkey_popup.title("Change Hotkey")
    hotkey_popup.configure(bg="#f8f8f8")
    hotkey_popup.geometry("300x150")
    center_window(hotkey_popup)

    label = tk.Label(hotkey_popup, text="Enter new hotkey:", font=("Arial", 12), fg="black", bg="#f8f8f8")
    label.pack(pady=(15, 5))

    hotkey_entry = tk.Entry(hotkey_popup, font=("Arial", 10), width=20)
    hotkey_entry.pack(pady=5)
    hotkey_entry.focus()

    def save_hotkey():
        global current_hotkey
        new_hotkey = hotkey_entry.get().upper()
        if new_hotkey:
            try:
                keyboard.unhook_all_hotkeys()  # Unregister previous hotkeys
                keyboard.add_hotkey(new_hotkey, toggle_clicker)  # Bind the new hotkey
                current_hotkey = new_hotkey
                hotkey_label.config(text=f"Current Hotkey: {current_hotkey}")
                messagebox.showinfo("Success", f"Hotkey changed to: {current_hotkey}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to set hotkey: {str(e)}")
        else:
            messagebox.showwarning("Warning", "Please enter a valid hotkey.")

    save_button = tk.Button(hotkey_popup, text="Save", command=save_hotkey, bg ="#1230AE", fg="white", font=("Arial", 10, "bold"))
    save_button.pack(pady=(10, 5))

    # Cancel button to close the popup without saving
    cancel_button = tk.Button(hotkey_popup, text="Cancel", command=hotkey_popup.destroy, bg="#f8f8f8", fg="black", font=("Arial", 10))
    cancel_button.pack()

# Function to open info popup window
def open_info_popup():
    info_popup = Toplevel(window)
    info_popup.title("About AS Auto Clicker")
    info_popup.configure(bg="#f8f8f8")
    info_popup.geometry("350x250")
    center_window(info_popup)

    title = tk.Label(info_popup, text="AS Auto Clicker", font=("Arial", 16, "bold"), fg="black", bg="#f8f8f8")
    title.pack(pady=(15, 5))

    info_text = (
        "Features:\n\n"
        "- Set custom click intervals\n"
        "- Choose click types (single or double )\n"
        "- Pick mouse button (left, middle, right)\n"
        "- Random intervals support\n"
        "- Configurable hotkeys for start/stop"
    )
    info_label = tk.Label(info_popup, text=info_text, font=("Arial", 10, "bold"), fg="black", bg="#f8f8f8", justify="center")
    info_label.pack(pady=10, padx=20)

    close_button = tk.Button(info_popup, text="Close", command=info_popup.destroy, bg="#1230AE", fg="white", font=("Arial", 10, "bold"))
    close_button.pack(pady=(10, 10))

# Function to close the main window and terminate the application
def close_window():
    window.destroy()

# Function to open record and playback popup window
def open_record_playback_popup():
    global record_playback_popup, record_button
    record_playback_popup = Toplevel(window)
    record_playback_popup.title("Record & Playback")
    record_playback_popup.configure(bg="#f8f8f8")
    record_playback_popup.geometry("300x200")
    center_window(record_playback_popup)

    title = tk.Label(record_playback_popup, text="Record & Playback", font=("Arial", 14, "bold"), fg="black", bg="#f8f8f8")
    title.pack(pady=(15, 10))
    is_recording = False  # To track if recording is in progress
    def update_record_button():
        nonlocal is_recording
        if is_recording:
            record_button.config(text="Recording", bg="green", fg="white")
        else:
            record_button.config(text="Record", bg="#1230AE", fg="white")

    def play_action():
        global recorded_actions
        # Ask user for a file to load recorded actions
        file_path = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])
        if file_path:
            try:
                with open(file_path, "r") as f:
                    recorded_actions = json.load(f)

                # Close the popup window
                record_playback_popup.destroy()

                # Play back the recorded actions
                def play_recording():
                    global is_playing
                    is_playing = True  # Set the flag to indicate playback is active
                    for action in recorded_actions:
                        if not is_playing:  # Check if playback is stopped
                            break  # Exit the loop if playback is stopped
                        x, y, button = action
                        pyautogui.click(x, y, button=button)  # Simulate the click at the recorded position
                        time.sleep(0.1)  # Optional delay between actions
                    is_playing = False  # Reset the flag when playback is done

                # Run the playback in a separate thread to avoid freezing the UI
                threading.Thread(target=play_recording).start()

            except FileNotFoundError:
                messagebox.showerror("Error", "No recorded actions found. Please record actions first.")

    def record_action():
        nonlocal is_recording
        global recorded_actions, listener
        if is_recording:
            messagebox.showerror("Error", "Recording is already in progress.")
            return

        recorded_actions = []  # Clear previous recordings
        is_recording = True
        update_record_button()

        # Start a new thread for recording
        def recording_thread():
            nonlocal is_recording
            global listener
            # Start listening to mouse events
            def on_click(x, y, button, pressed):
                if pressed:
                    recorded_actions.append((x, y, button.name))  # Store click position and button
                    print(f"Recorded: {x}, {y}, {button.name}")

            # Start a listener
            listener = Listener(on_click=on_click)
            listener.start()  # This will start the listener in a separate thread # Wait until recording is stopped
            while is_recording:
                time.sleep(0.1)

            # Ask user for a location to save the recorded actions
            file_path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON files", "*.json")])
            if file_path:
                # Save recorded actions to the selected file
                with open(file_path, "w") as f:
                    json.dump(recorded_actions, f)
                print(f"Recording saved to {file_path}")
            is_recording = False 
            update_record_button()

        # Run the recording thread
        threading.Thread(target=recording_thread).start()

        # Close the popup window after starting recording
        record_playback_popup.destroy()

    # Create buttons for play and record
    play_button = tk.Button(record_playback_popup, text="Play", command=play_action, bg="#1230AE", fg="white", font=("Arial", 10, "bold"), width=15)
    play_button.pack(pady=5)
    record_button = tk.Button(record_playback_popup, text="Record", command=record_action, bg="#1230AE", fg="white", font=("Arial", 10, "bold"), width=15)
    record_button.pack(pady=5)

    close_button = tk.Button(record_playback_popup, text="Close", command=record_playback_popup.destroy, bg="#f8f8f8", fg="black", font=("Arial", 10))
    close_button.pack(pady=(10, 5))

# Function to make the window draggable
def start_move(event):
    window.x = event.x
    window.y = event.y

def stop_move(event):
    window.x = None
    window.y = None

def do_move(event):
    x = window.winfo_pointerx() - window.x
    y = window.winfo_pointery() - window.y
    window.geometry(f"+{x}+{y}")

# Create the main window with increased width
window = tk.Tk()
window.title("AS Auto Clicker")
window.configure(bg="#f8f8f8")
# Adjust the main window height
window.geometry("800x650")  # Reduced height to 650

center_window(window)

# Load and set taskbar icon to 'icons8-mouse-48.png'
taskbar_icon = Image.open("logoauto-removebg-preview.png").resize((48, 48), Image.LANCZOS)
icon_photo = ImageTk.PhotoImage(taskbar_icon)
window.iconphoto(True, icon_photo)  # This sets the icon in the taskbar

# Placeholder for images (use actual file paths)
icon_image = Image.open("logoauto-removebg-preview.png").resize((50, 50), Image.LANCZOS)
icon_photo = ImageTk.PhotoImage(icon_image)
sun_icon_image = Image.open("sun (1).png").resize((25, 25), Image.LANCZOS)
sun_icon_photo = ImageTk.PhotoImage(sun_icon_image)

# Function to create labeled frames with precise blue border
def create_label_frame(window, title):
    outer_frame = tk.Frame(window, bg="#1230AE")  # Removed padx and pady
    outer_frame.pack(pady=8, fill=tk.X, padx=15)  # Keep padding for the outer frame
    label_frame = tk.LabelFrame(outer_frame, text=title, fg="#1230AE", bg="#f8f8f8", font=("Arial", 12, "bold"), padx=10, pady=10)  # Adjusted padding
    label_frame.pack(fill=tk.BOTH, expand=True, padx=0, pady=0)  # Removed padding for the label frame
    return label_frame

# Header section
header_frame = tk.Frame(window, bg="#f8f8f8")
header_frame.pack(pady=2, fill=tk.X, padx=5)
icon_label = tk.Label(header_frame, image=icon_photo, bg="#f8f8f8")
icon_label.pack(side=tk.LEFT, padx=(2, 2))
header_label = tk.Label(header_frame, text="AS Auto Clicker", fg="#1230AE", bg="#f8f8f8", font=("Arial", 18, "bold"))
header_label.pack(side=tk.LEFT, padx=(2, 5))

# Right icons
close_icons_frame = tk.Frame(header_frame, bg="#f8f8f8")
close_icons_frame.pack(side=tk.RIGHT, padx=(0, 5))

info_label = tk.Label(close_icons_frame, text="ℹ", fg="#1230AE", bg="#f8f8f8", font=("Arial", 16))
info_label.pack(side=tk.LEFT, padx=5)
info_label.bind("<Button-1>", lambda e: open_info_popup())

theme_label = tk.Label(close_icons_frame, image=sun_icon_photo, bg="#f8f8f8")
theme_label.pack(side=tk.LEFT, padx=5)
theme_label.bind("<Button-1>", lambda e: toggle_theme())

# Click Interval section
interval_frame = create_label_frame(window, "Click Interval")

# Set Time section
set_time_label = tk.Label(interval_frame, text="Set Time (Hours:Min:Sec: Ms)", fg="black", bg="#f8f8f8", font=("Arial", 10, "bold"))
set_time_label.grid(row=0, column=0, columnspan=4, pady=1)
tk.Label(interval_frame, text="Hrs", fg="black", bg="#f8f8f8", font=("Arial", 9)).grid(row=1, column=0, padx=5)
tk.Label(interval_frame, text="Min", fg="black", bg="#f8f8f8", font=("Arial", 9)).grid(row=1, column=1, padx=5)
tk.Label(interval_frame, text="Sec", fg="black", bg="#f8f8f8", font=("Arial", 9)).grid(row=1, column=2, padx=5)
tk.Label(interval_frame, text="Ms", fg="black", bg="#f8f8f8", font=("Arial", 9)).grid(row=1, column=3, padx=5)

# Time Spinboxes
hours = tk.Spinbox(interval_frame, from_=0, to=23, width=5, fg="#1230AE")
minutes = tk.Spinbox(interval_frame, from_=0, to=59, width=5, fg="#1230AE")
seconds = tk.Spinbox(interval_frame, from_=0, to=59, width=5, fg="#1230AE")
milliseconds = tk.Spinbox(interval_frame, from_=0, to=990, increment=10, width=5, fg="#1230AE")
milliseconds.grid(row=2, column=3, padx=5)
milliseconds.delete(0, "end")
milliseconds.insert(0, "100")

def update_spinbox(event):
    try:
        value = int(milliseconds.get())
        if 0 <= value <= 990:
            milliseconds.delete(0, "end")
            milliseconds.insert(0, str(value))
    except ValueError:
        pass

milliseconds.bind("<KeyRelease>", update_spinbox)
hours.grid(row=2, column=0, padx=5)
minutes.grid(row=2, column=1, padx=5)
seconds.grid(row=2, column=2, padx=5)

# Random Interval section
rand_interval_label = tk.Label(interval_frame, text="Random Interval (Sec:Ms)", fg="black", bg="#f8f8f8", font=("Arial", 10, "bold"))
rand_interval_label.grid(row=0, column=5, columnspan=2, pady=1)
tk.Label(interval_frame, text="Sec", fg="black", bg="#f8f8f8", font=("Arial", 9)).grid(row=1, column=5, padx=5)
tk.Label(interval_frame, text="Ms", fg="black", bg="#f8f8f8", font=("Arial", 9)).grid(row=1, column= 6, padx=5)
rand_seconds = tk.Spinbox(interval_frame, from_=0, to=59, width=5, fg="#1230AE")
rand_milliseconds = tk.Spinbox(interval_frame, from_=0, to=990, increment=10, width=5, fg ="#1230AE")
rand_seconds.grid(row=2, column=5, padx=5)
rand_milliseconds.grid(row=2, column=6, padx=5)

# Click Options section
options_frame = create_label_frame(window, "Click Options")
mouse_buttons_frame = tk.Frame(options_frame, bg="#f8f8f8")
mouse_buttons_frame.grid(row=0, column=0, padx=10, pady=5, sticky="nw")
tk.Label(mouse_buttons_frame, text="Mouse Buttons", fg="#1230AE", bg="#f8f8f8", font=("Arial", 12, "bold")).pack(anchor="w")
mouse_button_var = tk.StringVar()
mouse_button_var.set("left")  # Default mouse button
left_button = tk.Radiobutton(mouse_buttons_frame, text="Left", variable=mouse_button_var, value="left", fg="#1230AE", bg="#f8f8f8", font=("Arial", 12, "bold"))
left_button.pack(anchor="w")
middle_button = tk.Radiobutton(mouse_buttons_frame, text="Middle", variable=mouse_button_var, value="middle", fg="#1230AE", bg="#f8f8f8", font=("Arial", 12 , "bold"))
middle_button.pack(anchor="w")
right_button = tk.Radiobutton(mouse_buttons_frame, text="Right", variable=mouse_button_var, value="right", fg="#1230AE", bg="#f8f8f8", font=("Arial", 12, "bold"))
right_button.pack(anchor="w")
click_type_frame = tk.Frame(options_frame, bg="#f8f8f8")
click_type_frame.grid(row =0, column=1, padx=10, pady=5, sticky="nw")
tk.Label(click_type_frame, text="Click Type", fg="#1230AE", bg="#f8f8f8", font=("Arial", 12, "bold")).pack(anchor="w")
click_type_var = tk.StringVar()
click_type_var.set("single")  # Default click type
single_click = tk.Radiobutton(click_type_frame, text="Single Click", variable=click_type_var, value="single", fg="#1230AE", bg="#f8f8f8", font=("Arial", 12, "bold"))
single_click.pack(anchor="w")
double_click = tk.Radiobutton(click_type_frame, text="Double Click", variable=click_type_var, value="double", fg="#1230AE", bg="#f8f8f8", font=("Arial", 12, "bold"))
double_click.pack(anchor="w")

# Click Repeat section
repeat_frame = create_label_frame(window, "Click Repeat")
repeat_var = tk.StringVar()
repeat_var.set("repeat")  # Default repeat option
repeat_button = tk.Radiobutton(repeat_frame, text="Repeat", variable=repeat_var, value="repeat", fg="#1230AE", bg="#f8f8f8", font=("Arial", 10, "bold"))
repeat_button.grid(row=0, column=0, sticky="w")
repeat_spinbox = tk.Spinbox(repeat_frame, from_=1, to=100, width=5, fg="#1230AE", font=("Arial", 10, "bold"))
repeat_spinbox.grid(row=0, column=1, padx=5)
stop_button = tk.Radiobutton(repeat_frame, text="Until Stopped", variable=repeat_var, value="until_stopped", fg="#1230AE", bg="#f8f8f8", font=("Arial", 10, "bold"))
stop_button.grid(row=0, column=2, sticky="w")

# Cursor Position section
cursor_container = tk.Frame(window, bg="#f8f8f8")
cursor_container.pack(fill=tk.X, padx=15, pady=5)
cursor_outer_frame = tk.Frame(cursor_container, bg="#f8f8f8", padx=1, pady=1)  # Changed to match background
cursor_outer_frame.pack(side=tk.LEFT, fill=tk.BOTH)
cursor_frame = tk.LabelFrame(cursor_outer_frame, text="Cursor Position", fg="#1230AE", bg="#f8f8f8", font=("Arial", 12, "bold"), padx=10, pady=10, highlightbackground="#f8f8f8", highlightthickness=0)  # Added options to remove border
cursor_frame.pack(fill=tk.BOTH)
cursor_options_frame = tk.Frame(cursor_frame, bg="#f8f8f8")
cursor_options_frame.pack(anchor="w")
cursor_var = tk.StringVar()
cursor_var.set("current")  # Default cursor position
current_location = tk.Radiobutton(cursor_options_frame, text="Use Current Location", variable=cursor_var , value="current", fg="#1230AE", bg="#f8f8f8", font=("Arial", 10, "bold"))
current_location.pack(anchor="w")
pick_location_frame = tk.Frame(cursor_options_frame, bg="#f8f8f8")
pick_location_frame.pack(anchor ="w")
pick_location = tk.Radiobutton(pick_location_frame, text="Pick a Location", variable=cursor_var, value="pick", fg="#1230AE", bg="#f8f8f8", font=("Arial", 10, "bold"))
pick_location.pack(side=tk.LEFT)
pick_button = tk.Button(pick_location_frame, text="Pick", fg="#1230AE", font=("Arial", 10, "bold"))
pick_button.pack(side=tk.LEFT, padx=5)

# Function to show an alert window when "Pick" is clicked
def show_pick_position_alert():
    alert_popup = Toplevel(window)
    alert_popup.title("Pick Position")
    alert_popup.configure(bg="#f8f8f8")
    alert_popup.geometry("250x100")
    center_window(alert_popup)

    # Alert message
    message_label = tk.Label(alert_popup, text="Move the pop-up window to any position then PICK and press start.", font=("Arial", 10), fg="black", bg="#f8f8f8", wraplength=250)
    message_label.pack(pady=(20, 10))

    # Close button
    close_button = tk.Button(alert_popup, text="Pick", command =alert_popup.destroy, bg="#1230AE", fg="white", font=("Arial", 10, "bold"))
    close_button.pack(pady=(5, 10))

    # Bind mouse click to capture coordinates
    alert_popup.bind("<Button-1 >", lambda e: set_cursor_position(e.x_root, e.y_root, alert_popup))

def set_cursor_position(x, y, popup):
    global selected_coordinates
    selected_coordinates = (x, y)
    print (f"Cursor position set to : {selected_coordinates}")
    popup.destroy()  # Close the popup after selecting the position

# Bind the "Pick" button to the show_pick_position_alert function
pick_button.config(command=show_pick_position_alert)

# Hotkey display
hotkey_label = tk.Label(window, text=f"Current Hotkey: {current_hotkey}", fg="#1230AE", bg="#f8f8f8", font=("Arial", 12, "bold"))
hotkey_label.pack(pady=(10, 0))

# Alert label to show clicking status
alert_label = tk.Label(window, text="", fg="green", bg="#f8f8f8", font=("Arial", 10))
alert_label.pack(pady=(5, 0))  # Add some padding

# Four main action buttons in a 2x2 grid layout
buttons_frame = tk.Frame(cursor_container, bg="#f8f8f8")
buttons_frame.pack(side=tk.RIGHT, padx=(15, 0), fill=tk.Y, pady=2)
rounded_start = create_rounded_rectangle(160, 35, 15, "#1230AE")
rounded_stop = create_rounded_rectangle(160, 35, 15, "#1230AE")
rounded_hotkey = create_rounded_rectangle(160, 35, 15, "#1230AE")
rounded_playback = create_rounded_rectangle(160, 35, 15, "#1230AE")

# Buttons with new arrangement
stop_button = tk.Button(buttons_frame, text="STOP", image=rounded_stop, compound="center", fg="white", font=("Arial", 10, "bold"), borderwidth=0)
start_button = tk.Button(buttons_frame, text="START", image=rounded_start, compound="center", fg="white", font=("Arial", 10, "bold"), borderwidth=0)
change_hotkey_button = tk.Button(buttons_frame, text="Change HOTKEY", image=rounded_hotkey, compound="center", fg="white", font=("Arial", 10, "bold"), borderwidth=0, command=open_hotkey_popup)
playback_button = tk.Button(buttons_frame, text="Record & Playback", image=rounded_playback, compound="center", fg="white", font=("Arial", 10, "bold"), borderwidth=0, command=open_record_playback_popup)

# Arrange buttons in a 2x2 grid layout
stop_button.grid(row=0, column=0, padx=10, pady=5)  # Move stop_button to the first row
change_hotkey_button.grid(row=1, column=0, padx=10, pady=5)  # Move change_hotkey_button to the second row
start_button.grid(row=0, column=1, padx=10, pady=5)  # Keep start_button in the first row, second column
playback_button.grid(row=1, column =1, padx=10, pady=5)

# Function to start the auto clicker
def start_clicker():
    global clicking, click_count
    clicking = True
    click_count = 0  # Reset click count when starting
    mouse_button = mouse_button_var.get()
    click_type = click_type_var.get()
    repeat_option = repeat_var.get()
    repeat_count = int(repeat_spinbox.get())

    interval = (int(hours.get()) * 3600 + int(minutes.get()) * 60 + int(seconds.get())) * 1000 + int(milliseconds.get())

    if selected_coordinates:
        pyautogui.moveTo(selected_coordinates[0], selected_coordinates[1])

    alert_label.config(text="Clicking has started!")

    def click():
        global click_count
        if not clicking: # Check if clicking is still true
            return  # Stop clicking if false
        if click_type == "single":
            pyautogui.click(button=mouse_button)
        elif click_type == "double":
            pyautogui.doubleClick(button=mouse_button)
        click_count += 1
        if repeat_option == "repeat" and click_count < repeat_count:
            window.after(interval, click)
        elif repeat_option == "until_stopped":
            window.after(interval, click)

    click()

# Function to stop the auto clicker
def stop_clicker():
    global clicking 
    clicking = False
    alert_label.config(text="Clicking has stopped.")

    # Save recorded actions
    if recorded_actions:
        file_path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON files", "*.json ")])
        if file_path:
            with open(file_path, "w") as f:
                json.dump(recorded_actions, f)
            print(f"Recording saved to {file_path}")

# Function to stop playback
def stop_playback():
    global is_playing
    is_playing = False
    alert_label.config(text="Playback has stopped.")

# Function to stop recording
def stop_recording():
    global is_recording
    is_recording = False
    if listener:
        listener.stop()  # Stop the mouse listener if it's active
    alert_label.config(text="Recording has stopped.")

# Function to toggle the auto clicker
def toggle_clicker():
    global clicking, is_playing, is_recording
    if clicking:
        stop_clicker()
    elif is_playing:
        stop_playback()  # Call a new function to stop playback
    elif is_recording:
        stop_recording()  # Stop recording if it's in progress
    else:
        start_clicker()

# Bind the start and stop buttons to the start_clicker and stop_clicker functions
start_button.config(command=start_clicker)
stop_button.config(command=stop_clicker)

# Register the hotkey
keyboard.add_hotkey(current_hotkey, toggle_clicker)  # Bind the default hot key

# Function to create system tray icon
def create_system_tray_icon():
    def run_tray_icon():
        image = Image.open("logoauto-removebg-preview.png")
        menu = pystray.Menu(
            pystray.MenuItem("Restore", restore_window),
            pystray.MenuItem("Exit", close_window)
        )
        icon = pystray.Icon("AS Auto Clicker", image, "AS Auto Clicker", menu)
        icon.run()

    # Start the tray icon in a separate thread
    tray_thread = threading.Thread(target=run_tray_icon, daemon=True)
    tray_thread.start()

# Function to restore the window
def restore_window():
    window.deiconify()  # Restore the main window
    # Optionally, you can also stop the tray icon if needed
    # icon.stop()  # If you want to stop the tray icon when restoring

# Add the label at the bottom middle of the window
footer_label = tk.Label(window, text="Proudly Developed by asautoclicker.com", fg="#1230AE", bg="#f8f8f8", font=("Arial", 12, "italic"))
footer_label.pack(side=tk.BOTTOM, pady=(5, 0))  # Reduce the padding to move it up


# Run the Tkinter event loop
window.mainloop()