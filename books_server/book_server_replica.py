# replica.py

import os
from flask import Flask, jsonify, make_response, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy import Float, Integer, String, ForeignKey, or_
from datetime import datetime
from flask_socketio import SocketIO

Base = declarative_base()

app_replica = Flask(__name__)
socketio_replica = SocketIO(app_replica, cors_allowed_origins="*")

# Configure SQLAlchemy to use SQLite and set the database URI for the replica
app_replica.config["SQLALCHEMY_DATABASE_URI"] = 'sqlite:///' + \
    os.path.join(os.getcwd(), 'project_replica.db')
app_replica.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db_replica = SQLAlchemy(model_class=Base)
db_replica.init_app(app_replica)


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

# Function to log messages to a file


def log_replica(message):
    with open('./catalog_log_replica.txt', 'a') as logger:
        logger.write(f'{message}\n')

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

    log_replica(
        f'make POST request on /catalogs > add new catalog {datetime.now()}')
    return jsonify({
        'success': True,
        'catalog': catalog_replica.name,
        'catalog_id': catalog_replica.id,
    })




# Endpoint to get all books in the replica


@app_replica.route('/books')
def get_all_books_replica():
    try:
        books = db_replica.session.execute(db_replica.select(
            BookReplica).order_by(BookReplica.id)).scalars()
        books_list = [{'id': book.id, 'name': book.name,
                       'count': book.count, 'price': book.price} for book in books]
        return jsonify({'books': books_list})
    except Exception as e:
        json_response = jsonify({'error': e.__str__()})
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

        return jsonify({
            'count': book.count,
        })
    except Exception as e:
        json_response = jsonify({
            'error': e.__str__()
        })

        return make_response(json_response, 404)

# ... (remaining code)




# Endpoint to decrease the stock count of a book by ID in the replica


@app_replica.route('/books/<int:id>/count/decrease', methods=['PUT'])
def decrease_book_stock_replica(id):
    try:
        book = BookReplica.query.get(id)
        if book:
            if book.count > 0:
                book.count -= 1
                db_replica.session.commit()
                socketio_replica.emit('catalog_change_replica', {'catalog_info': {
                                      'id': book.id, 'name': book.name, 'count': book.count}})
                app_replica.logger.info(
                    f"Emitted catalog_change_replica event for book ID {book.id}")
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

        # Emit a Socket.IO event for catalog change in replica
        socketio_replica.emit('catalog_change_replica', {'catalog_info': {
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

# ... (remaining code)


# Socket.io event handler for handling catalog change in Replica


@socketio_replica.on('catalog_change')
def handle_catalog_change_replica(message):
    catalog_info = message.get('catalog_info')
    if catalog_info:
        print(f"Received catalog change in Replica: {catalog_info}")


# Run the Flask application with SocketIO on host 0.0.0.0 and port 4001 in debug mode
if __name__ == '__main__':
    socketio_replica.run(app_replica, host='0.0.0.0', port=4001, debug=True)
