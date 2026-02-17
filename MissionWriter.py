"""
Astro Mission Planning

An API to create plan files to for the Astro
"""

class MissionWriter(object):
    def __init__(self):
        self.vehicle_type = 2

    def write(self, to_file: str):
        self._write_header()
        self._write_mission()
        print("Need to write to file")
        pass

    def _write_header(self):
        self.plan.update(
            {
                # UUID ?
                "fileType": "Plan",
                "geoFence": {
                    "circles": [],
                    "polygons": [],
                    "version": 2
                },
                "rallyPoints": {
                    "points": [],
                    "version": 2
                },
                "version": 1
            }
        )

    def _get_items(self):
        return [
                {
                    "AMSLAltAboveTerrain": "null",
                    "Altitude": 50,
                    "AltitudeMode": 0,
                    "autoContinue": True,
                    "command": 22,
                    "doJumpId": 1,
                    "frame": 3,
                    "params": [
                        15,
                        0,
                        0,
                        "null",
                        47.3985099,
                        8.5451002,
                        50
                    ],
                    "type": "SimpleItem"
                }
            ]

    def _write_mission(self):
        self.plan.update({
            "cruiseSpeed": self.cruise_speed,
            "hoverSpeed": self.cruise_speed, # Same as cruise but for hovering, for some reason this is diff in the missions....
            "firmwareType": 12, # TODO: CHECK WHAT THE ASTRO USES MAYBE
            "globalPlanAltitudeMode": 1,
            "plannedHomePosition": [
                25.731907796176873,
                -80.1629181,
                4
            ],
            "vehicleType": self.vehicle_type,
            "version": 2
        })
        self.plan.update({
            "items": self._get_items()
        })

class Item(object):
    def __init__(self, type):
        self.type = type
        self.plan = {}

    def encode(self, ID):
        self.plan.update({
            "type": self.type
        })

class SimpleItem(object):
    def __init__(self, alt):
        super().__init__("SimpleItem")

    def encode(self, ID):
        super().encode()
        self.plan.update({
            "MISSION_ITEM_ID": str(ID),
            "autoContinue": True, # If false, pauses mission after every waypoint
            command,
            doJumpId,
            frame,
            groupTag,
            params
        })
# Navigate to waypoint = 16
# Loiter for X turns = 18
# Delay next command = 93 MAV_CMD_NAV_DELAY


# Go to waypoint 16 – MAV_CMD_NAV_WAYPOINT
# Start taking photos 2000 – MAV_CMD_IMAGE_START_CAPTURE
# Loiter 19 
# Can use this if necessary, but I think the start photos command covers it...
# MAV_CMD_IMAGE_STOP_CAPTURE


class ComplexItem(object):
    def __init__(self, ID):
        super().__init__("ComplexItem")