# tools.py - LLM tools for robot control and document search
import threading
import time
import math
import yaml

import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
from rclpy.executors import MultiThreadedExecutor
from rclpy.qos import QoSProfile, DurabilityPolicy
from geometry_msgs.msg import PoseWithCovarianceStamped
from nav2_msgs.action import NavigateToPose

from langchain_core.tools import tool  # @tool decorator exposes functions to the LLM

from rag import retrieve_context, index_all_pdfs, auto_index_if_needed

# Global ROS2 node reference - shared across all tool calls
ros_node = None
ros_executor = None
ros_thread = None


class RobotToolsNode(Node):
    """
    ROS2 node that provides robot control capabilities.
    Subscribes to /amcl_pose for localization and uses NavigateToPose action for movement.
    """

    def __init__(self):
        super().__init__('robot_tools_node')

        # Action client for Nav2 navigation stack
        self.nav_client = ActionClient(self, NavigateToPose, '/navigate_to_pose')

        # Subscribe to AMCL pose with TRANSIENT_LOCAL QoS
        # TRANSIENT_LOCAL: receives last published message even if we subscribed after it was sent
        qos_profile = QoSProfile(depth=10, durability=DurabilityPolicy.TRANSIENT_LOCAL)
        self.current_pose = None
        self.pose_sub = self.create_subscription(
            PoseWithCovarianceStamped,
            '/amcl_pose',
            self.pose_callback,
            qos_profile
        )
        self.get_logger().info("RobotToolsNode initialized.")

    def pose_callback(self, msg):
        """Stores latest pose from AMCL (Adaptive Monte Carlo Localization)."""
        self.current_pose = msg


def ensure_ros_node_started():
    """Initializes ROS2 and starts the node in a background thread (singleton pattern)."""
    global ros_node, ros_executor, ros_thread

    try:
        if not rclpy.ok():
            rclpy.init(args=None)

        if ros_node is None:
            ros_node = RobotToolsNode()
            ros_executor = MultiThreadedExecutor()
            ros_executor.add_node(ros_node)

            # Spin in background thread so tools don't block
            ros_thread = threading.Thread(target=ros_executor.spin, daemon=True)
            ros_thread.start()

    except Exception as e:
        print(f"Error initializing ROS node: {e}")


# Initialize ROS2 on module import
ensure_ros_node_started()

# Auto-index PDFs on startup if needed
try:
    status = auto_index_if_needed()
    print(f"[RAG] {status}")
except Exception as e:
    print(f"[RAG] Auto-index check failed: {e}")


@tool
def move_to_pose(pose_str: str) -> str:
    """
    Sends a navigation goal to Nav2 to move the robot to a specified pose.
    Non-blocking - returns immediately after goal is sent.

    Args:
        pose_str: YAML string with x, y, theta (radians). Example: "x: 1.0\ny: 2.0\ntheta: 1.57"

    Returns:
        Status message indicating if goal was sent successfully.
    """
    global ros_node
    if ros_node is None:
        return "Error: ROS 2 node is not initialized."

    try:
        # Parse YAML pose input
        pose = yaml.safe_load(pose_str)
        x = float(pose['x'])
        y = float(pose['y'])
        theta = float(pose['theta'])

        # Convert theta (yaw angle) to quaternion for ROS
        # Only z and w components needed for 2D rotation around z-axis
        qz = math.sin(theta / 2.0)
        qw = math.cos(theta / 2.0)

        # Build NavigateToPose goal message
        goal_msg = NavigateToPose.Goal()
        goal_msg.pose.header.frame_id = 'map'
        goal_msg.pose.header.stamp = ros_node.get_clock().now().to_msg()
        goal_msg.pose.pose.position.x = x
        goal_msg.pose.pose.position.y = y
        goal_msg.pose.pose.position.z = 0.0
        goal_msg.pose.pose.orientation.x = 0.0
        goal_msg.pose.pose.orientation.y = 0.0
        goal_msg.pose.pose.orientation.z = qz
        goal_msg.pose.pose.orientation.w = qw

        # Wait for action server to be available
        if not ros_node.nav_client.wait_for_server(timeout_sec=2.0):
            return "Error: NavigateToPose action server not available."

        # Send goal asynchronously (non-blocking)
        future = ros_node.nav_client.send_goal_async(goal_msg)

        return f"Navigation goal sent to x={x}, y={y}, theta={theta}. Movement started."

    except Exception as e:
        return f"Error sending navigation goal: {str(e)}"


