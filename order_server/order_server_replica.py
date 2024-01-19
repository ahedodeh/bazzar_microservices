# order_server_replica.py
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

catalog_replica_url = "http://127.0.0.1:4001"

# SocketIO event handler for handling order confirmation in the replica


@socketio_replica.on('order_confirmation_replica')
def handle_order_confirmation_replica(message):
    order_info = message.get('order_info')
    if order_info:
        # You can process the order confirmation in the replica as needed
        print(f"Order confirmation received in Replica: {order_info}")
    else:
        print("No order_info found in message")


# Function to get the current catalog server replica index for a given action
catalog_indices = {'purchase': 0}




# Endpoint to purchase a book


@app_replica.route('/purchase/<int:id>', methods=['POST'])
def purchase_book(id):
   

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


# Run the Flask application with SocketIO on host 0.0.0.0 and port 3001 in debug mode
if __name__ == '__main__':
    socketio_replica.run(app_replica, host='0.0.0.0', port=3001, debug=True)
