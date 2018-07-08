# This Dockerfile will only work with host networking enabled.

# Use an official Python runtime as a parent image
FROM python:3

# Set the working directory to /app
WORKDIR /app

# Copy the current directory contents into the container at /app
ADD . /app

# Install any needed packages specified in requirements.txt
RUN pip install -r requirements.txt

# Define environment variables
ENV SERIAL_PORT "/dev/ttyS0"

ENV MQTT_SERVER "iot.eclipse.org"
ENV MQTT_USERNAME ""
ENV MQTT_PASSWORD ""
ENV MQTT_ROOT "pipswitch"
ENV MQTT_CLIENT_NAME "pipswitch"

# Run app.sh when the container launches
CMD ["./app.sh"]
