from djitellopy import Tello

myTello = Tello()
myTello.connect()

battery_level = myTello.get_battery()
print(f"battery level: {battery_level}")

while True:
    command = int(input("Enter Command: "))
    print(command, end="\n")

    if command == 1:
        myTello.takeoff()
    elif command == 2:
        myTello.move_up(30)
    elif command == 3:
        myTello.move_down(30)
    elif command == 4:
        myTello.land()
    else:
        break

print("Drone mission completed!")
