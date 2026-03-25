import tkinter as tk
from djitellopy import Tello

myTello = Tello()

# ── Drone commands ───────────────────────────────────────
def connect():
    myTello.connect()
    battery = myTello.get_battery()
    status_var.set(f"Connected  |  Battery: {battery}%")

def takeoff():
    myTello.takeoff()
    status_var.set("Takeoff")

def move_up():
    myTello.move_up(30)
    status_var.set("Move Up 30cm")

def move_down():
    myTello.move_down(30)
    status_var.set("Move Down 30cm")

def land():
    myTello.land()
    status_var.set("Landed")

# ── Window ───────────────────────────────────────────────
root = tk.Tk()
root.title("Simple Tello Drone Controller")
root.geometry("360x320")
root.resizable(False, False)

BG     = "#f0f4f8"
BTN_FG = "white"
root.config(bg=BG)

# 전체 레이아웃: 3행 — 타이틀 / 버튼 / 상태
root.rowconfigure(0, weight=1)
root.rowconfigure(1, weight=3)
root.rowconfigure(2, weight=1)
root.columnconfigure(0, weight=1)

status_var = tk.StringVar(value="Not connected")

# ── Title ─────────────────────────────────────────────────
tk.Label(root, text="Simple Tello Drone Controller",
         font=("Arial", 14, "bold"), bg=BG, fg="#333").grid(
         row=0, column=0, sticky="nsew", pady=(16, 4))

# ── Buttons grid ──────────────────────────────────────────
grid = tk.Frame(root, bg=BG)
grid.grid(row=1, column=0, sticky="nsew", padx=30)

grid.columnconfigure(0, weight=1)
grid.columnconfigure(1, weight=1)
for r in range(3):
    grid.rowconfigure(r, weight=1)

def btn(text, cmd, bg, r, c, cs=1):
    b = tk.Button(grid, text=text, command=cmd,
                  bg=bg, fg=BTN_FG, font=("Arial", 11, "bold"),
                  relief=tk.FLAT, cursor="hand2",
                  activebackground=bg, activeforeground=BTN_FG)
    b.grid(row=r, column=c, columnspan=cs, padx=6, pady=6, sticky="nsew")
    return b

btn("Connect",   connect,   "#4CAF50", 0, 0, cs=2)
btn("Takeoff",   takeoff,   "#2196F3", 1, 0)
btn("Land",      land,      "#f44336", 1, 1)
btn("Move Up",   move_up,   "#607D8B", 2, 0)
btn("Move Down", move_down, "#607D8B", 2, 1)

# ── Status ────────────────────────────────────────────────
tk.Label(root, textvariable=status_var,
         font=("Arial", 10), bg=BG, fg="#666").grid(
         row=2, column=0, sticky="nsew", pady=(4, 14))

root.mainloop()
