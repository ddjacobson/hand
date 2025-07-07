import pygame
from logic import Card
import os
import numpy as np
# Initialize Pygame
pygame.init()

# Screen dimensions
SCREEN_WIDTH = 1300
SCREEN_HEIGHT = 800  # More reasonable height for display
CARD_SIZE_X = 100
CARD_SIZE_Y = 150
FACES = ['jack', 'queen', 'king', 'ace']
# Set up display
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Arabian Rummy - Deck Viewer")

# Load card images
card_images = {}
suits = ['clubs', 'diamonds', 'hearts', 'spades']
ranks = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'jack', 'queen', 'king', 'ace']

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


# Create deck with card positions
class Card:
    def __init__(self, rank, suit, image):
        self.rank = rank
        self.suit = suit
        self.image = image
        self.rect = self.image.get_rect()

    def __eq__(self, other):
        if isinstance(other, Card):
            return self.rank == other.rank and self.suit == other.suit
        return False

# Initialize deck and hand
deck = []
hand = []
discard_pile = []
hand_position = (50, 600)  # Lower y-position for hand area
hand_spacing = 75  # Horizontal spacing between cards

CARDS_IN_HAND = 14
def deal(deck):
    for _ in range(CARDS_IN_HAND):
        np.random.shuffle(deck)
        card = deck.pop()
        card.rect.x = hand_position[0] 
        card.rect.y = hand_position[1]
        hand.append(card)

def validate_run(run_cards):
    if (len(run_cards) == 3 or len(run_cards) == 4) and len({(card.rank, card.suit) for card in run_cards}) == len(run_cards): # Check for valid size and unique cards
            # Check if suits are same - run
            ranks = set(card.rank for card in run_cards)
            if len(ranks) == 1:
                return True
            
            ranks = []
            for card in run_cards:
                if card.rank in FACES:
                    ranks.append(FACES.index(card.rank) + 11)  # Convert face cards to numerical values
                else:
                    ranks.append(int(card.rank))

            print ("Ranks in run:", ranks)
            ranks.sort()
            # check if ranks are consecutive
            return all(ranks[i] + 1 == ranks[i + 1] for i in range(len(ranks) - 1))
    return False



def create_deck():
    deck = []
    for _, ((rank, suit), img) in enumerate(card_images.items()):
        card = Card(rank, suit, img)

        card.in_hand = False  # Track if card is in hand
        deck.append(card)

    deck = deck * 2
    return deck

deck = create_deck()
deal(deck)

# Main loop variables
dragging = False
selected_card = None
offset_x = 0
offset_y = 0

run_selector = False
run_cards = []
runs = []

running = True
discard_pile = [np.random.choice(deck)] # Starting discard

while running:
    mouse_pos = pygame.mouse.get_pos()
    for event in pygame.event.get():
        # print(event)
        if event.type == pygame.QUIT:
            running = False

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_LCTRL:
                run_selector = True
        
        elif event.type == pygame.KEYUP:
            if event.key == pygame.K_LCTRL:
                # validate run cards
                if validate_run(run_cards):
                    print("Run selected:", [f"{card.rank} of {card.suit}" for card in run_cards])
                    runs.append(run_cards.copy())
                    
                    for card in run_cards:
                        if card in hand:
                            hand.remove(card)

                else:
                    print("Not enough cards for a run.")

                run_selector = False
                # Reset run cards when exiting run selector mode
                run_cards.clear()


        elif event.type == pygame.MOUSEBUTTONDOWN:
            dragging = True
            # Check hand cards first
            card_clicked = False
            for card in hand:
                if card.rect.collidepoint(event.pos):
                    # card is clicked
                    selected_card = card
                    offset_x = selected_card.rect.x - event.pos[0]
                    offset_y = selected_card.rect.y - event.pos[1]
                    card_clicked = True

                    if run_selector:
                        run_cards.append(selected_card)


                    break
            
        elif event.type == pygame.MOUSEBUTTONUP:
            # check if discarding before resetting selected_card
            if selected_card and not run_selector:
                discard_area_rect = pygame.Rect(SCREEN_WIDTH - 260, 50, CARD_SIZE_X, CARD_SIZE_Y)
                if discard_area_rect.collidepoint(event.pos):
                    if selected_card in hand:
                        hand.remove(selected_card)
                        discard_pile.append(selected_card)
                        print(f"Discarded {selected_card.rank} of {selected_card.suit}")

            dragging = False
            selected_card = None

        elif event.type == pygame.MOUSEMOTION:
            if dragging and selected_card:
                # Constrain movement to hand area
                selected_card.rect.x = event.pos[0] + offset_x
                selected_card.rect.y = event.pos[1] + offset_y

    screen.fill((35, 166, 43))  # Green background
    
    # Draw hand area background
    hand_bg_width = SCREEN_WIDTH - 100
    hand_bg = pygame.Surface((hand_bg_width, 200), pygame.SRCALPHA)
    hand_bg.fill((255, 255, 255, 128))
    screen.blit(hand_bg, ((SCREEN_WIDTH - hand_bg_width) // 2, 580))  # Centered

    font = pygame.font.Font(None, 36)
    text = font.render("Your Hand", True, (255, 255, 255))
    screen.blit(text, (50, 550))

    # Draw remaining cards
    image = pygame.image.load('assets/back.png')
    image = pygame.transform.scale(image, (CARD_SIZE_X, CARD_SIZE_Y))
    screen.blit(image, (SCREEN_WIDTH - 150, 50))  # Position at top right corner

    # Draw discard area and top card
    # discard_area = pygame.Surface((CARD_SIZE_X, CARD_SIZE_Y), pygame.SRCALPHA)
    # discard_area.fill((255, 255, 255, 128))
    # screen.blit(discard_area, (SCREEN_WIDTH - 260, 50))
    if discard_pile:
        top_card = discard_pile[-1]
        top_card.rect.topleft = (SCREEN_WIDTH - 260, 50)
        screen.blit(top_card.image, top_card.rect)

    # Draw hand label
    font = pygame.font.Font(None, 36)
    text = font.render("Your Runs", True, (255, 255, 255))
    screen.blit(text, (50, 275))
    
    # Position and draw hand cards
    for i, card in enumerate(hand):
        if card == selected_card and dragging:
            # Draw selected card at mouse position
            card.rect.x = mouse_pos[0] + offset_x
            card.rect.y = mouse_pos[1] + offset_y
        
        else:
            card.rect.x = (SCREEN_WIDTH//2 - (CARDS_IN_HAND * hand_spacing) // 2) + (i * hand_spacing)
            card.rect.y = hand_position[1]
            # Keep cards within hand area boundaries
            card.rect.x = max(50, min(card.rect.x, SCREEN_WIDTH - 150))
        
        # Always blit the card image
        screen.blit(card.image, card.rect)
    
    # Draw selected run cards
    for i, run in enumerate(runs):
        for j, card in enumerate(run):
            card.rect.x = 55 + (i * 110)
            card.rect.y = 300 + (j * 40)
            screen.blit(card.image, card.rect)


    pygame.display.flip()

pygame.quit()
