# Use the official Alpine Linux image
FROM alpine:latest

# Set the working directory
WORKDIR /app

# Copy the Python server file and requirements file
COPY book_server.py requirements.txt catalog_log.txt /app/

# Install Python and pip
RUN apk add --update --no-cache python3 py3-pip

# Install Python dependencies
RUN pip3 install --no-cache-dir -r requirements.txt

# Expose the port on which the application will run
EXPOSE 4000

# Command to run the application
CMD ["python3", "book_server.py"]
