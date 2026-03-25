from djitellopy import Tello

myTello = Tello()
myTello.connect()
myTello.takeoff()

myTello.move_up(30)
myTello.move_down(30)

myTello.move_up(50)
myTello.move_down(50)

myTello.move_up(50)
myTello.move_down(50)

myTello.land()
