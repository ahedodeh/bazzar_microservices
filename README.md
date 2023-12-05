```txt
Read bazzar_microservices_docker_explain_steps.docx 
to know how we built this project using microservices

Read Design_Document + how to run it + improvements.docx 
to get info about system design, how to run it and improvements for it
```

## project done list

1. A well documented code and project
2. Included all documentations inside the docs folder
3. Outputs images in outputs folder
4. a well documented docker setup in docker_setup.md file
5. Included all possible issues in issues.md

<br>
<br>
<br>

# Documentation of API Endpoints
### books server api

# Flask Book Catalog API

This is a simple Flask-based API for managing a book catalog. It allows you to create catalogs, add books to them, search for books by name, and retrieve book information by ID. The API uses a SQLite database to store catalog and book data.

## Prerequisites

Before running the application, make sure you have the following installed:

- Python 3
- Flask
- Flask-SQLAlchemy

You can install Flask and Flask-SQLAlchemy using `pip`:

```bash
pip install -r requirements.txt
```


## API Endpoints

### Get All Catalogs

- **URL**: `/catalogs`
- **Method**: `GET`
- **Description**: Retrieve a list of all catalogs.
- **Response**:
  - Success: JSON object with a list of catalogs.
  - Error: JSON object with an error message.

### Create Catalog

- **URL**: `/catalogs`
- **Method**: `POST`
- **Description**: Create a new catalog.
- **Request Parameters**:
  - `name` (required): The name of the new catalog.
- **Response**:
  - Success: JSON object with the created catalog information.
  - Error: JSON object with an error message.

### Get All Books

- **URL**: `/books`
- **Method**: `GET`
- **Description**: Retrieve a list of all books in the catalog.
- **Response**:
  - Success: JSON object with a list of books.
  - Error: JSON object with an error message.

### Create Book

- **URL**: `/books`
- **Method**: `POST`
- **Description**: Create a new book in the catalog.
- **Request Parameters**:
  - `name` (required): The name of the new book.
  - `catalog` (required): The ID of the catalog to which the book belongs.
  - `count` (required): The count of the book in the catalog.
- **Response**:
  - Success: JSON object with the created book information.
  - Error: JSON object with an error message.

### Search Books by Catalog ID

- **URL**: `/books/search/<int:id>`
- **Method**: `GET`
- **Description**: Retrieve a list of books in a specific catalog by catalog ID.
- **Response**:
  - Success: JSON object with a list of books in the specified catalog.
  - Error: JSON object with an error message.

### Search Books by Name

- **URL**: `/books/find`
- **Method**: `GET`
- **Description**: Search for books by name or part of the name.
- **Request Parameters**:
  - `name` (optional): The name or part of the name to search for.
- **Response**:
  - Success: JSON object with a list of books matching the search criteria.
  - Error: JSON object with an error message.

### Get Book by ID

- **URL**: `/books/<int:id>`
- **Method**: `GET`
- **Description**: Retrieve detailed information about a book by its ID.
- **Response**:
  - Success: JSON object with the book's information.
  - Error: JSON object with an error message.



# Order Server API Endpoints

### Purchase Book

- **URL**: `/purchase/<int:id>`
- **Method**: `POST`
- **Description**: Purchase a book by ID.
- **Request Parameters**: 
- - `id` (required): The ID of the book to be purchased.
- **Response**:
  - Success: JSON object with order details.
  - Error: JSON object with an error message.


# Front Tier Server Endpoints (Acts As Client)

### Search Book

- **URL**: `/search/<string:item_type>`
- **Method**: `GET`
- **Description**: Get a book by it's Name.

### Get Book

- **URL**: `/info/<int:item_number>`
- **Method**: `GET`
- **Description**: Get a book by it's ID.

### Purchase Book

- **URL**: `/purchase/<int:item_id>`
- **Method**: `POST`
- **Description**: Purchase a book by it's ID.