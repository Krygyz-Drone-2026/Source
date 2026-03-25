import tkinter as tk
from tkinter import messagebox
import threading
from djitellopy import Tello

# ── Drone instance ───────────────────────────────────────
myTello = Tello()
is_connected = False
is_flying = False

# ── Helpers ──────────────────────────────────────────────
def run_in_thread(fn):
    """Run drone command in background thread to keep GUI responsive."""
    threading.Thread(target=fn, daemon=True).start()

def set_status(msg, color="gray"):
    status_var.set(msg)
    status_label.config(fg=color)

def update_battery():
    if is_connected:
        battery = myTello.get_battery()
        color = "green" if battery > 50 else ("orange" if battery > 20 else "red")
        battery_var.set(f"Battery: {battery}%")
        battery_label.config(fg=color)
        root.after(10000, update_battery)  # refresh every 10s

def set_buttons_state(connected, flying):
    connect_btn.config(state=tk.DISABLED if connected else tk.NORMAL)
    takeoff_btn.config(state=tk.NORMAL if (connected and not flying) else tk.DISABLED)
    land_btn.config(state=tk.NORMAL if (connected and flying) else tk.DISABLED)
    for btn in move_buttons:
        btn.config(state=tk.NORMAL if (connected and flying) else tk.DISABLED)

# ── Drone commands ───────────────────────────────────────
def connect():
    def _connect():
        global is_connected
        try:
            set_status("Connecting...", "orange")
            myTello.connect()
            is_connected = True
            battery = myTello.get_battery()
            color = "green" if battery > 50 else ("orange" if battery > 20 else "red")
            battery_var.set(f"Battery: {battery}%")
            battery_label.config(fg=color)
            set_status("Connected", "green")
            set_buttons_state(True, False)
            root.after(10000, update_battery)
        except Exception as e:
            set_status(f"Connection failed: {e}", "red")
    run_in_thread(_connect)

def takeoff():
    def _takeoff():
        global is_flying
        try:
            set_status("Taking off...", "orange")
            # myTello.takeoff()
            is_flying = True
            set_status("Airborne", "blue")
            set_buttons_state(True, True)
        except Exception as e:
            set_status(f"Error: {e}", "red")
    run_in_thread(_takeoff)

def land():
    def _land():
        global is_flying
        try:
            set_status("Landing...", "orange")
            # myTello.land()
            is_flying = False
            set_status("Landed", "green")
            set_buttons_state(True, False)
        except Exception as e:
            set_status(f"Error: {e}", "red")
    run_in_thread(_land)

def move_up():
    run_in_thread(lambda: (set_status("Moving Up 30cm", "blue"), myTello.move_up(30), set_status("Airborne", "blue")))

def move_down():
    run_in_thread(lambda: (set_status("Moving Down 30cm", "blue"), myTello.move_down(30), set_status("Airborne", "blue")))

def move_forward():
    run_in_thread(lambda: (set_status("Moving Forward 30cm", "blue"), myTello.move_forward(30), set_status("Airborne", "blue")))

def move_back():
    run_in_thread(lambda: (set_status("Moving Back 30cm", "blue"), myTello.move_back(30), set_status("Airborne", "blue")))

def move_left():
    run_in_thread(lambda: (set_status("Moving Left 30cm", "blue"), myTello.move_left(30), set_status("Airborne", "blue")))

def move_right():
    run_in_thread(lambda: (set_status("Moving Right 30cm", "blue"), myTello.move_right(30), set_status("Airborne", "blue")))

def rotate_cw():
    run_in_thread(lambda: (set_status("Rotating CW 45°", "blue"), myTello.rotate_clockwise(45), set_status("Airborne", "blue")))

def rotate_ccw():
    run_in_thread(lambda: (set_status("Rotating CCW 45°", "blue"), myTello.rotate_counter_clockwise(45), set_status("Airborne", "blue")))

def emergency():
    if messagebox.askyesno("Emergency Stop", "Force stop all motors?"):
        myTello.emergency()
        set_status("EMERGENCY STOP", "red")

# ── Window ───────────────────────────────────────────────
root = tk.Tk()
root.title("Tello Drone Controller")
root.geometry("380x520")
root.resizable(False, False)
root.config(bg="#1e1e2e")

DARK   = "#1e1e2e"
PANEL  = "#2a2a3e"
GREEN  = "#4CAF50"
BLUE   = "#2196F3"
RED    = "#f44336"
ORANGE = "#FF9800"
WHITE  = "#ffffff"
GRAY   = "#aaaaaa"

