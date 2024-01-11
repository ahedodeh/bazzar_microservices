from flask import Flask, request, jsonify
import requests
from cachetools import LRUCache
from flask_socketio import SocketIO
import time

app_replica = Flask(__name__)
socketio_replica = SocketIO(app_replica)

cache_replica = LRUCache(maxsize=1000)

CATALOG_SERVER_REPLICA_IPS = ["http://127.0.0.1:4001"]
ORDER_SERVER_REPLICA_URLS = ["http://127.0.0.1:3001"]

server_replica_indices = {
    'search': 0,
    'info': 0,
    'purchase': 0
}


def get_server_replica_index(request_type):
    index = server_replica_indices[request_type]
    server_replica_indices[request_type] = (index + 1) % len(CATALOG_SERVER_REPLICA_IPS)
    return index


def get_data_from_cache_or_server_replica(key, server_replica_urls, endpoint, request_type):
    cached_data = cache_replica.get(key)
    if cached_data:
        app_replica.logger.info(f"Data retrieved from cache for key: {key}")
        return cached_data
    else:
        server_replica_index = get_server_replica_index(request_type)
        server_replica_url = server_replica_urls[server_replica_index]
        response = requests.get(f"{server_replica_url}/{endpoint}")
        if response.status_code == 200:
            data = response.json()
            app_replica.logger.info(f"Data retrieved from server replica {server_replica_url} for key: {key}")
            cache_replica[key] = data  # Cache the data
            return data
        return {'error': f'Server replica {server_replica_url} failed to respond'}, 500


def invalidate_cache_replica(key):
    app_replica.logger.info(f"Invalidating cache for key: {key}")
    if key in cache_replica:
        cache_replica.pop(key)
        app_replica.logger.info(f"Cache invalidated successfully for key: {key}")
    else:
        app_replica.logger.warning(f"Key not found in the cache for invalidation: {key}")


# Socket.io event handler for cache invalidation
@socketio_replica.on('cache_invalidate_replica')
def handle_cache_invalidate_replica(message):
    key = message.get('key')
    invalidate_cache_replica(key)
    app_replica.logger.info(f"Cache invalidated for key: {key}")


# Socket.io event handler for handling catalog replica change
@socketio_replica.on('catalog_change_replica')
def handle_catalog_change_replica(message):
    catalog_info_replica = message.get('catalog_info_replica')
    if catalog_info_replica:
        key = catalog_info_replica.get('id')
        if key:
            invalidate_cache_replica(key)
            socketio_replica.emit('cache_invalidate_replica', {'key': key})
            app_replica.logger.info(f"Received catalog change replica: {catalog_info_replica}")
        else:
            app_replica.logger.warning("No key found in catalog_info_replica")
    else:
        app_replica.logger.warning("No catalog_info_replica found in message")


# Socket.io event handler for order confirmation replica
@socketio_replica.on('order_confirmation_replica')
def handle_order_confirmation_replica(message):
    order_info_replica = message.get('order_info_replica')
    if order_info_replica:
        book_info_replica = order_info_replica.get('book_info_replica')
        if book_info_replica:
            book_id_replica = book_info_replica.get('id')
            if book_id_replica:
                cache_replica[book_id_replica] = book_info_replica
                app_replica.logger.info(f"Cache updated for book ID replica {book_id_replica}")


# Endpoint for searching items in the catalog replica based on item type
@app_replica.route('/search_replica/<string:item_type_replica>', methods=['GET'])
def search_replica(item_type_replica):
    try:
        server_replica_urls = CATALOG_SERVER_REPLICA_IPS
        start_time = time.time()

        data_replica = get_data_from_cache_or_server_replica(
            item_type_replica, server_replica_urls, f"books/search/{item_type_replica}", 'search')
        
        end_time = time.time()
        response_time = end_time - start_time
        print(f"Request to Catalog Server Replica ({server_replica_urls[get_server_replica_index('search')]})")
        print(f"Request processing time: {response_time} seconds")
        return jsonify(data_replica)
    except Exception as e:
        app_replica.logger.error(f"Exception: {str(e)}")
        return jsonify({'error': str(e)}), 500


# Endpoint for retrieving information about a specific item in the catalog replica
@app_replica.route('/info_replica/<int:item_number_replica>', methods=['GET'])
def info_replica(item_number_replica):
    try:
        server_replica_urls = CATALOG_SERVER_REPLICA_IPS
        start_time = time.time()

        data_replica = get_data_from_cache_or_server_replica(
            item_number_replica, server_replica_urls, f"books/{item_number_replica}", 'info')
        
        end_time = time.time()
        response_time = end_time - start_time
        print(f"Request to Catalog Server Replica ({server_replica_urls[get_server_replica_index('info')]})")
        print(f"Request processing time: {response_time} seconds")

        # Emit a socket.io event for cache invalidation replica
        socketio_replica.emit('cache_invalidate_replica', {'key': item_number_replica})

        return jsonify(data_replica)
    except Exception as e:
        app_replica.logger.error(f"Exception: {str(e)}")
        return jsonify({'error': str(e)}), 500


# Endpoint for making a purchase request for a specific item replica
@app_replica.route('/purchase_replica/<int:item_id_replica>', methods=['POST'])
def purchase_replica(item_id_replica):
    try:
        server_replica_urls = ORDER_SERVER_REPLICA_URLS
        server_replica_index = get_server_replica_index('purchase')
        server_replica_url = server_replica_urls[server_replica_index]

        start_time = time.time()

        response_replica = requests.post(f"{server_replica_url}/purchase/{item_id_replica}")
        data_replica = response_replica.json()
        end_time = time.time()
        response_time = end_time - start_time
        print(f"Request processing time: {response_time} seconds")

        if response_replica.status_code == 200:
            # Invalidate the cache for the purchased item replica
            invalidate_cache_replica(item_id_replica)
            # Emit a notification about the update replica
            socketio_replica.emit('cache_invalidate_replica', {'key': item_id_replica})
            print("Order server made a change replica")

        app_replica.logger.info(f"Response from order server replica {server_replica_url}: {data_replica}")
        print(f"Request to Order Server Replica ({server_replica_url})")
        return jsonify(data_replica)
    except Exception as e:
        app_replica.logger.error(f"Exception: {str(e)}")
        return jsonify({'error': str(e)}), 500


# Endpoint to get all cached data replica
@app_replica.route('/cached_data_replica', methods=['GET'])
def get_cached_data_replica():
    try:
        cached_data_replica = {key: cache_replica[key] for key in cache_replica.keys()}
        app_replica.logger.info(f"All cached data replica: {cached_data_replica}")
        return jsonify(cached_data_replica)
    except Exception as e:
        app_replica.logger.error(f"Exception: {str(e)}")
        return jsonify({'error': str(e)}), 500




# Run the Flask application on host 0.0.0.0 and port 3000 in debug mode
if __name__ == '__main__':
    socketio_replica.run(app_replica, host='0.0.0.0', port=5001, debug=True)
