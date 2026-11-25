import random


LIMITS = {"Take Card": 1, "Discard One": 2}


def valid_group(cards):
    if len(cards) < 3:
        return False
    numbers = sorted(number for colour, number in cards)
    if numbers[0] == numbers[-1]:
        return True
    colours = {colour for colour, number in cards}
    return len(colours) <= 2 and numbers == list(range(numbers[0], numbers[-1] + 1))


def card_name(card):
    return f"{card[0]} {card[1]}"


class GameActions:
    def __init__(self, names, hands, deck, player=0):
        self.names = names
        self.hands = hands
        self.deck = deck
        self.player = player
        self.used = {}
        self.offer = []
        self.dealing = False
        self.winner = None
        self.message = ""

    def allowed(self, action):
        if self.dealing or self.winner is not None or self.offer:
            return False
        if action in LIMITS and self.used.get(action, 0) >= LIMITS[action]:
            return False
        if action == "Take Card" and len(self.hands[self.player]) >= 20:
            return False
        if action == "Take Card":
            return any(hand for i, hand in enumerate(self.hands) if i != self.player)
        return action in ("Discard One", "Discard Group")

    def play(self, action, positions=(), target=None):
        if not self.allowed(action):
            return
        hand = self.hands[self.player]
        name = self.names[self.player]

        if action == "Take Card":
            if target not in range(len(self.hands)) or target == self.player or len(positions) != 1:
                return
            other = self.hands[target]
            if not 0 <= positions[0] < len(other):
                return
            card = other.pop(positions[0])
            hand.append(card)
            self.message = f"{name} took {card_name(card)} from {self.names[target]}."
            if not other:
                self.winner = target
        else:
            if len(set(positions)) != len(positions) or any(not 0 <= i < len(hand) for i in positions):
                return
            cards = [hand[i] for i in positions]

            if action == "Discard One" and len(cards) != 1:
                return

            if action == "Discard Group" and not valid_group(cards):
                return

            for i in sorted(positions, reverse=True):
                self.deck.append(hand.pop(i))
            random.shuffle(self.deck)
            discarded = card_name(cards[0]) if len(cards) == 1 else f"a group of {len(cards)} cards"
            self.message = f"{name} discarded {discarded}."
            if not hand:
                self.winner = self.player

        self.used[action] = self.used.get(action, 0) + 1
