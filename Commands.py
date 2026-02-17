from enum import Enum

class GPSCoordinate(object):
    def __init__(self, lat, lon, alt=None):
        self.lat = lat
        self.lon = lon
        self.alt = alt

    def get_params(self, mission_info):
        return [
            self.lat,
            self.lon,
            mission_info.get("alt") if self.alt is None else self.alt
        ]

class Command(object):
    def __init__(self, command_code):
        self.command_code = command_code

    def info(self, mission_info):
        params = self.params(mission_info)
        if len(params) < 7:
            params += [0] * (len(params) - 7)
        assert(len(params) == 7)

        return [
            self.command_code,
            params
        ]

# https://mavlink.io/en/messages/common.html#MAV_CMD_NAV_WAYPOINT
class Nav2Point(Command):
    def __init__(self, coords, hold_time = 0, acceptance_radius = 0.25):
        super().__init__(16)
        self.coords = coords
        self.hold_time = hold_time
        self.acceptance_radius = acceptance_radius

    def params(self, mission_info):
        return [
            self.hold_time,
            self.acceptance_radius,
            0, # Pass radius
            "NaN"
        ] + self.coords.get_params(mission_info)
    
# https://mavlink.io/en/messages/common.html#MAV_CMD_NAV_LOITER_TIME
class NavNLoiter(Command):
    def __init__(self, time, coords):
        super().__init__(19)
        self.time = time
        self.coords = coords

    def params(self, mission_info):
        return [
            self.time,
            False, 
            0,
            0,
        ] + self.coords.get_params(mission_info)
    
# https://mavlink.io/en/messages/common.html#CAMERA_MODE
class CAMERA_MODE(Enum):
    IMAGE = 0
    VIDEO = 1
    SURVEY = 2

# https://mavlink.io/en/messages/common.html#MAV_CMD_SET_CAMERA_MODE
class CamSetMode(Command):
    def __init__(self, camera_mode: CAMERA_MODE = CAMERA_MODE.IMAGE):
        super().__init__(530)
        self.camera_mode = camera_mode

    def params(self, mission_info):
        return [
            0,
            self.camera_mode
        ]

# https://mavlink.io/en/messages/common.html#MAV_CMD_DO_GIMBAL_MANAGER_PITCHYAW
class GimballSet(Command): # 1001, 1000
    def __init__(self, pitch_angle, yaw_angle, pitch_rate = 5, yaw_rate = 5):
        super().__init__(1000)
        assert(pitch_angle <= 180 and pitch_angle >= -180)
        assert(yaw_angle <= 180 and yaw_angle >= -180)
        self.pitch_angle = pitch_angle
        self.yaw_angle = yaw_angle
        self.pitch_rate = pitch_rate
        self.yaw_rate = yaw_rate

    def params(self, mission_info):
        return [
            self.pitch_angle,
            self.yaw_angle,
            self.pitch_rate,
            self.yaw_rate,
            8 | 16, # https://mavlink.io/en/messages/common.html#GIMBAL_DEVICE_FLAGS
            0,
            0
        ]

# https://mavlink.io/en/messages/common.html#MAV_CMD_SET_CAMERA_FOCUS
class CamFocusSet(Command):
    def __init__(self, focus_type, focus_value):
        super().__init__(532)
        self.focus_type = focus_type
        self.focus_value = focus_value

    def params(self, mission_info):
        return [
            self.focus_type,
            self.focus_value,
            0
        ]

# https://mavlink.io/en/messages/common.html#SET_FOCUS_TYPE
class CamFocusINF(CamFocusSet):
    def __init__(self):
        super().__init__(2, 100)

# https://mavlink.io/en/messages/common.html#MAV_CMD_IMAGE_START_CAPTURE
class CamStartSeq(Command):
    def __init__(self, interval: int, imgCount: int = 0):
        super().__init__(2000)
        self.interval = interval
        self.imgCount = imgCount

    def params(self, mission_info):
        return [
            0,
            self.interval,
            self.max_images,
            self.imgCount
        ]

# https://mavlink.io/en/messages/common.html#MAV_CMD_IMAGE_STOP_CAPTURE
class CamStopSeq(Command):
    def __init__(self):
        super().__init__(2001)

    def params(self, mission_info):
        return [0]