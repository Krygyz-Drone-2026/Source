from djitellopy import Tello

# Create Tello object and connect to the drone
drone = Tello()
drone.connect()

# Takeoff
drone.takeoff()

# Fly forward 40cm x 3, rotate 180 degrees CW, repeat once more
for _ in range(2):
    for _ in range(3):
        drone.move_forward(40)
    drone.rotate_clockwise(180)

# Land the drone
drone.land()
