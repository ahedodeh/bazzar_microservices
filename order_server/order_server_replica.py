from datetime import datetime
from flask import Flask, make_response, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import Integer, JSON, DATETIME
from sqlalchemy.orm import Mapped, mapped_column
from flask_socketio import SocketIO
import requests

# Define a base class for SQLAlchemy models


class Base(DeclarativeBase):
    pass


# Create a Flask web application
app_replica = Flask(__name__)
socketio_replica = SocketIO(app_replica, cors_allowed_origins="*")

# Configure SQLAlchemy to use SQLite and set the database URI
app_replica.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///project_replica.db"
app_replica.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db_replica = SQLAlchemy(model_class=Base)
db_replica.init_app(app_replica)

# Define SQLAlchemy model for Order in the replica


class OrderReplica(db_replica.Model):
    __tablename__ = 'order_replica'  # Specify the table name
    id = db_replica.Column(db_replica.Integer, primary_key=True)
    book_data = db_replica.Column(db_replica.JSON)
    purchase_date = db_replica.Column(db_replica.DATETIME)
    count = db_replica.Column(db_replica.Integer)


# Create the Order replica table in the database
with app_replica.app_context():
    db_replica.create_all()

# Function to log order information to a file


def log_order(message):
    with open('./order_replica_log.txt', 'a') as logger:
        logger.write(f'{message}\n')

# Socket.io event handler for handling order confirmation


@socketio_replica.on('order_confirmation_replica')
def handle_order_confirmation(message):
    order_info = message.get('order_info')
    if order_info:
        log_order(f"Received order confirmation in Replica: {order_info}")
        # You can add additional logic here if needed


# Define catalog server replica IPs
CATALOG_SERVER_REPLICA_IPS = [
    "http://127.0.0.1:4001"]
catalog_indices = {'purchase': 0}

# Function to get the current catalog server replica index for a given action


def get_catalog_replica_index(action):
    index = catalog_indices[action]
    catalog_indices[action] = (index + 1) % len(CATALOG_SERVER_REPLICA_IPS)
    return index

# Endpoint to purchase a book


@app_replica.route('/purchase/<int:id>', methods=['POST'])
def purchase_book(id):
    """
    Purchase a book.

    Input:
    - Book ID (integer)

    Output:
    - JSON response confirming the purchase or providing an error message

    Example:
    - POST request: /purchase/1
    """
    action = 'purchase'
    catalog_replica_index = get_catalog_replica_index(action)
    catalog_replica_url = CATALOG_SERVER_REPLICA_IPS[catalog_replica_index]
    print(f"Request to Catalog Server Replica ({catalog_replica_url})")

    # Check stock availability from the catalog replica server
    av_response = requests.get(
        f'{catalog_replica_url}/books/{id}/stock/availability')

    if av_response.status_code == 200:
        # Decrease the stock count if the book is available
        decrease_response = requests.put(
            f'{catalog_replica_url}/books/{id}/count/decrease')

        # Check if the stock count decrease was successful
        if decrease_response.status_code == 404:
            return make_response(decrease_response.json(), 404)

        # Retrieve book information after the stock count decrease
        book_info = requests.get(f'{catalog_replica_url}/books/{id}')
        book = book_info.json()

        # Create an Order replica record in the database
        order_replica = OrderReplica(
            book_data=book, purchase_date=datetime.now(), count=1)
        db_replica.session.add(order_replica)
        db_replica.session.commit()

        # Log the order information
        log_order(f"user purchased book {book['books']['name']} at {
                  datetime.now()}, in stock left {decrease_response.json()['count']}")

        # Emit a notification about the order confirmation
        socketio_replica.emit('order_confirmation_replica', {'order_info': {
            'book_info': book,
            'purchase_date': datetime.now(),
            'count': 1,
        }})

        # Return a JSON response confirming the order
        json_response = jsonify({
            'order': {
                'book_info': book,
                'purchase_date': datetime.now(),
                'count': 1,
            }
        })
        return json_response

    else:
        # Return an error response if the book is not available
        json_response = av_response.json()
        return make_response(json_response, 403)


# Run the Flask application with SocketIO on host 0.0.0.0 and port 3000 in debug mode
if __name__ == '__main__':
    socketio_replica.run(app_replica, host='0.0.0.0', port=3001, debug=True)
