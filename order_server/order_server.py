# Import necessary modules
from datetime import datetime
from flask import Flask, render_template, request, make_response, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import Integer, String, ForeignKey, JSON, DATETIME
from sqlalchemy.orm import Mapped, mapped_column
import requests

# Define a base class for SQLAlchemy models
class Base(DeclarativeBase):
    pass

# Create a Flask web application
app = Flask(__name__)

# Configure SQLAlchemy to use SQLite and set the database URI
db = SQLAlchemy(model_class=Base)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:////data/project.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db.init_app(app)

# Define SQLAlchemy model for Order
class Order(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    book_data: Mapped[dict] = mapped_column(JSON)
    purchase_date: Mapped[datetime] = mapped_column(DATETIME)
    count: Mapped[int] = mapped_column(Integer)

# Create the Order table in the database
with app.app_context():
    db.create_all()

# Endpoint to purchase a book
@app.post('/purchase/<int:id>')
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
    # Check stock availability from the catalog server
    av_response = requests.get(f'http://172.27.144.1:4000/books/{id}/stock/availability')

    if av_response.status_code == 200:
        # Decrease the stock count if the book is available
        decrease_response = requests.put(f'http://172.27.144.1:4000/books/{id}/count/decrease')

        # Check if the stock count decrease was successful
        if decrease_response.status_code == 404:
            return make_response(decrease_response.json(), 404)

        # Retrieve book information after the stock count decrease
        book_info = requests.get(f'http://172.27.144.1:4000/books/{id}')
        book = book_info.json()

        # Create an Order record in the database
        order = Order(book_data=book, purchase_date=datetime.now(), count=1)
        db.session.add(order)
        db.session.commit()

        # Log the order information
        with open('./order_log.txt', 'a') as log:
            log.write(f'user purchased book {book["books"]["name"]} at {datetime.now()}, in stock left {decrease_response.json()["count"]}\n')

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

# Run the Flask application on host 0.0.0.0 and port 5000 in debug mode
if __name__ == '__main__':
    app.run('0.0.0.0', port=5000, debug=True)
