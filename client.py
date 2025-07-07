import asyncio
import websockets

import pygame
import websockets
import asyncio
from logic import validate_run, validate_51
import game
import pickle
from log import CONNECT, GAME
from game import GameState, double_click
import ssl
from screen import *


# Client configuration
# HOST_PROD = '216.17.58.23' # change in chicago
HOST = '127.0.0.1'  # The server's hostname or IP address
PORT = 8443       # The port used by the server
URI = f"wss://{HOST}:{PORT}" # WebSocket URI
connected = False


# Initialize Pygame
pygame.init()

# game constants
CARDS_IN_HAND = 15
SCREEN_WIDTH = 1300
SCREEN_HEIGHT = 800  # More reasonable height for display


ORDER_HAND_X = SCREEN_WIDTH - 200
ORDER_HAND_Y = SCREEN_HEIGHT - 70

FACES = ['jack', 'queen', 'king', 'ace']
# Set up display
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Arabian Rummy - Deck Viewer")

opponent_runs = []
card_images = {}
suits = ['clubs', 'diamonds', 'hearts', 'spades']
ranks = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'jack', 'queen', 'king', 'ace']
deck = []
discard_pile = []
hand = []
run_cards = []
runs = []
myTurn = False
staged_runs = []
run_selector = False

UPDATE_GAME_STATE = pygame.USEREVENT + 1

def create_self_signed_cert():
    return ssl._create_unverified_context()

async def send_state(websocket, state, deck, hand, discard_pile, runs):
    pygame.display.flip()
    state.deck = deck  # Convert to dicts for JSON serialization
    state.myHand = hand  # Convert to dicts for JSON serialization
    state.discard_pile = discard_pile

    state.runs = runs  # Convert to dicts for JSON serialization
    state.myTurn = False  # Set to True for the next turn  

    print("sending to server")
    await websocket.send(pickle.dumps(state.to_dict()))  # Send as pickled data



# --- CLIENT CODE ---
    
def check_add_to_run(card, runs, opp_runs):
    for run in runs:
        if validate_run(run + [card]):
            run.append(card)
            hand.remove(card)
            # add to run
            return True
    for run in opp_runs:
        if validate_run(run + [card]):
            run.append(card)
            hand.remove(card)
            # add to run
            return True
    
    return False
    

async def receive_messages(websocket):
    """Receives and processes messages from the server."""
    global discard_pile, myTurn, opponent_runs
    try:
        print("Listening for messages from server...")
        async for message in websocket:
            try:
                opponent_state = GameState.from_dict(pickle.loads(message))
                discard_pile = opponent_state.discard_pile
                myTurn = opponent_state.myTurn
                opponent_runs = opponent_state.runs
                pygame.event.post(pygame.event.Event(UPDATE_GAME_STATE))
                print("Received opponent's turn data")
            except (pickle.UnpicklingError, KeyError) as e:
                print(f"Error processing message: {e}")

    except websockets.exceptions.ConnectionClosed:
        print("ASYNCIO: Connection to server closed.")


