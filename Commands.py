from enum import IntEnum

# https://mavlink.io/en/messages/common.html#MAV_BOOL
class MAV_BOOL(IntEnum):
    MAV_BOOL_FALSE = 0
    MAV_BOOL_TRUE = 1

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
    
# https://mavlink.io/en/messages/common.html#MAV_FRAME
class Frame(IntEnum):
    MAV_FRAME_GLOBAL = 0	                #   Global (WGS84) coordinate frame + altitude relative to mean sea level (MSL).
    MAV_FRAME_LOCAL_NED = 1	                #   NED local tangent frame (x: North, y: East, z: Down) with origin fixed relative to earth.
    MAV_FRAME_MISSION = 2	                #   NOT a coordinate frame, indicates a mission command.
    MAV_FRAME_GLOBAL_RELATIVE_ALT = 3	    #	Global (WGS84) coordinate frame + altitude relative to the home position.
    MAV_FRAME_LOCAL_ENU = 4	                #	ENU local tangent frame (x: East, y: North, z: Up) with origin fixed relative to earth.
    MAV_FRAME_GLOBAL_INT = 5	            #	Global (WGS84) coordinate frame (scaled) + altitude relative to mean sea level (MSL).
    MAV_FRAME_GLOBAL_RELATIVE_ALT_INT = 6	#	Global (WGS84) coordinate frame (scaled) + altitude relative to the home position.
    MAV_FRAME_LOCAL_OFFSET_NED = 7	        #	NED local tangent frame (x: North, y: East, z: Down) with origin that travels with the vehicle.
    MAV_FRAME_BODY_NED = 8	                #	Same as MAV_FRAME_LOCAL_NED when used to represent position values. Same as MAV_FRAME_BODY_FRD when used with velocity/acceleration values.
    MAV_FRAME_BODY_OFFSET_NED = 9	        #	This is the same as MAV_FRAME_BODY_FRD.
    MAV_FRAME_GLOBAL_TERRAIN_ALT = 10	    #	Global (WGS84) coordinate frame with AGL altitude (altitude at ground level).
    MAV_FRAME_GLOBAL_TERRAIN_ALT_INT = 11	#	Global (WGS84) coordinate frame (scaled) with AGL altitude (altitude at ground level).
    MAV_FRAME_BODY_FRD = 12	                #	FRD local frame aligned to the vehicle's attitude (x: Forward, y: Right, z: Down) with an origin that travels with vehicle.
    MAV_FRAME_LOCAL_FRD = 20	            #	FRD local tangent frame (x: Forward, y: Right, z: Down) with origin fixed relative to earth. The forward axis is aligned to the front of the vehicle in the horizontal plane.
    MAV_FRAME_LOCAL_FLU = 21	            #	FLU local tangent frame (x: Forward, y: Left, z: Up) with origin fixed relative to earth. The forward axis is aligned to the front of the vehicle in the horizontal plane.

class Command(object):
    def __init__(self, command_code, frame: Frame):
        self.command_code = command_code
        self.frame = frame

    def info(self, mission_info):
        params = self.params(mission_info)
        if len(params) < 7:
            params += [0] * (7 - len(params))
        assert(len(params) == 7)

        return [
            self.command_code,
            self.frame,
            params
        ]
    
class MissionCommand(Command):
    def __init__(self, command_code):
        super().__init__(command_code, Frame.MAV_FRAME_MISSION)

class NavigationCommand(Command):
    def __init__(self, command_code):
        super().__init__(command_code, Frame.MAV_FRAME_GLOBAL_RELATIVE_ALT)

# https://mavlink.io/en/messages/common.html#MAV_CMD_NAV_WAYPOINT
class Nav2Point(NavigationCommand):
    def __init__(self, coords, hold_time = 0, acceptance_radius = 0.25, yaw=None):
        super().__init__(16)
        self.coords = coords
        self.hold_time = hold_time
        self.acceptance_radius = acceptance_radius
        self.yaw = yaw

    def params(self, mission_info):
        return [
            self.hold_time,
            self.acceptance_radius,
            0, # Pass radius
            self.yaw if self.yaw is None else (self.yaw + 1) * 180,
        ] + self.coords.get_params(mission_info)
    
# https://mavlink.io/en/messages/common.html#MAV_CMD_NAV_LOITER_TIME
class NavNLoiter(NavigationCommand):
    def __init__(self, time, coords, loiter_radius=0, direction=None):
        super().__init__(19)
        self.time = time
        self.coords = coords
        self.loiter_radius = loiter_radius
        if not direction is None:
            print("DIRECTION FOR NAVNLOITER IS SET BUT NOT USED")

    def params(self, mission_info):
        return [
            self.time,
            MAV_BOOL.MAV_BOOL_TRUE, 
            self.loiter_radius,
            0,
        ] + self.coords.get_params(mission_info)
    
