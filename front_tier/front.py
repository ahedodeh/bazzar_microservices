from flask import Flask, request, jsonify
import requests
from cachetools import LRUCache
from flask_socketio import SocketIO
import time
app = Flask(__name__)
socketio = SocketIO(app)

cache = LRUCache(maxsize=1000)

CATALOG_SERVER_IPS = ["http://127.0.0.1:4000"]
ORDER_SERVER_URLS = ["http://127.0.0.1:3000"]

server_indices = {
    'search': 0,
    'info': 0,
    'purchase': 0
}

def get_server_index(request_type):
    index = server_indices[request_type]
    server_indices[request_type] = (index + 1) % len(CATALOG_SERVER_IPS)
    return index

def get_data_from_cache_or_server(key, server_urls, endpoint, request_type):
    cached_data = cache.get(key)
    if cached_data:
        app.logger.info(f"Data retrieved from cache for key: {key}")
        return cached_data
    else:
        server_index = get_server_index(request_type)
        server_url = server_urls[server_index]
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
            socketio.emit('cache_invalidate', {'key': key})
            app.logger.info(f"Received catalog change: {catalog_info}")
        else:
            app.logger.warning("No key found in catalog_info")
    else:
        app.logger.warning("No catalog_info found in message")



# Socket.io event handler for order confirmation
@socketio.on('order_confirmation')
def handle_order_confirmation(message):
    order_info = message.get('order_info')
    if order_info:
        book_info = order_info.get('book_info')
        if book_info:
            book_id = book_info.get('id')
            if book_id:
                cache[book_id] = book_info
                app.logger.info(f"Cache updated for book ID {book_id}")

# Endpoint for searching items in the catalog based on item type
@app.route('/search/<string:item_type>', methods=['GET'])
def search(item_type):
    try:
        server_urls = CATALOG_SERVER_IPS
        
        start_time = time.time()

        data = get_data_from_cache_or_server(
            item_type, server_urls, f"books/search/{item_type}", 'search')
        
        end_time = time.time()
        response_time = end_time - start_time
        print(f"Request to Catalog Server ({
              server_urls[get_server_index('search')]})")
        print(f"Request processing time: {response_time} seconds")
        return jsonify(data)
    except Exception as e:
        app.logger.error(f"Exception: {str(e)}")
        return jsonify({'error': str(e)}), 500

# Endpoint for retrieving information about a specific item in the catalog


@app.route('/info/<int:item_number>', methods=['GET'])
def info(item_number):
    try:
        server_urls = CATALOG_SERVER_IPS
        start_time = time.time()

        data = get_data_from_cache_or_server(
            item_number, server_urls, f"books/{item_number}", 'info')
        
        end_time = time.time()
        response_time = end_time - start_time
        print(f"Request to Catalog Server ({
              server_urls[get_server_index('info')]})")
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
    try:
        server_urls = ORDER_SERVER_URLS
        server_index = get_server_index('purchase')
        server_url = server_urls[server_index]

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



# Run the Flask application on host 0.0.0.0 and port 3000 in debug mode
if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
