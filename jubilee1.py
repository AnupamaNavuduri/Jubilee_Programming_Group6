import random
from itertools import combinations

import pygame


COLOURS = {
    "Red": (164, 43, 48), "Green": (25, 112, 66), "Yellow": (245, 191, 60),
    "Black": (44, 46, 51), "Blue": (38, 83, 162),
}
LIMITS = {"Draw One": 1, "Take Card": 1, "Draw Two": 1, "Discard One": 2}
ACTIONS = ["Draw One", "Draw Two", "Take Card", "Discard One", "Discard Group", "Pass"]


def valid_group(cards):
    if len(cards) < 3:
        return False
    numbers = sorted(number for colour, number in cards)
    if numbers[0] == numbers[-1]:
        return True
    colours = {colour for colour, number in cards}
    return len(colours) <= 2 and numbers == list(range(numbers[0], numbers[-1] + 1))


def find_group(hand):
    """Find a longest set or run for the computer. Return its card positions."""
    best = []
    for number in range(1, 10):
        same = [i for i, card in enumerate(hand) if card[1] == number]
        if len(same) >= 3 and len(same) > len(best):
            best = same
    for colours in combinations(COLOURS, 2):
        positions = {number: i for i, (colour, number) in enumerate(hand) if colour in colours}
        run = []
        for number in range(1, 10):
            if number in positions:
                run.append(positions[number])
                if len(run) >= 3 and len(run) > len(best):
                    best = run[:]
            else:
                run = []
    return best


def card_name(card):
    return f"{card[0]} {card[1]}"


class Game:
    def __init__(self, opponents):
        self.names = ["You"] + [f"Computer {i + 1}" for i in range(opponents)]
        self.deck = [(colour, number) for colour in COLOURS for number in range(1, 10)] * 2
        random.shuffle(self.deck)
        self.hands = [[self.deck.pop() for _ in range(7)] for name in self.names]
        self.player = 0
        self.used = {}
        self.offer = []
        self.winner = None
        self.message = "Seven cards dealt to each player."

    def allowed(self, action):
        if self.winner is not None or self.offer:
            return False
        if action in LIMITS and self.used.get(action, 0) >= LIMITS[action]:
            return False
        if action in ("Draw One", "Draw Two", "Take Card") and len(self.hands[self.player]) == 20:
            return False
        if action == "Draw One":
            return len(self.deck) >= 1
        if action == "Draw Two":
            return len(self.deck) >= 2
        if action == "Take Card":
            return any(hand for i, hand in enumerate(self.hands) if i != self.player)
        return action in ("Discard One", "Discard Group", "Pass")

    def play(self, action, positions=(), target=None):
        if not self.allowed(action):
            return
        hand = self.hands[self.player]
        name = self.names[self.player]
        if action == "Pass":
            self.message = f"{name} ended the turn." if self.used else f"{name} passed."
            self.player = (self.player + 1) % len(self.hands)
            self.used = {}
            return
        if action == "Draw One":
            card = self.deck.pop()
            hand.append(card)
            self.message = f"{name} drew {card_name(card)}."
        elif action == "Draw Two":
            self.offer = [self.deck.pop(), self.deck.pop()]
            self.message = f"{name} drew two cards."
        elif action == "Take Card":
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

    def keep(self, index):
        if self.offer and index in (0, 1):
            card = self.offer[index]
            self.hands[self.player].append(card)
            self.deck.append(self.offer[1 - index])
            random.shuffle(self.deck)
            self.offer = []
            self.message = f"{self.names[self.player]} kept {card_name(card)}."


def computer_step(game, strategy):
    hand = game.hands[game.player]
    if game.offer:
        game.keep(random.randrange(2))
        return

    group = find_group(hand)
    if strategy == "Groups":
        if group:
            game.play("Discard Group", group)
            return
        if len(hand) > 2 and game.allowed("Take Card"):
            for target, other in enumerate(game.hands):
                if target != game.player and len(other) > 1:
                    for i, card in enumerate(other):
                        if find_group(hand + [card]):
                            game.play("Take Card", [i], target)
                            return
        if game.allowed("Discard One"):
            game.play("Discard One", [0])
        else:
            game.play("Pass")
        return

    # Pick a random legal action, then use a random card where needed.
    choices = [("Pass",)]
    for action in ("Draw One", "Draw Two"):
        if game.allowed(action):
            choices.append((action,))
    if game.allowed("Take Card"):
        targets = [i for i, other in enumerate(game.hands) if i != game.player and other]
        target = random.choice(targets)
        choices.append(("Take Card", [random.randrange(len(game.hands[target]))], target))
    if game.allowed("Discard One"):
        choices.append(("Discard One", [random.randrange(len(hand))]))
    if group:
        choices.append(("Discard Group", group))
    game.play(*random.choice(choices))


