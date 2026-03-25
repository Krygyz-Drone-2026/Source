from djitellopy import Tello
import time

# Create Tello object and connect to the drone
tello = Tello()
tello.connect()

# Print current battery level before flight
battery_level = tello.get_battery()
print(f"Battery Level: {battery_level}")

# Take off and wait 3 seconds for the drone to stabilize
tello.takeoff()
time.sleep(3)

# Attempt a flip to the right; catch any errors to ensure landing still occurs
try:
    print("Flip Right")
    tello.flip_right()
except Exception as e:
    print(f"Flip failed: {e}")

# Uncomment one of the lines below to try other flip directions
# try tello.flip_left()
# try tello.flip_forward()
# try tello.flip_back()

# Land the drone
print("landing")
tello.land()
