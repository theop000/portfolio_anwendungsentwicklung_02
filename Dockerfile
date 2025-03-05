# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt


# Copy the current directory contents into the container
COPY . .

# Make port 8050 available to the world outside this container
EXPOSE 8050

# Create a startup script
RUN echo '#!/bin/bash\n\
    python main.py\n'\
    > /app/start.sh

# Make the startup script executable
RUN chmod +x /app/start.sh

# Run the startup script when the container launches
CMD ["/app/start.sh"] 