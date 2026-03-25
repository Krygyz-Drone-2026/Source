from djitellopy import Tello
import time

print("Create Tello object")
tello = Tello()

print("Connect to Tello Drone")
tello.connect()

battery_level = tello.get_battery()
print(battery_level)

print("Takeoff!")
tello.takeoff()

time.sleep(1)  # Wait for the drone to stabilize after takeoff

# go_xyz_speed(x, y, z, speed)
# x - (+)forward / (-)backward
# y - (+)left    / (-)right
# z - (+)up      / (-)down
# speed - movement speed (cm/s)

# Distance to travel for each move (in centimeters)
travel_distance_cm = 50
speed = 20

# Waypoints define the flight path as a list of (x, y, z) positions
# The drone visits each waypoint in order, creating a zigzag pattern
waypoints = [
    (0,  0,                  travel_distance_cm),   # Step 1: Move straight up
    (0,  travel_distance_cm, -travel_distance_cm),  # Step 2: Move left and down
    (0,  0,                  travel_distance_cm),   # Step 3: Move straight up
    (0, -travel_distance_cm, -travel_distance_cm),  # Step 4: Move right and down
]

for x, y, z in waypoints:
    tello.go_xyz_speed(x, y, z, speed)
    time.sleep(0.5)  # Wait for the drone to reach the position before next move

print("landing")
tello.land()