@tool
def check_pose(pose_str: str = "") -> str:
    """
    Reads current robot pose from AMCL. Optionally compares to a target pose.

    Args:
        pose_str: Optional target pose as YAML (x,y,theta) or "x y theta [tol_xy tol_theta]"

    Returns:
        Current pose, or comparison with target including distance error and tolerance check.
    """
    global ros_node
    if ros_node is None:
        return "Error: ROS 2 node is not initialized."

    if ros_node.current_pose is None:
        return "Waiting for /amcl_pose data... (Robot might not be localized yet)"

    try:
        # Extract current pose from cached AMCL message
        msg = ros_node.current_pose
        pos = msg.pose.pose.position
        ori = msg.pose.pose.orientation

        # Convert quaternion to yaw angle (theta)
        # Formula: yaw = atan2(2*(w*z + x*y), 1 - 2*(y² + z²))
        siny_cosp = 2.0 * (ori.w * ori.z + ori.x * ori.y)
        cosy_cosp = 1.0 - 2.0 * (ori.y * ori.y + ori.z * ori.z)
        theta_cur = math.atan2(siny_cosp, cosy_cosp)

        current = {"x": float(pos.x), "y": float(pos.y), "theta": float(theta_cur)}

        # If no target provided, just return current pose
        pose_str = pose_str or ""
        if not pose_str.strip():
            return yaml.safe_dump(current, sort_keys=False)

        # Parse target pose (try YAML first, then space-separated numbers)
        import re
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

        # Default tolerances
        tol_xy = target.get("tol_xy", 0.25)
        tol_theta = target.get("tol_theta", 0.25)

        # Calculate errors
        dx = current["x"] - float(target["x"])
        dy = current["y"] - float(target["y"])
        dist = math.hypot(dx, dy)
        # Normalize angle difference to [-pi, pi]
        dtheta = abs((current["theta"] - float(target["theta"]) + math.pi) % (2 * math.pi) - math.pi)
        within = dist <= tol_xy and dtheta <= tol_theta

        return yaml.safe_dump({
            "current_pose": current,
            "target_pose": {"x": float(target["x"]), "y": float(target["y"]), "theta": float(target["theta"])},
            "tolerances": {"tol_xy": tol_xy, "tol_theta": tol_theta},
            "error": {"dx": float(dx), "dy": float(dy), "distance_xy": float(dist), "error_theta": float(dtheta)},
            "within_tolerance": within
        }, sort_keys=False)

    except Exception as e:
        return f"Error checking pose: {str(e)}"


@tool
def index_pdfs() -> str:
    """Re-indexes all PDFs in data/pdfs into the Chroma vector database."""
    return index_all_pdfs()


@tool
def search_docs(query: str, k: int = 4) -> str:
    """
    Searches indexed PDFs for information relevant to the query.
    Uses semantic similarity (not keyword matching) via RAG.

    Args:
        query: The question or search query
        k: Number of document chunks to retrieve (default 4)

    Returns:
        Relevant document excerpts with sources, or "NICHT IN DOKUMENTEN" if nothing found.
    """
    context, sources = retrieve_context(query, k=k)
    if not context:
        return "NICHT IN DOKUMENTEN"
    return context + "\n\nQuellen:\n" + "\n".join(sources)


# List of tools available to the LLM
available_tools = [check_pose, move_to_pose, index_pdfs, search_docs]
