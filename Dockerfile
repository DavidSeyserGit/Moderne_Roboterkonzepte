FROM ros:jazzy-ros-base

# Install Nav2 packages and Python
RUN apt-get update && apt-get install -y \
    ros-jazzy-navigation2 \
    ros-jazzy-nav2-bringup \
    ros-jazzy-rviz2 \
    ros-jazzy-turtlebot3* \
    python3-pip \
    python3-venv \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy chatbot files
COPY requirements.txt .
COPY *.py .
COPY system_prompt.txt .

# Create and activate virtual environment
RUN python3 -m venv /app/venv
ENV PATH="/app/venv/bin:$PATH"

# Install Python dependencies
RUN pip install --upgrade pip && pip install -r requirements.txt

# Set environment variables for display passthrough
ENV DISPLAY=${DISPLAY}
ENV QT_X11_NO_MITSHM=1

# Source ROS2 setup on container start
RUN echo "source /opt/ros/jazzy/setup.bash" >> ~/.bashrc

CMD ["/bin/bash"]
