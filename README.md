# Moderne Roboterkonzepte

A chatbot for robot control using LangChain, OpenRouter, and ROS2 Nav2.

## Architecture

This project uses two Docker containers:
- **nav2-MRK**: Runs the ROS2 Nav2 stack with Gazebo simulation and RViz
- **chatbot-MRK**: Runs the Chainlit chatbot that communicates with Nav2

Both containers share the host's network and IPC namespace for seamless ROS2 DDS communication.

## Prerequisites

- Docker and Docker Compose
- X11 display server (for GUI applications like RViz and Gazebo)
- OpenRouter API key

## Quick Start

### 1. Setup Environment

Create a `.env` file with your API key:
```bash
echo "OPENROUTER_API_KEY=your-api-key-here" > .env
```

### 2. Allow Docker to Access Display

```bash
xhost +local:docker
```

### 3. Build and Start Containers

## On the initial build Docker will take upwards of 10 mins to build, this is due to large python dependencies such as torch and langchain accumulating time.

**Or standard build:**
```bash
docker compose up -d --build
```

The fast build script uses Docker BuildKit with caching for much faster rebuilds (especially for Python dependencies).

This starts both containers:
- The **chatbot** container auto-starts Chainlit on port 8000
- The **nav2** container waits for you to launch the simulation

### 4. Start Nav2 Simulation

Open a terminal into the nav2 container and launch the simulation:

```bash
docker exec -it nav2-MRK bash
```

Inside the container:
```bash
source /opt/ros/jazzy/setup.bash
ros2 launch nav2_bringup tb3_simulation_launch.py headless:=False
```

This opens:
- **Gazebo**: 3D robot simulation
- **RViz**: Visualization and control interface

### 5. Use the Chatbot

Open http://localhost:8000 in your browser to interact with the robot through natural language.

Example commands:
- "Where is the robot?"
- "Move the robot to position x=1, y=2"
- "Navigate to coordinates 3, 4 with orientation 90 degrees"

## Container Management

### View Logs

```bash
# Chatbot logs
docker logs -f chatbot-MRK

# Nav2 container logs
docker logs -f nav2-MRK
```

### Enter Containers

```bash
# Enter chatbot container
docker exec -it chatbot-MRK bash

# Enter nav2 container
docker exec -it nav2-MRK bash
```

### Restart Containers

```bash
docker compose restart
```

### Stop Everything

```bash
docker compose down
```

### Rebuild After Code Changes

**Fast rebuild (uses cache):**
```bash
./build.sh
docker compose up -d
```

**Or force full rebuild (slower):**
```bash
docker compose build --no-cache
docker compose up -d
```

## Verify ROS2 Communication

From the chatbot container, check if topics are visible:

```bash
docker exec -it chatbot-MRK bash -c "source /opt/ros/jazzy/setup.bash && ros2 topic list"
```

You should see topics like `/cmd_vel`, `/map`, `/odom`, `/scan`, `/goal_pose`, `/amcl_pose`, etc.

## Project Structure

```
├── config/
│   └── system_prompt.txt    # AI system prompt configuration
├── docker/
│   ├── Dockerfile.chatbot   # Chatbot container (ROS2 + Python)
│   └── Dockerfile.nav2      # Nav2 container (ROS2 + Navigation)
├── src/
│   ├── main.py              # Chainlit entry point
│   ├── chatbot.py           # LangChain chatbot logic
│   ├── tools.py             # ROS2 tools (move_to_pose, check_pose)
│   └── model_fetcher.py     # OpenRouter model configuration
├── docker-compose.yml       # Container orchestration
├── requirements.txt         # Python dependencies
└── .env                     # API keys (not in git)
```

## Adding a New Tool

Edit `src/tools.py`:

```python
@tool
def my_new_tool(param: str) -> str:
    """Description of what the tool does."""
    # Your ROS2 command here
    cmd = ["bash", "-c", "source /opt/ros/jazzy/setup.bash && ros2 ..."]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    return result.stdout

# Add to the list
available_tools = [move_to_pose, check_pose, my_new_tool]
```

The chatbot will automatically pick up the new tool after restart.

## Troubleshooting

### Display Issues (RViz/Gazebo won't open)

```bash
# Run this on the host before starting containers
xhost +local:docker

# Check your DISPLAY variable
echo $DISPLAY
```

### ROS2 Topics Not Visible Between Containers

Both containers need `ipc: host` and `network_mode: host` in docker-compose.yml (already configured).

### Chatbot Can't Connect to Nav2

Make sure Nav2 simulation is running first, then the chatbot can discover topics.

## Local Development (Without Docker)

```bash
# Install dependencies
pip install -r requirements.txt

# Source ROS2
source /opt/ros/jazzy/setup.bash

# Run chatbot
chainlit run src/main.py -w
```
