## Docker for flask microservices

1. Install Docker
2. bull images

```bash
docker pull alpine
docker pull ubuntu
docker pull debian
```

3. define Dockerfile for each microservice tier

Alpine Dockerfile (For books&catalogs microservice)

``` Docker
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

```

Debian Dockerfile (for Order microservice)

```Docker
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
RUN pip3 install --no-cache-dir -r requirements.txt

# Expose the port on which the application will run
EXPOSE 5000

# Command to run the application
CMD ["python3", "order_server.py"]

```

Ubuntu Dockerfile (For frontend microservice)

```Docker
# Use the official Ubuntu image
FROM ubuntu:latest

# Set the working directory
WORKDIR /app

# Copy the Python server file and requirements file
COPY app.py requirements.txt /app/

# Install Python and pip
RUN apt-get update && \
    apt-get install -y python3 python3-pip && \
    rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip3 install --no-cache-dir -r requirements.txt

# Expose the port on which the application will run
EXPOSE 3000

# Command to run the application
CMD ["python3", "app.py"]

```

Specified Ports and mapping ports::

```text
Books|Alpine > 4000:4000
Orders|Debian > 5000:5000
Frontend|Ubuntu > 3000:3000
```

use this command to build Dockerfile configuration in vscode

```text
ctrl + shift + p
```

next choose docker build image option

### Make SQL database shared with all microservices containers
---

1. create docker volume using this command
```
docker volume create volume-name
```

2. now we have to change SQL path in python flask server as well

```py
# Set the database URI to the path within the Docker volume
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:////data/project.db"

# Other configurations
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
```


3. run all docs and set configurations for volumes and network as all containers should use same network to communicate with each other, recommended network is bridge network connection

``` bash
docker run -d --name books_service --network bridge -p 4000:4000 -v bazzar_database_volume:/data booksserver

-p 4000:4000 -v > specify the mapping port
x:y means if you open port x in browser it will navigate to port y in the container

--name books_service > choose which image to run, image is the one created by ctrl + shift + p

-v bazzar_database_volume > specify which volume will the container use

/data > specify where is the relative path for it and for Database as well
```

4. runs the other two images by doing the same as above instructions

### Finally test all together and it should work as expected