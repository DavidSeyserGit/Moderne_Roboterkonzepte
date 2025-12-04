import socket
import subprocess
import math
import yaml
from langchain_core.tools import tool

@tool
def move_to_pose(pose_str: str) -> str:
    """
    Sends a navigation goal to the nav2 stack to move the robot to a specified pose.
    
    Args:
        pose_str: A YAML string containing x, y, and theta values for the target pose.
                  Example: "x: 1.0\ny: 2.0\ntheta: 1.57"
    
    Returns:
        The constructed goal message in YAML format.
    """

    # parse the pose string
    pose = yaml.safe_load(pose_str)
    # extract x,y, theta from pose_str
    x = pose['x']
    y = pose['y']
    theta = pose['theta']

    # compute quaternion from theta
    qz = math.sin(theta / 2.0)
    qw = math.cos(theta / 2.0) # assuming roll and pitch are 0 -> motion model from a planar mobile robot

    # construct the goal string in yaml
    goal = f"""{{
        pose: {{
            header: {{
            frame_id: "map"
            }},
            pose: {{
            position: {{x: {x}, y: {y}, z: 0.0}},
            orientation: {{x: 0.0, y: 0.0, z: {qz}, w: {qw}}}
            }}
        }}
    }}"""

    # check if the action server of nav2 is running

    # Send the pose to the nav2 stack
    return goal


# List of all available tools
available_tools = [move_to_pose]
