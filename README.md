# Moderne Roboterkonzepte

A chatbot for robot control using LangChain and OpenRouter.

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Create a `.env` file with your API key:
```bash
echo "OPENROUTER_API_KEY=your-api-key-here" > .env
```

## Run the App

```bash
chainlit run main.py -w
```

Open http://localhost:8000 in your browser.

## Docker Usage

### Build and Start the Container

```bash
touch .env        #falls .env not found
docker compose up -d
xhost +local:docker        #wird benötigt um GUI Fenster zu öffnen
```

### Enter the Container

```bash
docker exec -it nav2-MRK bash
```

### Terminal 1: Start Nav2 Simulation

Inside the container, launch the TurtleBot3 Nav2 simulation:

```bash
source /opt/ros/jazzy/setup.bash
export TURTLEBOT3_MODEL=waffle
ros2 launch nav2_bringup tb3_simulation_launch.py
```

This will open RViz with the Nav2 stack and TurtleBot3 simulation.

### Terminal 2: Start the Chatbot Server

Open a second terminal into the container:

```bash
docker exec -it nav2-MRK bash
```

Then start the Chainlit server:

```bash
source /opt/ros/jazzy/setup.bash
chainlit run main.py -w
```

Open http://localhost:8000 in your browser to interact with the chatbot.

### Verify ROS2 Topics

To check if Nav2 is running correctly:

```bash
source /opt/ros/jazzy/setup.bash
ros2 topic list
```

You should see topics like `/cmd_vel`, `/map`, `/odom`, `/scan`, `/goal_pose`, etc.

### Stop the Container

```bash
docker compose down
```

## Adding a New Tool

Edit `tools.py`:

```python
@tool
def my_new_tool(param: str) -> str:
    """Description of what the tool does."""
    # Your code here
    return "result"

# Add to the list
available_tools = [move_to_pose, my_new_tool]
```

Restart the app to use the new tool.