async def start_client():

    global hand, deck, discard_pile, myTurn, runs, opponent_runs
    try:
        ssl_context = ssl._create_unverified_context()
        print(f"{CONNECT}: Connecting to WebSocket server...")
        async with websockets.connect(URI, ssl=ssl_context) as websocket:
            print(f"{CONNECT}: Connected to WebSocket server at {URI}")

            # Receive the initial welcome message from the server
            welcome_data = await websocket.recv()
            game_state = game.GameState.from_dict(pickle.loads(welcome_data))
            
            # Initialize client game state
            deck = game_state.deck
            hand = game_state.myHand
            discard_pile = game_state.discard_pile
            myTurn = game_state.myTurn
            runs = game_state.runs
            opponent_runs = []

            # Start the message receiver task
            receive_task = asyncio.create_task(receive_messages(websocket))
            state = game.GameState()
            running = True
            run_selector = False
            last_click_time = 0
            last_clicked_card = None
            hasFiftyOne = False

            while running:
                # event loop
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        running = False
                        break

                    elif event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_LCTRL:
                            run_selector = True
                    
                    elif event.type == pygame.KEYUP:
                        if event.key == pygame.K_LCTRL:
                            if run_cards:
                                staged_runs.append(run_cards.copy())
                                run_cards.clear()
                            run_selector = False

                    elif event.type == pygame.K_ESCAPE:
                        running = False
                        break

                    elif event.type == pygame.MOUSEBUTTONDOWN:
                        lay_down_button_rect = draw_lay_down_button(screen)
                        draw_button_rect = pygame.Rect(DECK_X, DECK_Y, CARD_SIZE_X, CARD_SIZE_Y)
                        draw_discard_rect = pygame.Rect(DISCARD_X, DISCARD_Y, CARD_SIZE_X, CARD_SIZE_Y)
                        order_hand_button_rect = draw_order_hand_button(screen)

                        if order_hand_button_rect.collidepoint(event.pos):
                            hand.sort(key=lambda card: (ranks.index(card.rank), suits.index(card.suit)), reverse=True)

                        elif draw_button_rect.collidepoint(event.pos) and myTurn:
                            print(f"{GAME} taking from deck")
                            hand.append(deck.pop())

                        elif draw_discard_rect.collidepoint(event.pos) and myTurn:
                            print(discard_pile)
                            if discard_pile:
                                hand.append(discard_pile.pop())
                            # share update        
                            await send_state(websocket, state, deck, hand, discard_pile, runs)
               
                        elif lay_down_button_rect.collidepoint(event.pos):
                            if not hasFiftyOne:
                                if validate_51(staged_runs):
                                    runs.extend(staged_runs)
                                    hasFiftyOne = True
                                    print("Staged runs meet the 51 rule, laying down.")
                                    for run in staged_runs:
                                        for card in run:
                                            if card in hand:
                                                hand.remove(card)
                                else:
                                    print("Staged runs do not meet the 51 rule.")
                            elif(validate_run(run_cards) and len(run_cards) <= 4):
                                runs.extend(staged_runs)
                                for run in staged_runs:
                                    for card in run:
                                        if card in hand:
                                            hand.remove(card)
                            staged_runs.clear()
                        else:
                            # check hand for collision
                            for card in hand:
                                if card.rect.collidepoint(event.pos):
                                    current_time = pygame.time.get_ticks()
                                    if myTurn and last_clicked_card == card and (current_time - last_click_time) < 500: # double-click card
                                        # before discard, check if can be added to any runs
                                        if hasFiftyOne:
                                            print("Checking run addition")
                                            if check_add_to_run(card, runs, opponent_runs):
                                                continue

                                        elif card in hand:
                                            hand.remove(card)
                                            discard_pile.append(card)
                                            print(f"Discarded {card.rank} of {card.suit}")
                                            await send_state(websocket, state, deck, hand, discard_pile, runs) # discard assumes end of turn
                                            myTurn = False

                                        last_clicked_card = None

                                    else:
                                        last_click_time = current_time
                                        last_clicked_card = card

                                    if run_selector:
                                        if card in run_cards:
                                            run_cards.remove(card)
                                        else:
                                            run_cards.append(card)
                                    break
                
                if not running:
                    break

                # --- draw screen ---
                draw_background(screen)
                draw_hand_area(screen)
                
                draw_text(screen, "Opponent Runs", (50, 10))
                draw_text(screen, "Your Hand", (50, 550))
                draw_text(screen, "Your Runs", (50, 275))
                
                draw_deck(screen)
                draw_discard_pile(screen, discard_pile)
                draw_player_hand(screen, hand, run_cards, staged_runs)
                
                draw_runs(screen, runs, 55, 300)
                draw_runs(screen, opponent_runs, 55, 50)
                draw_lay_down_button(screen)
                draw_order_hand_button(screen)

                pygame.display.flip()

                await asyncio.sleep(0.01)

            receive_task.cancel()
            pygame.quit()

    except websockets.exceptions.ConnectionClosedError:
        print("Connection refused. Make sure the WebSocket server is running.")
    except websockets.exceptions.InvalidURI:
        print(f"Invalid WebSocket URI: {URI}")

if __name__ == "__main__":
    asyncio.run(start_client())