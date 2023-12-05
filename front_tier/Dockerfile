# Use the official Ubuntu image
FROM ubuntu:latest

# Set the working directory
WORKDIR /app

# Copy the Python server file and requirements file
COPY front.py requirements.txt /app/

# Install Python and pip
RUN apt-get update && \
    apt-get install -y python3 python3-pip && \
    rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip3 install --no-cache-dir -r requirements.txt

# Expose the port on which the application will run
EXPOSE 3000

# Command to run the application
CMD ["python3", "front.py"]
