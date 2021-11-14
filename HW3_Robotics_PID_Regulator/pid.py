#!/usr/bin/env python


class PID:

    # TODO: Complete the PID class. You may add any additional desired functions

    def __init__(self, Kp, Ki=0.0, Kd=0.0):
        # TODO: Initialize PID coefficients (and errors, if needed)
        self.Kp = Kp
        self.Ki = Ki
        self.Kd = Kd
        self.p_error = 0
        self.d_error = 0
        self.errors = []
        self.dt = 8

    def UpdateError(self, cte):
        # TODO: Update PID errors based on cte
        cte = float(cte)
        self.d_error = cte - self.p_error
        self.p_error = cte
        self.errors.append(cte)
        self.i_error = sum(self.errors[-self.dt:])


    def TotalError(self):
        # TODO: Calculate and return the total error

        return self.Kp * self.p_error + self.Kd * self.d_error + self.Ki * self.dt * self.i_error
