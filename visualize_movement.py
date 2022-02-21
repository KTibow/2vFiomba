"""
Visualize the local file movement.json, containing a previous log of the roomba's movement.

The file format is a JSON file, with the following columns:

- Amount that the Roomba has moved forwards/backwards (encoder_delta)
- Amount that the Roomba has turned left/right (left is positive, right is negative, degrees_turned)
- Light bumper (true/false, light_bumper)
- Cliff (true/false, cliff)
- Bumper/wheel drop (true/false, bumper_wheel_drop)
"""
import ujson, turtle

with open("movement.json") as f:
    movement = ujson.load(f)
    turtle.penup()
    turtle.goto(400, 400)
    turtle.color(1, 0.4, 0.4)
    turtle.write("bumper/drop")
    turtle.goto(400, 380)
    turtle.color(1, 0.4, 1)
    turtle.write("cliff sensor")
    turtle.goto(400, 360)
    turtle.color(0.9, 0.9, 0)
    turtle.write("light bumper")
    turtle.home()
    for movement_step in movement:
        turtle.color("black")
        turtle.pensize(10)
        turtle.pendown()
        turtle.setheading(turtle.heading() + movement_step["degrees_turned"])
        turtle.forward(movement_step["encoder_delta"] * 20)
        turtle.penup()
        turtle.update()
        if movement_step["bumper_wheel_drop"]:
            turtle.color(1, 0.4, 0.4)
            turtle.dot(20)
        elif movement_step["cliff"]:
            turtle.color(1, 0.4, 1)
            turtle.dot(20)
        elif movement_step["light_bumper"]:
            turtle.color(1, 1, 0.4)
            turtle.dot(20)

turtle.done()
