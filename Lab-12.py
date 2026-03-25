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

# Distance to travel for each move (in centimeters)
travel_distance_cm = 50

# go_xyz_speed(x, y, z, speed)
# x - (+)forward  / (-)backward
# y - (+)left     / (-)right
# z - (+)up       / (-)down
# speed - movement speed (cm/s)

# Step 1: Move straight up
tello.go_xyz_speed(0, 0, travel_distance_cm, 20)
time.sleep(0.5)  # Wait for the drone to reach the position

# Step 2: Move left and down diagonally
tello.go_xyz_speed(0, travel_distance_cm, -travel_distance_cm, 20)
time.sleep(0.5)

# Step 3: Move straight up again
tello.go_xyz_speed(0, 0, travel_distance_cm, 20)
time.sleep(0.5)

# Step 4: Move right and down diagonally (back to original height)
tello.go_xyz_speed(0, -travel_distance_cm, -travel_distance_cm, 20)
time.sleep(0.5)

print("landing")
tello.land()
