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
        Status message indicating if the goal was sent successfully.
    """

    # parse the pose string
    pose = yaml.safe_load(pose_str)
    # extract x,y, theta from pose_str
    x = pose['x']
    y = pose['y']
    theta = pose['theta']

    # compute quaternion from theta
    qz = math.sin(theta / 2.0)
    qw = math.cos(theta / 2.0)  # assuming roll and pitch are 0 -> motion model from a planar mobile robot

    # Construct the ros2 action send_goal command
    goal_msg = (
        f"{{pose: {{header: {{frame_id: 'map'}}, "
        f"pose: {{position: {{x: {x}, y: {y}, z: 0.0}}, "
        f"orientation: {{x: 0.0, y: 0.0, z: {qz}, w: {qw}}}}}}}}}"
    )

    cmd = [
        "bash", "-c",
        f"source /opt/ros/jazzy/setup.bash && "
        f"ros2 action send_goal /navigate_to_pose nav2_msgs/action/NavigateToPose \"{goal_msg}\""
    ]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60  # timeout after 60 seconds
        )
        
        if result.returncode == 0:
            return f"Navigation goal sent successfully to x={x}, y={y}, theta={theta}.\nOutput: {result.stdout}"
        else:
            return f"Failed to send navigation goal. Error: {result.stderr}"
    except subprocess.TimeoutExpired:
        return f"Navigation goal sent to x={x}, y={y}, theta={theta}. Navigation in progress (timed out waiting for completion)."
    except Exception as e:
        return f"Error sending navigation goal: {str(e)}"


# List of all available tools
available_tools = [move_to_pose]
