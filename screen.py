import pygame
from client import suits, ranks
import os 

CARDS_IN_HAND = 15
SCREEN_WIDTH = 1300
SCREEN_HEIGHT = 800  # More reasonable height for display
CARD_SIZE_X = 75 * 1.2
CARD_SIZE_Y = 112 * 1.2
hand_spacing = 75  # Horizontal spacing between cards
hand_position = (SCREEN_WIDTH // 2, SCREEN_HEIGHT - 200)  # Centered horizontally, near bottom
ORDER_HAND_X = SCREEN_WIDTH - 200
ORDER_HAND_Y = SCREEN_HEIGHT - 70

card_images = {}  # Cache for card images

def setup():
    loaded_images_count = 0
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
                loaded_images_count += 1
            else:
                print(f"Warning: Image file not found: {path}")
    print(f"Loaded {loaded_images_count} card images.")

def get_card_image(card):
        # print(card)
        rank = card.rank
        suit = card.suit
        rect = card.rect
        rect = pygame.Rect(rect[0], rect[1], rect[2], rect[3])  # Convert to pygame.Rect
        
        # Ensure image is loaded
        image = card_images.get((rank, suit))
        if image is None:
            # If image not in cache, try to load it dynamically
            if rank in ['jack', 'queen', 'king']:
                filename = f"{rank}_of_{suit}2.png"
            else:
                filename = f"{rank}_of_{suit}.png"
            path = os.path.join('assets', filename)
            if os.path.exists(path):
                image = pygame.image.load(path)
                image = pygame.transform.scale(image, (CARD_SIZE_X, CARD_SIZE_Y))
                card_images[(rank, suit)] = image # Add to cache
            else:
                print(f"Error: Image file not found for {rank} of {suit} at {path}")


        return image

def draw_background(screen):
    """Fills the screen with the background color."""
    screen.fill((35, 166, 43))  # Green background

def draw_hand_area(screen):
    """Draws the semi-transparent background for the player's hand."""
    hand_bg_width = SCREEN_WIDTH - 50
    hand_bg = pygame.Surface((hand_bg_width, 200), pygame.SRCALPHA)
    hand_bg.fill((255, 255, 255, 128))
    screen.blit(hand_bg, ((SCREEN_WIDTH - hand_bg_width) // 2, 580))  # Centered

def draw_text(screen, text, position, font_size=36, color=(255, 255, 255)):
    """Renders and draws text on the screen."""
    font = pygame.font.Font(None, font_size)
    text_surface = font.render(text, True, color)
    screen.blit(text_surface, position)

DECK_X = SCREEN_WIDTH - 150
DECK_Y = 50

def draw_deck(screen):
    """Draws the deck of cards (back facing up)."""
    image = pygame.image.load('assets/back.png')
    image = pygame.transform.scale(image, (CARD_SIZE_X, CARD_SIZE_Y))
    screen.blit(image, (DECK_X, DECK_Y))

DISCARD_X, DISCARD_Y = SCREEN_WIDTH - 260, 50

def draw_discard_pile(screen, discard_pile):
    draw_text(screen, "Discard", (DISCARD_X , DISCARD_Y - 25), font_size=18)
    if discard_pile:
        top_card = discard_pile[-1]
        top_card.rect.topleft = (DISCARD_X, DISCARD_Y)
        screen.blit(get_card_image(top_card), top_card.rect)

def draw_player_hand(screen, hand, run_cards, staged_runs):    
    # ensure no dupliate cards in staged_runs
    staged_cards_flat = [card for run in staged_runs for card in run]
    
    # Calculate starting x position to center the hand
    total_hand_width = len(hand) * hand_spacing
    start_x = (SCREEN_WIDTH - total_hand_width) / 2
    
    for i, card in enumerate(hand):
        # Set card position
        card.rect.x = start_x + (i * hand_spacing)
        card.rect.y = hand_position[1]

        # Move card up if selected
        is_staged = card in staged_cards_flat
        is_selecting = card in run_cards
        
        temp_rect = card.rect.copy()
        if is_staged or is_selecting:
            temp_rect.y -= 20  # Move up by 20 pixels

        # Draw the card image
        screen.blit(get_card_image(card), temp_rect)

        # Draw highlight if the card is staged or being selected
        if is_staged:
            pygame.draw.rect(screen, (255, 255, 0), temp_rect, 4)  # Yellow for staged
       

def draw_runs(screen, runs_to_draw, start_x, start_y):
    if runs_to_draw:
        for i, run in enumerate(runs_to_draw):
            # if run longer than 3, close it    
            if len(run) > 3:
                run[0].rect.x = start_x + (i * 110)
                run[0].rect.y = start_y
                screen.blit(get_card_image(run[0]), run[0].rect)
                continue

            for j, card in enumerate(run):
                card.rect.x = start_x + (i * 110)
                card.rect.y = start_y + (j * 40)
                screen.blit(get_card_image(card), card.rect)

def draw_lay_down_button(screen):
    button_rect = pygame.Rect(SCREEN_WIDTH - 400, SCREEN_HEIGHT - 70, 150, 50)
    pygame.draw.rect(screen, (0, 100, 0), button_rect)  # Dark green button
    draw_text(screen, "Lay Down", (button_rect.x + 20, button_rect.y + 10), font_size=30)
    return button_rect



def draw_order_hand_button(screen):
    button_rect = pygame.Rect(ORDER_HAND_X, ORDER_HAND_Y, 150, 50)
    pygame.draw.rect(screen, (0, 100, 0), button_rect)  # Dark green button
    draw_text(screen, "Order Hand", (button_rect.x + 20, button_rect.y + 10), font_size=30)
    return button_rect