
# app.py

import requests

# Define the base URLs for the front_tier servers
FRONT_TIER_SERVERS = ["http://127.0.0.1:3000", "http://192.168.2.105:3000"]
server_index = 0

# Function to switch to the next server
def switch_server():
    global server_index
    server_index = (server_index + 1) % len(FRONT_TIER_SERVERS)

# Function to search for items based on item type
def search_item():
    item_type = input("Enter the item type to search for: ")
    try:
        server_url = FRONT_TIER_SERVERS[server_index]
        response = requests.get(f"{server_url}/search/{item_type}")
        response.raise_for_status()  # Check for HTTP errors
        print(f"Search Result from {server_url}:", response.json())
        switch_server()
    except requests.exceptions.RequestException as e:
        print(f"Error during search: {e}")

# Function to get information about a specific item
def get_item_info():
    item_number = input("Enter the item number to get information: ")
    try:
        server_url = FRONT_TIER_SERVERS[server_index]
        response = requests.get(f"{server_url}/info/{item_number}")
        response.raise_for_status()  # Check for HTTP errors
        print(f"Item Information from {server_url}:", response.json())
        switch_server()
    except requests.exceptions.RequestException as e:
        print(f"Error during item information retrieval: {e}")

# Function to make a purchase request for a specific item
def purchase_item():
    item_id = input("Enter the item ID to purchase: ")
    try:
        server_url = FRONT_TIER_SERVERS[server_index]
        response = requests.post(f"{server_url}/purchase/{item_id}")
        response.raise_for_status()  # Check for HTTP errors
        print(f"Purchase Result from {server_url}:", response.json())
        switch_server()
    except requests.exceptions.RequestException as e:
        print(f"Error during purchase: {e}")

# Main loop
while True:
    # Get user input for the action
    user_action = input("What would you like to do? (search/info/purchase/exit): ").lower()

    # Check if the user wants to exit
    if user_action == "exit":
        break

    # Perform the chosen action
    if user_action == "search":
        search_item()
    elif user_action == "info":
        get_item_info()
    elif user_action == "purchase":
        purchase_item()
    else:
        print("Invalid action. Please choose 'search', 'info', 'purchase', or 'exit'.")