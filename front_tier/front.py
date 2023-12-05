# Import necessary modules
from flask import Flask, request, jsonify
import requests
from datetime import datetime

# Create a Flask web application
app = Flask(__name__)

# Define the URLs for catalog and order servers
CATALOG_SERVER_URL = "http://172.27.144.1:4000"
ORDER_SERVER_URL = "http://172.27.144.1:5000"

# Endpoint for searching items in the catalog based on item type
@app.route('/search/<string:item_type>', methods=['GET'])
def search(item_type):
    """
    Search for items in the catalog based on item type.

    Input:
    - item_type: The type of item to search for (string)

    Output:
    - JSON response containing search results

    Example:
    - GET request: /search/book
    """
    try:
        # Send a GET request to the catalog server
        response = requests.get(f"{CATALOG_SERVER_URL}/books/search/{item_type}")

        # Parse the JSON response from the catalog server
        data = response.json()

        # Log the response for debugging purposes
        app.logger.info(f"Response from catalog server: {data}")

        # Return the response as JSON
        return jsonify(data)
    except Exception as e:
        # Log and return an error message if an exception occurs
        app.logger.error(f"Exception: {str(e)}")
        return jsonify({'error': str(e)}), 500

# Endpoint for retrieving information about a specific item in the catalog
@app.route('/info/<int:item_number>', methods=['GET'])
def info(item_number):
    """
    Retrieve information about a specific item in the catalog.

    Input:
    - item_number: The unique identifier of the item (integer)

    Output:
    - JSON response containing information about the item

    Example:
    - GET request: /info/123
    """
    try:
        # Send a GET request to the catalog server
        response = requests.get(f"{CATALOG_SERVER_URL}/books/{item_number}")

        # Parse the JSON response from the catalog server
        data = response.json()

        # Log the response for debugging purposes
        app.logger.info(f"Response from catalog server: {data}")

        # Return the response as JSON
        return jsonify(data)
    except Exception as e:
        # Log and return an error message if an exception occurs
        app.logger.error(f"Exception: {str(e)}")
        return jsonify({'error': str(e)}), 500

# Endpoint for making a purchase request for a specific item
@app.route('/purchase/<int:item_id>', methods=['POST'])
def purchase(item_id):
    """
    Make a purchase request for a specific item.

    Input:
    - item_id: The unique identifier of the item to purchase (integer)

    Output:
    - JSON response confirming the purchase

    Example:
    - POST request: /purchase/456
    """
    try:
        # Send a POST request to the order server
        response = requests.post(f"{ORDER_SERVER_URL}/purchase/{item_id}")

        # Parse the JSON response from the order server
        data = response.json()

        # Log the response for debugging purposes
        app.logger.info(f"Response from order server: {data}")

        # Return the response as JSON
        return jsonify(data)
    except Exception as e:
        # Log and return an error message if an exception occurs
        app.logger.error(f"Exception: {str(e)}")
        return jsonify({'error': str(e)}), 500

# Run the Flask application on host 0.0.0.0 and port 3000 in debug mode
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000, debug=True)
