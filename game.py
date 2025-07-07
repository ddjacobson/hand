import pygame
# game state
CARD_SIZE_X = 75 * 1.2
CARD_SIZE_Y = 112 * 1.2


class Card:
    def __init__(self, rank, suit, rect):
        self.rank = rank
        self.suit = suit
        self.rect = rect if rect else pygame.Rect(0, 0, CARD_SIZE_X, CARD_SIZE_Y)

    def __str__(self):
        return f"{self.rank} of {self.suit}"
 
    def __eq__(self, other):
        if isinstance(other, Card):
            return self.rank == other.rank and self.suit == other.suit
        return False
    
    def to_dict(self):
        return {'rank': self.rank, 'suit': self.suit, 'rect': [self.rect.x, self.rect.y, self.rect.width, self.rect.height]}
                
    @staticmethod
    def from_dict(data):
        rect = pygame.Rect(data['rect'][0], data['rect'][1], data['rect'][2], data['rect'][3])
        return Card(data['rank'], data['suit'], rect)



class GameState():

    def __init__(self):
        self.deck = []
        self.myHand = []
        self.discard_pile = []
        self.myTurn = True
        self.runs = []
        self.opponent_runs = []

    def __str__(self):
        return f"GameState(deck={self.deck}, myHand={self.myHand}, discard_pile={self.discard_pile}, myTurn={self.myTurn}, runs={self.runs})"
    
    def to_dict(self):
        return {
            'deck': [card.to_dict() for card in self.deck],
            'myHand': [card.to_dict() for card in self.myHand],
            'discard_pile': [card.to_dict() for card in self.discard_pile],
            'myTurn': self.myTurn,
            'runs': [[card.to_dict() for card in run] for run in self.runs]
        }
    
    @staticmethod
    def from_dict(data):
        state = GameState()
        state.deck = [Card.from_dict(card_data) for card_data in data['deck']]
        state.myHand = [Card.from_dict(card_data) for card_data in data['myHand']]
        state.discard_pile = [Card.from_dict(card_data) for card_data in data['discard_pile']]
        state.myTurn = data['myTurn']
        state.runs = [[Card.from_dict(card_data) for card_data in run_data] for run_data in data['runs']]
        return state
    

def double_click(last_clicked_card, card, last_click_time, current_time):
    return last_clicked_card == card and (current_time - last_click_time) < 500