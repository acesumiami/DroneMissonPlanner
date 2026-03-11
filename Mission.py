from Commands import *

def mission_preamble():
    return [
        # ChangeSpeed(SPEED_TYPE.SPEED_TYPE_GROUNDSPEED, 15),
        # GimballSet(0, -90),
        CamSetMode(),
        # CamFocusSet(FocusType.CAMERA_SOURCE_DEFAULT, 1)
    ]

class Mission(object):
    def __init__(self, waypoints, altitude, fps, n_photos, directions=None, videos=False):
        self.wps = waypoints
        self.alt = altitude
        self.cam_rate = fps
        self.n_photos = n_photos
        self.directions = directions
        self.videos = videos

    def get_items(self):
        items = mission_preamble()
        for idx, wp in enumerate(self.wps):
            items += self.wp_items(wp, 0 if self.directions is None else self.directions[idx])

        return items


    def wp_items(self, wp, direction):
        coord = GPSCoordinate(wp[1], wp[0], alt=self.alt)
        record = [
            CamStartSeq(3, 2),
            NavNLoiter(2, coords=coord, direction=direction),
            CamStopSeq(),
            CamSetMode(CAMERA_MODE.VIDEO),
            CamStartVideo()
        ] if self.videos else [
            CamStartSeq(self.cam_rate, self.n_photos + 1), # +1 because why not? Could be fun to see if it actually counts okay
        ]

        end_recording = [CamStopVideo(), CamSetMode()] if self.videos else [CamStopSeq()]
        return [
            Nav2Point(coords=coord, yaw=direction),
        ] + record + [
            NavNLoiter(int(round(self.n_photos * self.cam_rate)), coords=coord, direction=direction)
        ] + end_recording