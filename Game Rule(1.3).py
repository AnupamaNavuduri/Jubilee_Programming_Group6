import random

MAX_HAND = 20
LIMITS = {"Draw One": 1, "Take Card": 1, "Draw Two": 1, "Discard One": 2}
class Card:  # One card = colour + number (1-9)
    def __init__(self, colour, number):
        self.colour = colour
        self.number = number

    def __str__(self):  # print(card) shows ex) "Red 5"
        return f'{self.colour} {self.number}'


class Deck:  # 90 cards
    def __init__(self):
        colours = ["Red", "Green", "Yellow", "Black", "Blue"]  # 5 colours
        self.cards = []
        for colour in colours:  
            for number in range(1, 10):  # 9 numbers 
                for _ in range(2):  # 2 copies 
                    self.cards.append(Card(colour, number))  
        self.shuffle()  # also used after discarding
    
    def shuffle(self):
        random.shuffle(self.cards)

    def draw(self):   # takes the top card off the deck and returns it
        card = self.cards.pop() 
        return card

    def add_back(self, card):  # for discards : puts the card back and reshuffles the whole deck
        self.cards.append(card)
        self.shuffle()


class Player:   # only for testing rules 1 and 3, player
    def __init__(self, name):
        self.name =  name
        self.hand = []

class Game:
    def __init__(self, names):
        self.deck = Deck()                  # one shared deck
        self.players = []                   # all players in turn order
        for name in names:
            self.players.append(Player(name))   # make a Player for each name
        self.current = 0                    # whose turn it(demo: self.player)
        self.used = {}                      # how many times each action was used
        self.offer = []                     # the two cards waiting to be chosen
        self.message = ""                   # text shown on screen

    # Rule 1: draw one card from the deck
    def draw_one(self):
        player = self.players[self.current]     # whose turn it is
        if self.offer:  # finish choosing from Draw Two first
            return False
        if self.used.get("Draw One", 0) >= LIMITS["Draw One"]:   # only once per turn
            return False
        if len(player.hand) >= MAX_HAND:
            self.message = "Your hand is full."   # max hand 20 cards
            return False
        if len(self.deck.cards) == 0:   # nothing left to draw
            return False
        card = self.deck.draw()                 # take the top card
        player.hand.append(card)                # add it to the hand
        self.used["Draw One"] = self.used.get("Draw One", 0) + 1   # count this use
        self.message = f"{player.name} drew {card}."                # same as demo
        return True

    # Rule 3 (step 1): draw two cards and hold them
    def draw_two(self):
        player = self.players[self.current]     # whose turn it is
        if self.offer:    # finish choosing from Draw Two first
            return False
        if self.used.get("Draw Two", 0) >= LIMITS["Draw Two"]:
            return False
        if len(player.hand) >= MAX_HAND:
            return False
        if len(self.deck.cards) < 2:   # need at least two cards
            return False
        self.offer = [self.deck.draw(), self.deck.draw()]          # hold both cards
        self.used["Draw Two"] = self.used.get("Draw Two", 0) + 1   # count this use
        self.message = f"{player.name} drew two cards."            # same as demo
        return True

    # Rule 3 (step 2): keep one, the other go to the deck
    # index is 0 or 1 (which card to keep)
    def keep(self, index):
        player = self.players[self.current]     # whose turn it is
        if not self.offer:   # nothing to choose
            return False
        if index not in (0, 1):   # only 0 or 1 is allowed
            return False
        card = self.offer[index]                    # the chosen card
        player.hand.append(card)                    # goes into the hand
        self.deck.add_back(self.offer[1 - index])   # the other is discarded
        self.offer = []                             # done choosing
        self.message = f"{player.name} kept {card}."   # same as demo
        return True

    # Test only: end the turn and move to the next player
    def end_turn(self):
        if self.offer:   # finish choosing from Draw Two first
            return False
        self.current = (self.current + 1) % len(self.players)   # next player, back to 0 after the last
        self.used = {}                                           # new turn, nothing used yet
        return True                          