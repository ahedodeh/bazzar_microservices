# Use the official Debian image
FROM debian:latest

# Set the working directory
WORKDIR /app

# Copy the Python server file and requirements file
COPY order_server.py requirements.txt order_log.txt /app/

# Install Python and pip
RUN apt-get update && \
    apt-get install -y python3 python3-pip && \
    rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip3 install --no-cache-dir -r requirements.txt --break-system-packages

# Expose the port on which the application will run
EXPOSE 5000

# Command to run the application
CMD ["python3", "order_server.py"]