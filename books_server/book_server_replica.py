import os
from flask import Flask, jsonify, make_response, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy import Float, Integer, String, ForeignKey, or_
from datetime import datetime
from flask_socketio import SocketIO
from book_server import Book

Base = declarative_base()

app_replica = Flask(__name__)
socketio_replica = SocketIO(app_replica, cors_allowed_origins="*")

# Configure SQLAlchemy to use SQLite and set the database URI for the replica
app_replica.config["SQLALCHEMY_DATABASE_URI"] = 'sqlite:///' + \
    os.path.join(os.getcwd(), 'project_replica.db')
app_replica.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Initialize SQLAlchemy directly with the Flask app
db_replica = SQLAlchemy(app_replica, model_class=Base)


# Define SQLAlchemy models for Catalog and Book in the replica
class CatalogReplica(db_replica.Model):
    __tablename__ = 'catalog_replica'  # Specify the table name
    id = db_replica.Column(db_replica.Integer, primary_key=True)
    name = db_replica.Column(db_replica.String)


class BookReplica(db_replica.Model):
    __tablename__ = 'book_replica'  # Specify the table name
    id = db_replica.Column(db_replica.Integer, primary_key=True)
    name = db_replica.Column(db_replica.String)
    count = db_replica.Column(db_replica.Integer, default=1)
    price = db_replica.Column(db_replica.Float, default=0)
    catalog_id = db_replica.Column(
        db_replica.Integer, db_replica.ForeignKey(CatalogReplica.id))
    catalog = db_replica.relationship(CatalogReplica)


with app_replica.app_context():
    db_replica.create_all()



# Define a flag to ensure data copy happens only once
data_copy_done = False

# Function to copy data from the original to the replica


# Function to copy data from the original to the replica
def copy_data_from_original_to_replica():
    try:
        global data_copy_done
        if not data_copy_done:
            with app_replica.app_context():
                # Fetch all books from the original database
                books_original = Book.query.all()

                # Copy each book to the replica database
                for book_original in books_original:
                    book_replica = BookReplica(
                        id=book_original.id,
                        name=book_original.name,
                        count=book_original.count,
                        price=book_original.price,
                        catalog_id=book_original.catalog_id
                    )
                    # Add and commit the copied book to the replica database
                    with app_replica.app_context():
                        db_replica.session.add(book_replica)
                        db_replica.session.commit()

              
                data_copy_done = True

        return True

    except Exception as e:
        return False


# Run the data copy function before each request


@app_replica.before_request
def before_request():
    with app_replica.app_context():
        copy_data_from_original_to_replica()


# Socket.io event handler for handling catalog change in replica
@socketio_replica.on('catalog_change_replica')
def handle_catalog_change_replica(message):
    catalog_info = message.get('catalog_info')
    if catalog_info:
        print(f"Received catalog change in Replica: {catalog_info}")
    else:
        app_replica.logger.warning("No catalog_info found in message")

# Socket.io event handler for handling book change in replica


@socketio_replica.on('book_change_replica')
def handle_book_change_replica(message):
    book_info = message.get('book_info')
    if book_info:
        print(f"Received book change in Replica: {book_info}")
    else:
        app_replica.logger.warning("No book_info found in message")

# Socket.io event handler for handling catalog change in origin


@socketio_replica.on('catalog_change')
def handle_catalog_change_origin(message):
    catalog_info = message.get('catalog_info')
    if catalog_info:
        print(f"Received catalog change from Replica to Origin: {
              catalog_info}")
    else:
        app_replica.logger.warning("No catalog_info found in message")

# Socket.io event handler for handling book change in origin


@socketio_replica.on('book_change')
def handle_book_change_origin(message):
    book_info = message.get('book_info')
    if book_info:
        print(f"Received book change from Replica to Origin: {book_info}")
    else:
        app_replica.logger.warning("No book_info found in message")


# Endpoint to get all catalogs in the replica
@app_replica.route('/catalogs')
def get_all_catalogs_replica():
    try:
        catalogs = db_replica.session.execute(
            db_replica.select(CatalogReplica).order_by(CatalogReplica.id)).scalars()
        catalogs_list = [{'id': catalog.id, 'name': catalog.name}
                         for catalog in catalogs]
        return jsonify({'catalogs': catalogs_list})
    except Exception as e:
        json_response = jsonify({'error': e.__str__()})
        return make_response(json_response, 500)

# Endpoint to create a new catalog in the replica


@app_replica.route('/catalogs', methods=['POST'])
def create_catalog_replica():
    try:
        name = request.form['name']
    except:
        json_response = jsonify({'error': 'no name was provided'})
        return make_response(json_response, 400)

    catalog_replica = CatalogReplica(name=name)

    db_replica.session.add(catalog_replica)
    db_replica.session.commit()

    # Emit a Socket.IO event for catalog change to origin
    socketio_replica.emit('catalog_change_replica', {'catalog_info': {
                          'id': catalog_replica.id, 'name': catalog_replica.name}})

    return jsonify({
        'success': True,
        'catalog': catalog_replica.name,
        'catalog_id': catalog_replica.id,
    })



# Endpoint to get all books in the replica


