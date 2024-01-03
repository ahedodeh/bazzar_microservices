from flask import Flask, request, jsonify
import requests
from cachetools import LRUCache
from flask_socketio import SocketIO

app = Flask(__name__)

socketio = SocketIO(app)

cache = LRUCache(maxsize=1000)

CATALOG_SERVER_IPS = ["http://127.0.0.1:4000", "http://192.168.2.105:4000"]
ORDER_SERVER_URLS = ["http://127.0.0.1:5000", "http://192.168.2.105:5000"]

server_index = 0


# Function to switch to the next server
def switch_server():
    global server_index
    server_index = (server_index + 1) % len(CATALOG_SERVER_IPS)


def get_data_from_cache_or_server(key, server_urls, endpoint):
    cached_data = cache.get(key)
    if cached_data:
        app.logger.info(f"Data retrieved from cache for key: {key}")
        return cached_data
    else:
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
    cache.pop(key, None)

# Endpoint for searching items in the catalog based on item type


@app.route('/search/<string:item_type>', methods=['GET'])
def search(item_type):
    try:
        server_urls = CATALOG_SERVER_IPS
        data = get_data_from_cache_or_server(
            item_type, server_urls, f"books/search/{item_type}")
        # Added: Print server IP with each request
        print(f"Request to Catalog Server ({server_urls[server_index]})")
        switch_server()  # Switch to the next server for the next request
        return jsonify(data)
    except Exception as e:
        app.logger.error(f"Exception: {str(e)}")
        return jsonify({'error': str(e)}), 500

# Endpoint for retrieving information about a specific item in the catalog


@app.route('/info/<int:item_number>', methods=['GET'])
def info(item_number):
    try:
        server_urls = CATALOG_SERVER_IPS
        data = get_data_from_cache_or_server(
            item_number, server_urls, f"books/{item_number}")
        # Added: Print server IP with each request
        print(f"Request to Catalog Server ({server_urls[server_index]})")
        switch_server()  # Switch to the next server for the next request
        return jsonify(data)
    except Exception as e:
        app.logger.error(f"Exception: {str(e)}")
        return jsonify({'error': str(e)}), 500

# Endpoint for making a purchase request for a specific item


@app.route('/purchase/<int:item_id>', methods=['POST'])
def purchase(item_id):
    try:
        server_urls = ORDER_SERVER_URLS
        server_url = server_urls[server_index]
        response = requests.post(f"{server_url}/purchase/{item_id}")
        data = response.json()

        if response.status_code == 200:
            # Invalidate the cache for the purchased item
            invalidate_cache(item_id)
            # Emit a notification about the update
            socketio.emit('cache_invalidate', {'key': item_id})

        app.logger.info(f"Response from order server {server_url}: {data}")
        # Added: Print server IP with each request
        print(f"Request to Order Server ({server_url})")
        switch_server()  # Switch to the next server for the next request
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

# Socket.io event handler for cache invalidation


@socketio.on('cache_invalidate')
def handle_cache_invalidate(message):
    key = message.get('key')
    invalidate_cache(key)
    app.logger.info(f"Cache invalidated for key: {key}")


# Run the Flask application on host 0.0.0.0 and port 3000 in debug mode
if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=3000, debug=True)
