FACES = ['jack', 'queen', 'king', 'ace']

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

            ranks.sort()
            # check if ranks are consecutive
            return all(ranks[i] + 1 == ranks[i + 1] for i in range(len(ranks) - 1)) and len(set(card.suit for card in run_cards)) == 1 
    return False

def get_runs_value(runs):
    total_value = 0
    for run in runs:
        for card in run:
            if card.rank in FACES and card.rank != 'ace':
                total_value += 10
            elif card.rank == 'ace':
                total_value += 11
            else:
                total_value += int(card.rank)
    return total_value


def validate_51(runs):
    for run in runs:
        if not validate_run(run):
            return False
    return get_runs_value(runs) >= 51