def main():
    pygame.display.init()
    pygame.font.init()
    screen = pygame.display.set_mode((990, 620))
    pygame.display.set_caption("Jubilee1")
    font = pygame.font.Font(None, 26)
    large_font = pygame.font.Font(None, 42)
    clock = pygame.time.Clock()
    game = None
    opponents = 2
    strategies = ["Random", "Groups"]
    selected = []
    taking = False
    auto = False
    next_move = 0
    running = True

    def text(label, pos, colour="black", large=False):
        screen.blit((large_font if large else font).render(label, True, colour), pos)

    def button(label, rect, command, enabled=True):
        pygame.draw.rect(screen, (213, 226, 247) if enabled else (223, 223, 223), rect)
        pygame.draw.rect(screen, (90, 100, 115), rect, 1)
        label_image = font.render(label, True, "black" if enabled else (100, 100, 100))
        screen.blit(label_image, label_image.get_rect(center=rect.center))
        if enabled:
            clicks.append((rect, command))

    def draw_card(card, rect, picked=False):
        colour, number = card
        pygame.draw.rect(screen, COLOURS[colour], rect)
        pygame.draw.rect(screen, (255, 192, 20) if picked else (235, 235, 235), rect, 3 if picked else 1)
        ink = "black" if colour == "Yellow" else "white"
        text(str(number), (rect.x + 5, rect.y + 8), ink, large=True)
        text(colour[:3], (rect.x + 5, rect.y + 47), ink)

    while running:
        now = pygame.time.get_ticks()
        if game and game.winner is None and (game.player != 0 or auto) and now >= next_move:
            computer_step(game, "Groups" if game.player == 0 else strategies[game.player - 1])
            if game.player != 0:
                auto = False
            next_move = now + 650

        screen.fill((247, 247, 247))
        clicks = []
        text("Jubilee1", (22, 15), large=True)
        if game is None:
            text("Computer opponents", (22, 93))
            for count in (1, 2):
                label = f"{count} (selected)" if count == opponents else str(count)
                button(label, pygame.Rect(22 + (count - 1) * 128, 122, 118, 38), ("Count", count))
            for i in range(opponents):
                button(f"Computer {i + 1}: {strategies[i]}", pygame.Rect(22 + i * 232, 181, 220, 38), ("Strategy", i))
            text("Click a strategy to switch between Random and Groups.", (22, 234))
            button("Start Game", pygame.Rect(22, 276, 170, 43), ("Start",))
            text("Empty your hand first. Click your cards to select them for discarding.", (22, 366))
            text("A group is 3+ of the same number, or 3+ consecutive numbers in up to two colours.", (22, 395))
        else:
            human = game.player == 0 and not auto and game.winner is None
            text(f"Deck: {len(game.deck)}   |   Turn: {game.names[game.player]}", (219, 22))
            button("Menu", pygame.Rect(872, 12, 95, 34), ("Menu",))
            for p, hand in enumerate(game.hands):
                y = 69 + p * 129
                name = game.names[p] if p == 0 else f"{game.names[p]} ({strategies[p - 1]})"
                text(f"{name}  -  {len(hand)} cards", (22, y), (22, 80, 150) if p == game.player else "black")
                spacing = min(58, 890 // max(1, len(hand) - 1))
                for i, card in enumerate(hand):
                    picked = p == 0 and i in selected
                    rect = pygame.Rect(22 + i * spacing, y + 29 - (4 if picked else 0), 54, 72)
                    draw_card(card, rect, picked)
                    if human and not game.offer and ((p == 0 and not taking) or (p != 0 and taking)):
                        clicks.append((rect, ("Card", p, i)))

            text(game.message, (22, 463))
            if game.winner is not None:
                result = "You win!" if game.winner == 0 else f"{game.names[game.winner]} wins!"
                text(f"Congratulations! {result}", (22, 501), large=True)
                button("Play Again", pygame.Rect(22, 550, 150, 40), ("Start",))
            elif game.offer and human:
                text("Click the card you want to keep.", (22, 507))
                for i, card in enumerate(game.offer):
                    rect = pygame.Rect(352 + i * 65, 503, 54, 72)
                    draw_card(card, rect)
                    clicks.append((rect, ("Keep", i)))
            else:
                hint = "Click an opponent's card, or click Take Card again to cancel." if taking else "Select your cards to discard."
                if not human:
                    hint = "Playing your turn..." if auto else "Computer is playing..."
                text(hint, (22, 491))
                for i, action in enumerate(ACTIONS):
                    enabled = human and game.allowed(action)
                    if action == "Discard One":
                        enabled = enabled and len(selected) == 1
                    if action == "Discard Group":
                        enabled = enabled and valid_group([game.hands[0][j] for j in selected])
                    label = "End Turn" if action == "Pass" and game.used else action
                    if action in LIMITS:
                        label += f" ({LIMITS[action] - game.used.get(action, 0)})"
                    button(label, pygame.Rect(22 + i * 156, 522, 146, 37), (action,), enabled)
                button("Play for Me", pygame.Rect(22, 569, 146, 37), ("Auto",), human)

        pygame.display.flip()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type != pygame.MOUSEBUTTONDOWN or event.button != 1:
                continue
            for rect, command in reversed(clicks):
                if rect.collidepoint(event.pos):
                    break
            else:
                continue
            clicks = []  # Redraw before accepting another click.
            action = command[0]
            if action == "Count":
                opponents = command[1]
            elif action == "Strategy":
                i = command[1]
                strategies[i] = "Groups" if strategies[i] == "Random" else "Random"
            elif action == "Start":
                game = Game(opponents)
                selected, taking, auto = [], False, False
            elif action == "Menu":
                game = None
            elif action == "Auto":
                selected, taking, auto = [], False, True
                next_move = now + 400
            elif action == "Take Card":
                selected = []
                taking = not taking
            elif action == "Keep":
                game.keep(command[1])
            elif action == "Card":
                _, p, i = command
                if taking:
                    game.play("Take Card", [i], p)
                    taking = False
                elif i in selected:
                    selected.remove(i)
                else:
                    selected.append(i)
            else:
                game.play(action, selected)
                selected, taking = [], False
                next_move = now + 650
        clock.tick(30)

    pygame.quit()


if __name__ == "__main__":
    main()