# https://mavlink.io/en/messages/common.html#CAMERA_MODE
class CAMERA_MODE(IntEnum):
    IMAGE = 0
    VIDEO = 1
    SURVEY = 2

# https://mavlink.io/en/messages/common.html#MAV_CMD_SET_CAMERA_MODE
class CamSetMode(MissionCommand):
    def __init__(self, camera_mode: CAMERA_MODE = CAMERA_MODE.IMAGE):
        super().__init__(530)
        self.camera_mode = camera_mode

    def params(self, mission_info):
        return [
            0,
            self.camera_mode
        ]

# Doesn't work on Astro
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
# Doesn't work on astro, but look into camera control??
# https://mavlink.io/en/messages/common.html#MAV_CMD_SET_CAMERA_FOCUS
class CamFocusSet(MissionCommand):
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

# Re: CamFocusSet
# https://mavlink.io/en/messages/common.html#SET_FOCUS_TYPE
class CamFocusINF(CamFocusSet):
    def __init__(self):
        super().__init__(2, 100)

# https://mavlink.io/en/messages/common.html#MAV_CMD_SET_CAMERA_MODE
# I don't understand what this one does.
# class CamCTRL(MissionCommand):
#     def __init__(self):
#         super().__init__(203)

#     def params(self, mission_info):
#         return [
#             1,
#             1,
#             1,

#         ]

# 
# https://mavlink.io/en/messages/common.html#MAV_CMD_IMAGE_START_CAPTURE
class CamStartSeq(MissionCommand):
    def __init__(self, interval: int, imgCount: int = 0):
        super().__init__(2000)
        self.interval = interval
        self.imgCount = imgCount

    def params(self, mission_info):
        return [
            0,
            self.interval,
            self.imgCount
        ]

# https://mavlink.io/en/messages/common.html#MAV_CMD_IMAGE_STOP_CAPTURE
class CamStopSeq(MissionCommand):
    def __init__(self):
        super().__init__(2001)

    def params(self, mission_info):
        return [0]
    
# https://mavlink.io/en/messages/common.html#MAV_CMD_VIDEO_START_CAPTURE
class CamStartVideo(MissionCommand):
    def __init__(self):
        super().__init__(2500)

    def params(self, mission_info):
        return [
            0,
            0,
            0
        ]
    
# https://mavlink.io/en/messages/common.html#MAV_CMD_VIDEO_STOP_CAPTURE
class CamStopVideo(MissionCommand):
    def __init__(self):
        super().__init__(2500)

    def params(self, mission_info):
        return [
            0,
            0
        ]

class Return(MissionCommand):
    def __init__(self):
        super().__init__(20)

    def params(self, mission_info):
        return []
# class CamReqCapture(MissionCommand):
#     def __init__(self):
#         super().__init__(2002)
    
#     def params(self, mission_info):
#         return [1]

class StorageFlag(IntEnum):
    STORAGE_USAGE_FLAG_SET = 1
    STORAGE_USAGE_FLAG_PHOTO = 2
    STORAGE_USAGE_FLAG_VIDEO = 4
    STORAGE_USAGE_FLAG_LOGS = 8

class CamSetStorage(MissionCommand):
    def __init__(self, storage_loc, usage: StorageFlag):
        super().__init__(533)
        self.storage = storage_loc
        self.usage = usage

    def params(self, mission_info):
        return [
            self.storage,
            self.usage
        ]
    
# https://mavlink.io/en/messages/common.html#SPEED_TYPE
class SPEED_TYPE(IntEnum):
	SPEED_TYPE_AIRSPEED = 0 #	    Airspeed
	SPEED_TYPE_GROUNDSPEED = 1 #	Groundspeed
	SPEED_TYPE_CLIMB_SPEED = 2 #	Climb speed
	SPEED_TYPE_DESCENT_SPEED = 3 #	Descent speed

    
# https://mavlink.io/en/messages/common.html#MAV_CMD_DO_CHANGE_SPEED
class ChangeSpeed(MissionCommand):
    def __init__(self, speed, mode=SPEED_TYPE.SPEED_TYPE_GROUNDSPEED, throttle=-1):
        super().__init__(178)
        self.mode = mode
        self.speed = speed
        self.throttle = throttle
    
    def params(self, mission_info):
        return [
            self.mode,
            self.speed,
            self.throttle
        ]