@app_replica.route('/books', methods=['GET'])
def get_all_books_replica():
    try:
        books_replica = BookReplica.query.all()
        books_list_replica = [{'id': book.id, 'name': book.name,
                               'count': book.count, 'price': book.price} for book in books_replica]

        return jsonify({
            'books': books_list_replica
        })

    except Exception as e:
        json_response = jsonify({
            'error': e.__str__()
        })
        return make_response(json_response, 500)

 
# Endpoint to create a new book in the replica
@app_replica.route('/books', methods=['POST'])
def create_book_replica():
    try:
        name = request.form['name']
        catalog = request.form['catalog']
        count = int(request.form['count'])
        price = int(request.form['price'])
    except Exception as exc:
        json_response = jsonify({'error': exc.__str__()})
        return make_response(json_response, 400)

    book_replica = BookReplica(
        name=name,
        catalog_id=catalog,
        count=count,
        price=price,
    )

    db_replica.session.add(book_replica)
    db_replica.session.commit()

    # Emit a Socket.IO event for book change to origin
    socketio_replica.emit('book_change_replica', {'book_info': {
                          'id': book_replica.id, 'name': book_replica.name, 'count': book_replica.count}})

    return jsonify({
        'success': True,
        'book': book_replica.name,
        'book_id': book_replica.id,
    })


# Endpoint to search for books by name in the replica


@app_replica.route('/books/search/<string:name>')
def search_books_replica(name):
    books = db_replica.session.execute(
        db_replica.select(BookReplica).filter_by(name=name)).scalars()
    books_list = [{'name': book.name, 'price': book.price, 'id': book.id}
                  for book in books]
    return jsonify({
        'books': books_list
    })

# Endpoint to get books by name using a search string in the replica


@app_replica.route('/books/find')
def get_book_by_name_replica():
    search_string = request.args.get('name', '')
    books = db_replica.session.query(BookReplica).filter(
        or_(BookReplica.name.like(f"%{search_string}%"))).all()

    book_info = [{
        'id': book.id,
        'name': book.name,
        'count': book.count
    } for book in books]
    return jsonify({
        'books': book_info
    })

# Endpoint to get information about a specific book by ID in the replica


@app_replica.route('/books/<int:id>')
def get_book_replica(id):
    try:
        book = BookReplica.query.filter_by(id=id).first()
        book_info = dict({
            'id': book.id,
            'name': book.name,
            'count': book.count
        })
        return jsonify({
            'books': book_info
        })
    except Exception as exc:
        json_response = jsonify({
            'error': exc.__str__()
        })

        return make_response(json_response, 404)


# Endpoint to increase the stock count of a book by ID in the replica
@app_replica.route('/books/<int:id>/count/increase', methods=['PUT'])
def increase_book_stock_replica(id):
    try:
        book = BookReplica.query.get(id)
        book.count += 1
        db_replica.session.commit()

        # Emit a Socket.IO event for book change to origin
        socketio_replica.emit('book_change_replica', {'book_info': {
                              'id': book.id, 'name': book.name, 'count': book.count}})

        return jsonify({
            'count': book.count,
        })
    except Exception as e:
        json_response = jsonify({
            'error': e.__str__()
        })

        return make_response(json_response, 404)

# Endpoint to decrease the stock count of a book by ID in the replica


@app_replica.route('/books/<int:id>/count/decrease', methods=['PUT'])
def decrease_book_stock_replica(id):
    try:
        book = BookReplica.query.get(id)
        if book:
            if book.count > 0:
                book.count -= 1
                db_replica.session.commit()

                # Emit a Socket.IO event for book change to origin
                socketio_replica.emit('book_change_replica', {'book_info': {
                                      'id': book.id, 'name': book.name, 'count': book.count}})

                return jsonify({'count': book.count})
            else:
                return jsonify({'error': 'Book is already out of stock'}), 403
        else:
            return jsonify({'error': 'Book not found'}), 404
    except Exception as e:
        json_response = jsonify({'error': e.__str__()})
        return make_response(json_response, 500)

# Endpoint to update the price of a book by ID in the replica


@app_replica.route('/books/<int:id>/price', methods=['PUT'])
def update_book_price_replica(id):
    try:
        price = float(request.form['price'])

        book = BookReplica.query.filter_by(id=id).first()
        book.price = price
        db_replica.session.commit()

        # Emit a Socket.IO event for book change to origin
        socketio_replica.emit('book_change_replica', {'book_info': {
                              'id': book.id, 'name': book.name, 'count': book.count}})

        return jsonify({
            'price': book.price,
        })
    except Exception as e:
        json_response = jsonify({
            'error': e.__str__()
        })
        return make_response(json_response, 404)

# Endpoint to check stock availability of a book by ID in the replica


@app_replica.route('/books/<int:id>/stock/availability')
def stock_availability_replica(id):
    book = BookReplica.query.filter_by(id=id).first()
    if book.count == 0:
        json_response = jsonify({
            'success': False,
            'message': 'Out of stock'
        })
        return make_response(json_response, 403)

    return jsonify({
        'success': True,
        'left': book.count
    })




# Run the Flask application with SocketIO on host 0.0.0.0 and port 4001 in debug mode
if __name__ == '__main__':
    socketio_replica.run(app_replica, host='0.0.0.0', port=4001, debug=True)