def styled_btn(parent, text, cmd, bg, fg=WHITE, width=12, state=tk.NORMAL):
    return tk.Button(parent, text=text, command=cmd, bg=bg, fg=fg,
                     width=width, relief=tk.FLAT, padx=6, pady=6,
                     font=("Arial", 10, "bold"), cursor="hand2",
                     activebackground=bg, activeforeground=fg, state=state)

status_var  = tk.StringVar(value="Not connected")
battery_var = tk.StringVar(value="Battery: --%")

# ── Title ─────────────────────────────────────────────────
tk.Label(root, text="Tello Drone Controller", font=("Arial", 15, "bold"),
         bg=DARK, fg=WHITE).pack(pady=(14, 2))

# ── Status bar ───────────────────────────────────────────
info_frame = tk.Frame(root, bg=PANEL, padx=10, pady=6)
info_frame.pack(fill=tk.X, padx=16, pady=6)

status_label = tk.Label(info_frame, textvariable=status_var,
                        font=("Arial", 10), bg=PANEL, fg=GRAY)
status_label.pack(side=tk.LEFT)

battery_label = tk.Label(info_frame, textvariable=battery_var,
                         font=("Arial", 10, "bold"), bg=PANEL, fg=GRAY)
battery_label.pack(side=tk.RIGHT)

# ── Connect ───────────────────────────────────────────────
connect_btn = styled_btn(root, "Connect to Drone", connect, GREEN, width=24)
connect_btn.pack(pady=6)

# ── Takeoff / Land ────────────────────────────────────────
tl_frame = tk.Frame(root, bg=DARK)
tl_frame.pack(pady=4)
takeoff_btn = styled_btn(tl_frame, "Takeoff", takeoff, BLUE, state=tk.DISABLED)
takeoff_btn.pack(side=tk.LEFT, padx=6)
land_btn = styled_btn(tl_frame, "Land", land, RED, state=tk.DISABLED)
land_btn.pack(side=tk.LEFT, padx=6)

# ── Directional pad ───────────────────────────────────────
tk.Label(root, text="Movement", font=("Arial", 10, "bold"),
         bg=DARK, fg=GRAY).pack(pady=(10, 0))

pad_frame = tk.Frame(root, bg=DARK)
pad_frame.pack()

move_buttons = []

def dpad_btn(parent, text, cmd, r, c):
    btn = styled_btn(parent, text, cmd, PANEL, GRAY, width=8, state=tk.DISABLED)
    btn.grid(row=r, column=c, padx=4, pady=4)
    move_buttons.append(btn)
    return btn

dpad_btn(pad_frame, "Up",      move_up,      0, 1)
dpad_btn(pad_frame, "Forward", move_forward, 1, 1)
dpad_btn(pad_frame, "Left",    move_left,    1, 0)
dpad_btn(pad_frame, "Back",    move_back,    2, 1)
dpad_btn(pad_frame, "Right",   move_right,   1, 2)
dpad_btn(pad_frame, "Down",    move_down,    2, 0)

# ── Rotate ────────────────────────────────────────────────
tk.Label(root, text="Rotate 45°", font=("Arial", 10, "bold"),
         bg=DARK, fg=GRAY).pack(pady=(10, 0))

rot_frame = tk.Frame(root, bg=DARK)
rot_frame.pack()

ccw_btn = styled_btn(rot_frame, "<< CCW", rotate_ccw, PANEL, GRAY, state=tk.DISABLED)
ccw_btn.pack(side=tk.LEFT, padx=6)
move_buttons.append(ccw_btn)

cw_btn = styled_btn(rot_frame, "CW >>",  rotate_cw,  PANEL, GRAY, state=tk.DISABLED)
cw_btn.pack(side=tk.LEFT, padx=6)
move_buttons.append(cw_btn)

# ── Emergency ─────────────────────────────────────────────
styled_btn(root, "EMERGENCY STOP", emergency, RED, width=24).pack(pady=14)

# ── Keyboard shortcuts ────────────────────────────────────
root.bind("<t>", lambda e: takeoff() if is_flying == False else None)
root.bind("<l>", lambda e: land())
root.bind("<w>", lambda e: move_forward())
root.bind("<s>", lambda e: move_back())
root.bind("<a>", lambda e: move_left())
root.bind("<d>", lambda e: move_right())
root.bind("<Up>",    lambda e: move_up())
root.bind("<Down>",  lambda e: move_down())
root.bind("<Left>",  lambda e: rotate_ccw())
root.bind("<Right>", lambda e: rotate_cw())

root.mainloop()
