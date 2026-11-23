class Player:
    def __init__(self, name, base_x, base_y, spacing_x, spacing_y, is_human):
        self.name = name
        self.base_x = base_x
        self.base_y = base_y
        self.spacing_x = spacing_x
        self.spacing_y = spacing_y
        self.is_human = is_human
        self.hand = []

    def draw_from_deck(self, deck, count):
        for _ in range(count):
            if len(deck.cards) > 0:
                self.hand.append(deck.draw())

    def remove_card(self, card):
        if card in self.hand:
            card.selected = False
            self.hand.remove(card)

    def get_card_position(self, index):
        x = self.base_x + index * self.spacing_x
        y = self.base_y + index * self.spacing_y
        return x, y

