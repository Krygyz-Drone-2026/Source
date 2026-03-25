from djitellopy import Tello
import time

# Initial speed value (range: -100 ~ 100)
speed = 10

up_down_speed = 0
left_right_speed = 0

# Connect to the drone
tello = Tello()
tello.connect()
time.sleep(0.5)


def set_speeds(ud, lr):
    # Update global speed variables and send RC control command
    global up_down_speed, left_right_speed
    up_down_speed = ud
    left_right_speed = lr
    tello.send_rc_control(lr, 0, ud, 0)


print(f"Battery Life Percentage: {tello.get_battery()}")

is_flying = False  # Track whether the drone is in the air

# Keep looping until the user chooses to land
while True:
    # Show available commands to the user
    print("1 - UP")
    print("2 - DOWN")
    print("3 - LEFT")
    print("4 - RIGHT")
    print("5 - Battery")
    print("6 - Stop (set speed to 0)")
    print("7 - +10 to speed")
    print("8 - -10 to speed")
    print("9 - Land")
    print("0 - Takeoff")

    cmd = input()
    if cmd == '':
        continue              # Ignore empty input and ask again
    cmd = int(cmd)
    print(cmd)

    if cmd == 0:
        if not is_flying:     # Only takeoff if the drone is on the ground
            tello.takeoff()
            is_flying = True
    elif cmd == 1:
        set_speeds(speed, 0)       # Move up at current speed
    elif cmd == 2:
        set_speeds(-speed, 0)      # Move down (negative = downward)
    elif cmd == 5:
        print(f"Battery Life Percentage: {tello.get_battery()}")
    elif cmd == 6:
        set_speeds(0, 0)     # Stop all movement (speed = 0)
    elif cmd == 7:
        if speed <= 100:
            speed += 10            # Increase speed by 10 (max 100)
    elif cmd == 8:
        if speed >= -100:
            speed -= 10            # Decrease speed by 10 (min -100)
    elif cmd == 9:
        tello.land()               # Land the drone and exit the loop
        break
