import tkinter as tk
from PIL import Image, ImageTk
from djitellopy import Tello

# ── Drone setup ───────────────────────────────────────────
tello = Tello()
speed = 30         # Current movement speed (range: 10 ~ 100)
is_flying = False  # Track whether the drone is in the air

# ── Drone commands ────────────────────────────────────────
def connect():
    tello.connect()
    battery = tello.get_battery()
    status_var.set(f"Connected  |  Battery: {battery}%")
    speed_var.set(f"Speed: {speed}")

def takeoff():
    global is_flying
    if not is_flying:
        tello.takeoff()
        is_flying = True
        state_dot.config(bg="#4CAF50")   # Green dot = flying
        status_var.set("Takeoff")

def land():
    global is_flying
    tello.land()
    is_flying = False
    state_dot.config(bg="#f44336")       # Red dot = landed
    status_var.set("Landed")

def move_up():
    tello.send_rc_control(0, 0, speed, 0)
    status_var.set(f"Move Up  (speed={speed})")

def move_down():
    tello.send_rc_control(0, 0, -speed, 0)
    status_var.set(f"Move Down  (speed={speed})")

def move_left():
    tello.send_rc_control(-speed, 0, 0, 0)
    status_var.set(f"Move Left  (speed={speed})")

def move_right():
    tello.send_rc_control(speed, 0, 0, 0)
    status_var.set(f"Move Right  (speed={speed})")

def stop():
    tello.send_rc_control(0, 0, 0, 0)
    status_var.set("Stop")

def speed_up():
    global speed
    if speed < 100:
        speed = min(speed + 10, 100)
        speed_var.set(f"Speed: {speed}")
        status_var.set(f"Speed increased → {speed}")

def speed_down():
    global speed
    if speed > 10:
        speed = max(speed - 10, 10)
        speed_var.set(f"Speed: {speed}")
        status_var.set(f"Speed decreased → {speed}")

def check_battery():
    battery = tello.get_battery()
    status_var.set(f"Battery: {battery}%")

# ── Window ────────────────────────────────────────────────
root = tk.Tk()
root.title("AI Drone")
root.geometry("380x500")
root.resizable(False, False)

BG     = "#f0f4f8"
BTN_FG = "white"
root.config(bg=BG)

for r in range(7):
    root.rowconfigure(r, weight=1)
root.columnconfigure(0, weight=1)

status_var = tk.StringVar(value="Not connected")
speed_var  = tk.StringVar(value=f"Speed: {speed}")

# ── Title ─────────────────────────────────────────────────
tk.Label(root, text="Tello Drone RC Controller",
         font=("Arial", 14, "bold"), bg=BG, fg="#333").grid(
         row=0, column=0, sticky="nsew", pady=(12, 0))

# ── Drone logo image ──────────────────────────────────────────────────────
# tello_logo.png: Tello product image (nicepng.com, personal/edu use)
# Crop: full drone body with guards, excluding right-side annotation text
_pil_img = Image.open("tello_logo.png").convert("RGB")
_iw, _ih = _pil_img.size
_pil_img = _pil_img.crop((30, 30, 540, _ih - 20))

# Resize to fit the logo area while keeping aspect ratio
logo_h = 110
ratio  = logo_h / _pil_img.height
logo_w = int(_pil_img.width * ratio)
_pil_img  = _pil_img.resize((logo_w, logo_h), Image.LANCZOS)
drone_img = ImageTk.PhotoImage(_pil_img)

# Logo frame: image on the left, status dot on the right
logo_frame = tk.Frame(root, bg=BG)
logo_frame.grid(row=1, column=0, pady=(4, 0))

tk.Label(logo_frame, image=drone_img, bg=BG).pack(side=tk.LEFT, padx=(0, 10))

# Vertical sub-frame for dot + label
dot_frame = tk.Frame(logo_frame, bg=BG)
dot_frame.pack(side=tk.LEFT, anchor="center")

state_dot = tk.Label(dot_frame, width=2, bg="#f44336",   # Red = landed
                     relief=tk.FLAT)
state_dot.pack()
tk.Label(dot_frame, text="status", font=("Arial", 8),
         bg=BG, fg="#999").pack()

# ── Connect / Takeoff / Land ──────────────────────────────
top = tk.Frame(root, bg=BG)
top.grid(row=2, column=0, sticky="nsew", padx=30)
for c in range(3):
    top.columnconfigure(c, weight=1)
top.rowconfigure(0, weight=1)

def btn(parent, text, cmd, bg, r, c, cs=1):
    b = tk.Button(parent, text=text, command=cmd,
                  bg=bg, fg=BTN_FG, font=("Arial", 11, "bold"),
                  relief=tk.FLAT, cursor="hand2",
                  activebackground=bg, activeforeground=BTN_FG)
    b.grid(row=r, column=c, columnspan=cs, padx=5, pady=5, sticky="nsew")
    return b

btn(top, "Connect",  connect, "#4CAF50", 0, 0)
btn(top, "Takeoff",  takeoff, "#2196F3", 0, 1)
btn(top, "Land",     land,    "#f44336", 0, 2)

# ── Directional pad ───────────────────────────────────────
pad = tk.Frame(root, bg=BG)
pad.grid(row=3, column=0, sticky="nsew", padx=30)
for c in range(3):
    pad.columnconfigure(c, weight=1)
for r in range(3):
    pad.rowconfigure(r, weight=1)

btn(pad, "▲ Up",    move_up,    "#607D8B", 0, 1)
btn(pad, "◀ Left",  move_left,  "#607D8B", 1, 0)
btn(pad, "■ Stop",  stop,       "#9E9E9E", 1, 1)
btn(pad, "Right ▶", move_right, "#607D8B", 1, 2)
btn(pad, "▼ Down",  move_down,  "#607D8B", 2, 1)

# ── Speed controls ────────────────────────────────────────
ctrl = tk.Frame(root, bg=BG)
ctrl.grid(row=4, column=0, sticky="nsew", padx=30)
for c in range(3):
    ctrl.columnconfigure(c, weight=1)
ctrl.rowconfigure(0, weight=1)

tk.Label(ctrl, textvariable=speed_var,
         font=("Arial", 11, "bold"), bg=BG, fg="#333").grid(
         row=0, column=0, sticky="nsew", padx=5)
btn(ctrl, "+ Speed", speed_up,   "#FF9800", 0, 1)
btn(ctrl, "- Speed", speed_down, "#FF9800", 0, 2)

# ── Battery ───────────────────────────────────────────────
bat = tk.Frame(root, bg=BG)
bat.grid(row=5, column=0, sticky="nsew", padx=30)
bat.columnconfigure(0, weight=1)
bat.rowconfigure(0, weight=1)
btn(bat, "Check Battery", check_battery, "#795548", 0, 0)

# ── Status bar ────────────────────────────────────────────
tk.Label(root, textvariable=status_var,
         font=("Arial", 10), bg=BG, fg="#666").grid(
         row=6, column=0, sticky="nsew", pady=(4, 12))

root.mainloop()
