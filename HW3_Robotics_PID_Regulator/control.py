#!/usr/bin/env python

import asyncio
import json

import websockets
from pid import PID


# TODO: Initialize the pid variable.
steering_pid = PID(-0.2, 0.00001, -2.0)
throttle_pid = PID(0.1, 0.002, 0.1)
INIT_THROTTLE = .3

# Checks if the SocketIO event has JSON data.
# If there is data the JSON object in string format will be returned,
# else the empty string "" will be returned.
def getData(message):
    try:
        start = message.find("[")
        end = message.rfind("]")
        return message[start : end + 1]
    except:
        return ""


async def handleTelemetry(websocket, msgJson):
    cte = msgJson[1]["cte"]
    speed = msgJson[1]["speed"]
    angle = msgJson[1]["steering_angle"]



    # TODO: Calculate steering value here, remember the steering value is
    # [-1, 1].
    # NOTE: Feel free to play around with the throttle and speed.
    # Maybe use another PID controller to control the speed!

    steering_pid.UpdateError(cte)

    steer_value = steering_pid.TotalError()
    if steer_value > 1.0:
        steer_value = 1.0
    if steer_value < -1.0:
        steer_value = -1.0

    throttle_pid.UpdateError(20.0 - float(speed))
    throttle = throttle_pid.TotalError()
    if throttle > 1.:
        throttle = 1.
    if throttle < 1.:
        throttle = -1.

    print("CTE: ", cte, ", speed: ", speed, ", angle: ", angle, ", speed delta: ", throttle)

    response = {}

    response["steering_angle"] = steer_value

    # TODO: Play around with throttle value
    response["throttle"] = throttle

    msg = '42["steer",' + json.dumps(response) + "]"

    await websocket.send(msg)


async def echo(websocket, path):
    async for message in websocket:
        if len(message) < 3 or message[0] != "4" or message[1] != "2":
            return

        s = getData(message)
        msgJson = json.loads(s)

        event = msgJson[0]
        if event == "telemetry":
            await handleTelemetry(websocket, msgJson)
        else:
            msg = '42["manual",{}]'
            await websocket.send(msg)


def main():
    start_server = websockets.serve(echo, "localhost", 4567)

    asyncio.get_event_loop().run_until_complete(start_server)
    asyncio.get_event_loop().run_forever()


if __name__ == "__main__":
    main()
