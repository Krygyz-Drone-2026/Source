from djitellopy import Tello

# Create Tello object
myTello = Tello()

try:
    # Connect to the drone
    myTello.connect()

    # Takeoff
    myTello.takeoff()

    # Bounce at each height (cm) in sequence
    heights = [30, 50, 50]
    for height in heights:
        myTello.move_up(height)    # Move up by the given height
        myTello.move_down(height)  # Return to original height

    # Land the drone
    myTello.land()

except Exception as e:
    # Print error message and land safely if an error occurs
    print(f"Error occurred: {e}")
    myTello.land()
