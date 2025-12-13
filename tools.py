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

import re

@tool
def check_pose(pose_str: str = "") -> str:
    """
    Reads current robot pose from /amcl_pose and optionally checks distance/yaw error to a target.
    Target can be YAML (x,y,theta, optional tol_xy,tol_theta) or plain numbers: "x y theta [tol_xy tol_theta]".
    """
    try:
        # 1) Read current pose once from AMCL
        cmd = ["bash", "-c", "source /opt/ros/jazzy/setup.bash && ros2 topic echo /amcl_pose --once"]
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        if res.returncode != 0:
            return f"Failed to read /amcl_pose: {res.stderr}"

        docs = [d for d in yaml.safe_load_all(res.stdout) if isinstance(d, dict)]
        if not docs:
            return "Error reading pose: could not parse YAML from /amcl_pose output."
        msg = next((d for d in docs if "pose" in d), docs[0])

        pos = msg["pose"]["pose"]["position"]
        ori = msg["pose"]["pose"]["orientation"]

        siny_cosp = 2.0 * (ori["w"] * ori["z"] + ori["x"] * ori["y"])
        cosy_cosp = 1.0 - 2.0 * (ori["y"] * ori["y"] + ori["z"] * ori["z"])
        theta_cur = math.atan2(siny_cosp, cosy_cosp)

        current = {"x": float(pos["x"]), "y": float(pos["y"]), "theta": float(theta_cur)}

        # 2) No target → just return pose
        pose_str = pose_str or ""
        if not pose_str.strip():
            return yaml.safe_dump(current, sort_keys=False)

        # 3) Parse target (YAML first, else numbers fallback)
        s = pose_str.replace("\t", "    ").replace("ol_xy:", "tol_xy:").replace("ol_theta:", "tol_theta:")
        try:
            target = yaml.safe_load(s)
        except Exception:
            target = None

        if not isinstance(target, dict):
            nums = re.findall(r"[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?", s)
            if len(nums) < 3:
                return "Invalid target pose. Provide YAML (x,y,theta) or 'x y theta [tol_xy tol_theta]'."
            target = {"x": float(nums[0]), "y": float(nums[1]), "theta": float(nums[2])}
            if len(nums) >= 4:
                target["tol_xy"] = float(nums[3])
            if len(nums) >= 5:
                target["tol_theta"] = float(nums[4])

        # Default tolerances = Nav2 general_goal_checker  (system: 0.25 / 0.25)
        tol_xy = 0.25
        tol_theta = 0.25


        dx = current["x"] - float(target["x"])
        dy = current["y"] - float(target["y"])
        dist = math.hypot(dx, dy)
        dtheta = abs((current["theta"] - float(target["theta"]) + math.pi) % (2 * math.pi) - math.pi)
        within = dist <= tol_xy and dtheta <= tol_theta

        return yaml.safe_dump({
            "current_pose": current,
            "target_pose": {"x": float(target["x"]), "y": float(target["y"]), "theta": float(target["theta"])},
            "tolerances": {"tol_xy": tol_xy, "tol_theta": tol_theta},
            "error": {"dx": float(dx), "dy": float(dy), "distance_xy": float(dist), "error_theta": float(dtheta)},
            "within_tolerance": within
        }, sort_keys=False)

    except subprocess.TimeoutExpired:
        return "Timed out waiting for /amcl_pose. Is AMCL running?"
    except Exception as e:
        return f"Error reading pose: {str(e)}"


# List of all available tools
available_tools = [move_to_pose, check_pose]
