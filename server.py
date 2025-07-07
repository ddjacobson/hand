# server_websocket.py
import asyncio
import ssl
import websockets
import json
import numpy as np
from game import Card, GameState
import os
import pygame 
import game
import pickle
from log import CONNECT
# Server configuration
HOST_PROD = '0.0.0.0' 
HOST = '127.0.0.1'  # Standard loopback interface address (localhost)
PORT = 8443     # Port to listen on

connected_clients = set() # To keep track of all connected clients

card_images = {}
suits = ['clubs', 'diamonds', 'hearts', 'spades']
ranks = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'jack', 'queen', 'king', 'ace']
CARD_SIZE_X = 100
CARD_SIZE_Y = 150

def create_ssl_context():
    ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ssl_context.load_cert_chain(certfile='cert.pem', keyfile='key.pem')
    return ssl_context

def populate_card_images():
    for suit in suits:
        for rank in ranks:
            # Handle special filenames for face cards
            if rank in ['jack', 'queen', 'king']:
                filename = f"{rank}_of_{suit}2.png"
            else:

                filename = f"{rank}_of_{suit}.png"
                
            path = os.path.join('assets', filename)
            if os.path.exists(path):
                image = pygame.image.load(path)
                card_images[(rank, suit)] = pygame.transform.scale(image, (CARD_SIZE_X, CARD_SIZE_Y))

def create_deck():
    populate_card_images()
    deck = []
    for _, ((rank, suit), img) in enumerate(card_images.items()):
        card = Card(rank, suit, None)
        card.in_hand = False  # Track if card is in hand
        deck.append(card)

    deck = deck * 2
    return deck

deck = create_deck()
discard_pile = [np.random.choice(deck, replace=False)]  # Initialize discard pile with one random card
client_hands = {}  # Store hands for each connected client
run_cards = []
opponent_runs = []
runs = []
hand_position = (50, 600)  # Lower y-position for hand area
CARDS_IN_HAND = 14

def deal_hand(deck):
    """Deals a new hand of cards from the deck."""
    hand = []
    for _ in range(CARDS_IN_HAND):
        np.random.shuffle(deck)
        card = deck.pop()
        card.rect.x = hand_position[0]
        card.rect.y = hand_position[1]
        hand.append(card)
    return hand

def deal_hand_MOCK(deck):
    """Deals a new hand of cards from the deck."""
    hand = []
    for _ in range(CARDS_IN_HAND-6):
        np.random.shuffle(deck)
        card = deck.pop()
        card.rect.x = hand_position[0]
        card.rect.y = hand_position[1]
        hand.append(card)
    # Add specific cards for testing
    specific_cards = [
        Card('jack', 'hearts', pygame.Rect(hand_position[0], hand_position[1], CARD_SIZE_X, CARD_SIZE_Y)),
        Card('king', 'hearts', pygame.Rect(hand_position[0], hand_position[1], CARD_SIZE_X, CARD_SIZE_Y)),
        Card('queen', 'hearts', pygame.Rect(hand_position[0], hand_position[1], CARD_SIZE_X, CARD_SIZE_Y)),
        Card('8', 'hearts', pygame.Rect(hand_position[0], hand_position[1], CARD_SIZE_X, CARD_SIZE_Y)),
        Card('9', 'hearts', pygame.Rect(hand_position[0], hand_position[1], CARD_SIZE_X, CARD_SIZE_Y)),
        Card('10', 'hearts', pygame.Rect(hand_position[0], hand_position[1], CARD_SIZE_X, CARD_SIZE_Y))
    ]
    hand.extend(specific_cards)
    return hand


async def send_message(websocket, state, hand):
    """Sends the initial game state to a client, including their specific hand."""
    state.deck = deck
    state.myHand = hand  # Use the specific hand for this client
    state.discard_pile = discard_pile
    state.runs = runs
    print(f"Sending initial game state to {websocket.remote_address}")
    await websocket.send(pickle.dumps(state.to_dict()))

async def register(websocket):
    """Register a new client connection."""
    connected_clients.add(websocket)
    print(f"Client {websocket.remote_address} connected. Total active connections: {len(connected_clients)}")

async def unregister(websocket):
    """Unregister a disconnected client and clean up their data."""
    connected_clients.remove(websocket)
    if websocket in client_hands:
        del client_hands[websocket]  # Remove the client's hand
    print(f"Client {websocket.remote_address} disconnected. Total active connections: {len(connected_clients)}")

async def handle_client(websocket):
    """Handles a single client connection, dealing them a unique hand."""
    await register(websocket)
    try:
        state = game.GameState()
        
        # Deal a unique hand for the new client
        player_hand = deal_hand(deck)

        if connected_clients == 1:
            player_hand = deal_hand_MOCK(deck)
        
        client_hands[websocket] = player_hand
        print(f"Dealt {len(player_hand)} cards to {websocket.remote_address}")

        if len(connected_clients) == 1:
            print("This is the first player.")
            state.myTurn = True
        else:
            state.myTurn = False

        # Send the starting state to the client with their hand
        await send_message(websocket, state, player_hand)

        async for message in websocket:
            print(f"Received from {websocket.remote_address}")
            try:
                data = GameState.from_dict(pickle.loads(message))

                # Update the server's authoritative state
                global discard_pile
                discard_pile = data.discard_pile
                runs = data.runs

                # Broadcast the updated state to all clients
                for client_ws in connected_clients:
                    server_state = game.GameState()
                    server_state.discard_pile = discard_pile
                    
                    if client_ws == websocket:
                        continue

                    server_state.runs = runs
                    server_state.myTurn = client_ws != websocket  # Toggle turn
                    
                    print(f"Broadcasting update to {client_ws.remote_address}")
                    await client_ws.send(pickle.dumps(server_state.to_dict()))

            except json.JSONDecodeError:
                print(f"Received non-JSON message: {message}")
                error_response = {"type": "error", "message": "Invalid JSON format"}
                await websocket.send(json.dumps(error_response))

    except websockets.exceptions.ConnectionClosedOK:
        print(f"Client {websocket.remote_address} closed connection normally.")
    except websockets.exceptions.ConnectionClosedError as e:
        print(f"Client {websocket.remote_address} closed connection with error: {e}")
    # except Exception as e:
    #     print(f"Error handling client {websocket.remote_address}: {e}")
    finally:
        await unregister(websocket)


async def start_server():
    """
    Starts the WebSocket server.
    """
    # Start the WebSocket server
    server = await websockets.serve(handle_client, HOST, PORT, ssl=create_ssl_context())
    print(f"{CONNECT} WebSocket Server listening on wss://{HOST}:{PORT}")
    # Keep the server running indefinitely
    await server.wait_closed()

if __name__ == "__main__":
    try:
        # build deck
        asyncio.run(start_server())
    except KeyboardInterrupt:
        print("Server stopped by user.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
