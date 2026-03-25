import tkinter as tk
from djitellopy import Tello

myTello = Tello()

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

# ── Window ──────────────────────────────────────────────
root = tk.Tk()
root.title("Tello Drone Controller")
root.geometry("300x320")
root.resizable(False, False)

status_var = tk.StringVar(value="Not connected")

tk.Label(root, text="Simple Tello Drone Controller", font=("Arial", 14, "bold")).pack(pady=10)

tk.Button(root, text="Connect",   width=20, bg="#4CAF50", fg="white", command=connect).pack(pady=4)
tk.Button(root, text="Takeoff",   width=20, bg="#2196F3", fg="white", command=takeoff).pack(pady=4)
tk.Button(root, text="Move Up",   width=20, command=move_up).pack(pady=4)
tk.Button(root, text="Move Down", width=20, command=move_down).pack(pady=4)
tk.Button(root, text="Land",      width=20, bg="#f44336", fg="white", command=land).pack(pady=4)

tk.Label(root, textvariable=status_var, font=("Arial", 10), fg="gray").pack(pady=12)

root.mainloop()
