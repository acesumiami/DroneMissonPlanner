from Commands import *
import math

def mission_preamble():
    return [
        GimballSet(0, -90),
        CamSetMode(),
        CamFocusINF()
    ]

class Mission(object):
    def __init__(self, waypoints, altitude, fps, n_photos):
        self.wps = waypoints
        self.alt = altitude
        self.cam_rate = fps
        self.n_photos = n_photos

    def get_items(self):
        items = mission_preamble()
        for wp in self.wps:
            items += self.wp_items(wp)

    def wp_items(self, wp):
        coord = GPSCoordinate(wp[0], wp[1], alt=self.alt)
        return [
            Nav2Point(coords=coord),
            CamStartSeq(self.cam_rate, self.n_photos + 1), # +1 because why not? Could be fun to see if it actually counts okay
            NavNLoiter(int(math.round(self.n_photos / self.cam_rate)), coords=coord),
            CamStopSeq()
        ]