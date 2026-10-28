"""Pure state machine. Safety uses monotonic wall time, motion uses ROS time."""
import math
from collections import deque

SELECT = {'Pointing_Up': 'back_forth', 'Victory': 'circle', 'Wave': 'wave'}
VALID = set(SELECT) | {'Thumb_Up', 'Open_Palm', 'Closed_Fist', 'None'}


class Controller:
    def __init__(self, hold=0.35, timeout=0.8, selection_timeout=5.0):
        self.hold, self.timeout = hold, timeout
        self.selection_timeout = selection_timeout
        self.selected_at = float("-inf")
        self.selected = self.active = None
        self.candidate = None
        self.since = self.last_signal = float('-inf')
        self.latched = False
        self.started = 0.0
        self.status = 'IDLE'

    def stop(self, reason):
        self.selected = self.active = None
        self.status = reason

    def receive(self, gesture, now, sim):
        if gesture not in VALID:
            gesture = 'None'
        # Unknown classifications never keep motion alive.
        if gesture != 'None':
            self.last_signal = now
        if self.selected and SELECT.get(gesture) == self.selected:
            self.selected_at = now
        if gesture in ('Open_Palm', 'Closed_Fist'):
            self.stop('STOP' if gesture == 'Open_Palm' else 'IDLE')
        if gesture != self.candidate:
            self.candidate, self.since, self.latched = gesture, now, False
        if self.latched or now - self.since < self.hold:
            return
        self.latched = True
        if gesture in SELECT and not self.active:
            self.selected = SELECT[gesture]
            self.selected_at = now
            self.status = 'SELECTED: ' + self.selected
        elif (gesture == 'Thumb_Up' and self.selected and not self.active
              and now - self.selected_at <= self.selection_timeout):
            self.active, self.selected = self.selected, None
            self.started = sim
            self.status = 'RUNNING: ' + self.active

    def velocity(self, now, sim):
        if self.active and now - self.last_signal > self.timeout:
            self.stop('SIGNAL LOST')
        elif self.selected and now - self.selected_at > self.selection_timeout:
            self.stop('SELECTION EXPIRED')
        elif not self.active and not self.selected and now - self.last_signal > self.timeout:
            self.status = 'SIGNAL LOST'
        if not self.active:
            return 0.0, 0.0
        elapsed = sim - self.started
        if elapsed < 0:
            self.stop('CLOCK RESET')
            return 0.0, 0.0
        if self.active == 'back_forth':
            # Four complete forward/back pairs, 0.18 m per leg.
            phase = int(elapsed / 1.5)
            if phase < 8:
                return (0.12 if phase % 2 == 0 else -0.12), 0.0
        elif self.active == 'circle':
            if elapsed < 2 * math.pi / 0.3:
                return 0.12, 0.3  # radius 0.4 m
        elif self.active == 'wave':
            if elapsed < 4.0:
                return 0.0, (0.5 if int(elapsed) % 2 == 0 else -0.5)
        self.stop('DONE')
        return 0.0, 0.0


class WaveDetector:
    """Open palm wrist crosses alternating extrema >= 0.10 image widths."""
    def __init__(self):
        self.points = deque()
        self.until = 0.0

    def update(self, label, x, now):
        if label != 'Open_Palm':
            self.points.clear()
            self.until = 0.0
            return label
        self.points.append((now, x))
        while self.points and now - self.points[0][0] > 1.5:
            self.points.popleft()
        if self.points:
            anchor = self.points[0][1]
            direction, reversals = 0, 0
            for _, value in self.points:
                delta = value - anchor
                if abs(delta) >= 0.10:
                    sign = 1 if delta > 0 else -1
                    if direction and sign != direction:
                        reversals += 1
                    direction, anchor = sign, value
            if reversals >= 2:
                self.until = now + 0.6
        return 'Wave' if now < self.until else label
