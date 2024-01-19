from flask import Flask, request, jsonify
import requests
from cachetools import LRUCache
from flask_socketio import SocketIO
import time

app = Flask(__name__)
socketio = SocketIO(app)

cache = LRUCache(maxsize=1000)

CATALOG_SERVER_IPS = ["http://127.0.0.1:4000", "http://127.0.0.1:4001"]
ORDER_SERVER_URLS = ["http://127.0.0.1:3000", "http://127.0.0.1:3001"]

# round robin algorithm to detect the server ip 
server_indices = {
    'search': 0,
    'info': 0,
    'purchase': 0
}


def get_order_server_url():
    index = server_indices['purchase']
    server_indices['purchase'] = (index + 1) % len(ORDER_SERVER_URLS)
    return ORDER_SERVER_URLS[index]


def get_catalog_server_url(request_type):
    index = server_indices[request_type]
    server_indices[request_type] = (index + 1) % len(CATALOG_SERVER_IPS)
    return CATALOG_SERVER_IPS[index]


def get_data_from_cache_or_server(key, server_url, endpoint, request_type):
    cached_data = cache.get(key)
    if cached_data:
        app.logger.info(f"Data retrieved from cache for key: {key}")
        return cached_data
    else:
        response = requests.get(f"{server_url}/{endpoint}")
        if response.status_code == 200:
            data = response.json()
            app.logger.info(f"Data retrieved from server {
                            server_url} for key: {key}")
            cache[key] = data  # Cache the data
            return data
        return {'error': f'Server {server_url} failed to respond'}, 500


def invalidate_cache(key):
    app.logger.info(f"Invalidating cache for key: {key}")
    if key in cache:
        cache.pop(key)
        app.logger.info(f"Cache invalidated successfully for key: {key}")
    else:
        app.logger.warning(
            f"Key not found in the cache for invalidation: {key}")

# Socket.io event handler for cache invalidation


@socketio.on('cache_invalidate')
def handle_cache_invalidate(message):
    key = message.get('key')
    invalidate_cache(key)
    app.logger.info(f"Cache invalidated for key: {key}")

# Socket.io event handler for handling catalog change


@socketio.on('catalog_change')
def handle_catalog_change(message):
    catalog_info = message.get('catalog_info')
    if catalog_info:
        key = catalog_info.get('id')
        if key:
            invalidate_cache(key)
            socketio.emit('cache_invalidate', {
                          'key': key}, callback=handle_ack)
            app.logger.info(f"Received catalog change: {catalog_info}")
        else:
            app.logger.warning("No key found in catalog_info")
    else:
        app.logger.warning("No catalog_info found in message")

# Socket.io event handler for order confirmation from the order server


@socketio.on('order_confirmation_original')
def handle_order_confirmation_original(message):
    order_info = message.get('order_info')
    if order_info:
        book_info = order_info.get('book_info')
        if book_info:
            book_id = book_info.get('id')
            if book_id:
                # Invalidate the cache for the purchased item
                invalidate_cache(book_id)
                # Emit a notification about the update
                socketio.emit('cache_invalidate', {
                              'key': book_id}, callback=handle_ack)
                print("Order server made a change (Front Server)")
            else:
                app.logger.warning("No book ID found in order_info")
        else:
            app.logger.warning("No book_info found in order_info")
    else:
        app.logger.warning("No order_info found in message")


def handle_ack():
    print("Acknowledgment received")

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
        server_url = get_catalog_server_url('search')
        start_time = time.time()

        data = get_data_from_cache_or_server(
            item_type, server_url, f"books/search/{item_type}", 'search')

        end_time = time.time()
        response_time = end_time - start_time
        print(f"Request to Catalog Server ({server_url})")
        print(f"Request processing time: {response_time} seconds")
        return jsonify(data)
    except Exception as e:
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
        server_url = get_catalog_server_url('info')
        start_time = time.time()

        data = get_data_from_cache_or_server(
            item_number, server_url, f"books/{item_number}", 'info')

        end_time = time.time()
        response_time = end_time - start_time
        print(f"Request to Catalog Server ({server_url})")
        print(f"Request processing time: {response_time} seconds")

        # Emit a socket.io event for cache invalidation
        socketio.emit('cache_invalidate', {'key': item_number})

        return jsonify(data)
    except Exception as e:
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
        server_url = get_order_server_url()
        start_time = time.time()

        response = requests.post(f"{server_url}/purchase/{item_id}")
        data = response.json()
        end_time = time.time()
        response_time = end_time - start_time
        print(f"Request processing time: {response_time} seconds")

        if response.status_code == 200:
            # Invalidate the cache for the purchased item
            invalidate_cache(item_id)
            # Emit a notification about the update
            socketio.emit('cache_invalidate', {'key': item_id})
            print("Order server made a change")

        app.logger.info(f"Response from order server {server_url}: {data}")
        print(f"Request to Order Server ({server_url})")
        return jsonify(data)
    except Exception as e:
        app.logger.error(f"Exception: {str(e)}")
        return jsonify({'error': str(e)}), 500

# Endpoint to get all cached data


@app.route('/cached_data', methods=['GET'])
def get_cached_data():
    try:
        cached_data = {key: cache[key] for key in cache.keys()}
        app.logger.info(f"All cached data: {cached_data}")
        return jsonify(cached_data)
    except Exception as e:
        app.logger.error(f"Exception: {str(e)}")
        return jsonify({'error': str(e)}), 500


# Run the Flask application on host 0.0.0.0 and port 5000 in debug mode
if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
