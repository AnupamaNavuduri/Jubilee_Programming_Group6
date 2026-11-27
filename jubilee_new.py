import random
from itertools import combinations
from pathlib import Path

import pygame



white = (255, 255, 255)
gold = (225, 188, 110)
darkBlue = (7, 16, 43)

cardColors = {
    "red": (180, 42, 58),
    "green": (26, 113, 65),
    "yellow": (142, 94, 12),
    "black": (39, 43, 52),
    "blue": (35, 86, 164),
}

MAX_HAND = 20
LIMITS = {"Draw One": 1, "Take Card": 1, "Draw Two": 1, "Discard One": 2}


class Card:
    def __init__(self, color, number):
        self.color = color
        self.number = number
        self.selected = False

    def __str__(self):
        return f"{self.color} {self.number}"

    def draw(self, screen, rect, font):
        pygame.draw.rect(screen, darkBlue, rect.move(3, 5), border_radius=10)
        pygame.draw.rect(screen, cardColors[self.color], rect, border_radius=10)
        drawText(screen, str(self.number), font, white, rect.center)

        if self.selected:
            pygame.draw.rect(screen, gold, rect, width=3, border_radius=10)
        elif rect.collidepoint(pygame.mouse.get_pos()):
            pygame.draw.rect(screen, white, rect, width=2, border_radius=10)


class Background:
    def __init__(self, screen):
        self.image = self.load("blue_bg", ".jpg", screen.get_size())
        self.frame = screen.get_rect().inflate(-28, -28)

    def load(self, name, extension, size):
        folder = Path(__file__).resolve().parent
        for directory in (folder, folder / "upload"):
            for filename in (name + extension, name + "(1)" + extension):
                path = directory / filename
                if path.is_file():
                    image = pygame.image.load(path).convert()
                    return pygame.transform.smoothscale(image, size)
        return None

    def draw(self, screen):
        screen.fill((16, 54, 108))
        if self.image:
            screen.blit(self.image, (0, 0))
        pygame.draw.rect(screen, gold, self.frame, width=1, border_radius=20)


class Deck:
    def __init__(self):
        self.cards = []

        for color in cardColors:
            for number in range(1, 10):
                self.cards.append(Card(color, number))
                self.cards.append(Card(color, number))

        self.shuffle()

    def shuffle(self):
        random.shuffle(self.cards)

    def add_back(self, cards):
        self.cards.extend(cards)
        self.shuffle()

    def takeCard(self):
        return self.cards.pop()

    def draw(self, screen, rect, font, back):
        if back and self.cards:
            screen.blit(back, rect)
            return
        pygame.draw.rect(screen, darkBlue, rect.move(3, 7), border_radius=10)
        pygame.draw.rect(screen, white, rect.move(0, 4), border_radius=10)
        pygame.draw.rect(screen, (12, 29, 70), rect, border_radius=10)
        pygame.draw.rect(screen, gold, rect, width=2, border_radius=10)
        drawText(screen, "Deck", font, white, rect.center)


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
                self.hand.append(deck.takeCard())

    def remove_card(self, card):
        if card in self.hand:
            card.selected = False
            self.hand.remove(card)

    def get_card_position(self, index, side):
        if side:
            column = index // 7
            row = index % 7
            columns = (len(self.hand) + 6) // 7
            count = min(7, len(self.hand) - column * 7)
            x = self.base_x + column * self.spacing_x
            x += (3 - columns) * self.spacing_x // 2
            y = self.base_y + row * self.spacing_y
            y += (7 - count) * self.spacing_y // 2
        else:
            row = index // 10
            column = index % 10
            count = min(10, len(self.hand) - row * 10)
            x = self.base_x + column * self.spacing_x
            x += (10 - count) * self.spacing_x // 2
            y = self.base_y + row * self.spacing_y
            if len(self.hand) <= 10:
                y += self.spacing_y // 2
        return x, y



def drawText(screen, text, font, color, position):
    label = font.render(text, True, color)
    labelRect = label.get_rect(center=position)
    screen.blit(label, labelRect)


def drawButton(screen, rect, text, font, enabled=True):
    color = (28, 57, 124)
    border = gold

    if not enabled:
        color = (35, 45, 72)
        border = (100, 115, 145)
    elif rect.collidepoint(pygame.mouse.get_pos()):
        color = (43, 77, 151)

    pygame.draw.rect(screen, darkBlue, rect.move(0, 4), border_radius=10)
    pygame.draw.rect(screen, color, rect, border_radius=10)
    pygame.draw.rect(screen, border, rect, width=2, border_radius=10)
    drawText(screen, text, font, white, rect.center)

class BotPlayer(Player):
    def play_turn(self, game):
        steps = []
        game.bot_steps[self.name] = steps
        while game.winner is None:
            moves = [("Pass", [], None)]
            for action in ("Draw One", "Draw Two"):
                if game.allowed(action):
                    moves.append((action, [], None))
            for index, player in enumerate(game.players):
                if index != game.current:
                    for card in player.hand:
                        if game.allowed("Take Card", [card], index):
                            moves.append(("Take Card", [card], index))
            for card in self.hand:
                if game.allowed("Discard One", [card]):
                    moves.append(("Discard One", [card], None))
            for group in combinations(self.hand, 3):
                if game.allowed("Discard Group", group):
                    moves.append(("Discard Group", group, None))
                    break
            action, cards, target = random.choice(moves)
            if action == "Pass":
                if not steps:
                    steps.append("Passed.")
                return
            game.play(action, cards, target)
            if game.offer:
                choice = random.randrange(2)
                steps.append(f"Drew two and kept {game.offer[choice]}.")
                game.keep(choice)
            elif action == "Discard One":
                steps.append(f"Discarded {cards[0]}.")
            elif action == "Discard Group":
                steps.append(f"Discarded a group of {len(cards)} cards.")
            else:
                step = game.message[len(self.name) + 1:]
                steps.append(step[0].upper() + step[1:])


class CoreLogic:
    def __init__(self, single_player):
        self.deck = Deck()
        self.players = [Player("Player 1", 203, 538, 56, 78, True)]
        if single_player:
            self.players.append(BotPlayer("Computer Player", 203, 85, 56, 78, False))
        else:
            self.players.append(BotPlayer("Computer Player 2", 28, 88, 54, 76, False))
            self.players.append(BotPlayer("Computer Player 3", 774, 88, 54, 76, False))
        for player in self.players:
            player.draw_from_deck(self.deck, 7)
        self.current = 0
        self.used = {}
        self.offer = []
        self.winner = None
        self.bot_steps = {}
        self.message = ""

    def valid_group(self, cards):
        if len(cards) < 3:
            return False
        numbers = sorted(card.number for card in cards)
        if numbers[0] == numbers[-1]:
            return True
        colors = {card.color for card in cards}
        return len(colors) <= 2 and numbers == list(range(numbers[0], numbers[-1] + 1))

    def allowed(self, action, cards=(), target=None):
        if self.winner or self.offer:
            return False
        if action in LIMITS and self.used.get(action, 0) >= LIMITS[action]:
            return False

        hand = self.players[self.current].hand
        if action in ("Discard One", "Discard Group"):
            if len(set(cards)) != len(cards):
                return False
            for card in cards:
                if card not in hand:
                    return False
            if action == "Discard One":
                return len(cards) == 1
            return self.valid_group(cards)

        if len(hand) >= MAX_HAND:
            return False
        if action == "Draw One":
            return len(self.deck.cards) >= 1
        if action == "Draw Two":
            return len(self.deck.cards) >= 2
        if action == "Take Card":
            if target not in range(len(self.players)) or target == self.current:
                return False
            return len(cards) == 1 and cards[0] in self.players[target].hand
        return False

    def play(self, action, cards=(), target=None):
        if not self.allowed(action, cards, target):
            return False
        self.used[action] = self.used.get(action, 0) + 1
        player = self.players[self.current]
        if action == "Draw One":
            player.draw_from_deck(self.deck, 1)
            self.message = f"{player.name} drew {player.hand[-1]}."
        elif action == "Draw Two":
            self.offer = [self.deck.takeCard(), self.deck.takeCard()]
        elif action == "Take Card":
            other = self.players[target]
            card = cards[0]
            other.remove_card(card)
            player.hand.append(card)
            self.message = f"{player.name} took {card} from {other.name}."
            if not other.hand:
                self.winner = other
        else:
            for card in cards:
                player.remove_card(card)
            self.deck.add_back(cards)
            self.message = f"{player.name} discarded {len(cards)} card(s)."
            if not player.hand:
                self.winner = player
        return True

    def keep(self, index):
        if not self.offer or index not in (0, 1):
            return
        player = self.players[self.current]
        card = self.offer[index]
        player.hand.append(card)
        self.deck.add_back([self.offer[1 - index]])
        self.offer = []
        self.message = f"{player.name} kept {card}."

    def next_player(self):
        self.current = (self.current + 1) % len(self.players)
        self.used = {}

    def end_turn(self):
        if self.offer or self.winner:
            return
        for card in self.players[self.current].hand:
            card.selected = False
        self.message = ""
        self.bot_steps = {}
        self.next_player()
        while not self.winner and not self.players[self.current].is_human:
            self.players[self.current].play_turn(self)
            if not self.winner:
                self.next_player()
        if len(self.players) == 3:
            self.message = ""


class Main:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((960, 720))
        pygame.display.set_caption("Jubilee!")
        self.clock = pygame.time.Clock()
        self.background = Background(self.screen)
        self.back = self.background.load("cardback", ".png", (60, 84))
        self.titleFont = pygame.font.SysFont("arial", 58, bold=True)
        self.cardFont = pygame.font.SysFont("arial", 27, bold=True)
        self.smallFont = pygame.font.SysFont("arial", 17, bold=True)
        self.singleButton = pygame.Rect(350, 240, 260, 42)
        self.multiButton = pygame.Rect(350, 296, 260, 42)
        self.stepFont = pygame.font.SysFont("arial", 14)
        self.menuButton = pygame.Rect(29, 26, 84, 29)
        self.deckRect = pygame.Rect(450, 255, 60, 84)
        self.offerRects = [pygame.Rect(367, 255, 60, 84),
                           pygame.Rect(533, 255, 60, 84)]
        self.buttons = {
            "Draw One": pygame.Rect(214, 446, 124, 38),
            "Draw Two": pygame.Rect(350, 446, 124, 38),
            "Discard": pygame.Rect(486, 446, 124, 38),
            "End Turn": pygame.Rect(622, 446, 124, 38),
        }
        self.game = None
        self.visibleCards = []

    def selected_cards(self):
        hand = self.game.players[self.game.current].hand
        return [card for card in hand if card.selected]

    def button_enabled(self, action):
        game = self.game
        if action == "End Turn":
            return not game.offer and game.winner is None
        cards = self.selected_cards()
        if action == "Discard":
            return game.allowed(self.discard_action(cards), cards)
        return game.allowed(action)

    def discard_action(self, cards):
        if len(cards) == 1:
            return "Discard One"
        return "Discard Group"

    def draw_game(self):
        game = self.game
        self.visibleCards = []
        for index, player in enumerate(game.players):
            side = len(game.players) == 3 and index != 0
            if side:
                center = (player.base_x + 79, player.base_y + 264)
            else:
                center = (480, player.base_y + 75)

            size = (50, 72)
            card_rects = []
            for card_index in range(len(player.hand)):
                rect = pygame.Rect(player.get_card_position(card_index, side), size)
                card_rects.append(rect)

            if card_rects:
                panel = card_rects[0].unionall(card_rects)
                panel = panel.inflate(16, 32).move(0, -8)
                if panel.width < 100:
                    panel = panel.inflate(100 - panel.width, 0)
            else:
                panel = pygame.Rect(0, 0, 100, 32)
                panel.center = center

            border = gold if index == game.current else white
            pygame.draw.rect(self.screen, darkBlue, panel, border_radius=8)
            pygame.draw.rect(self.screen, border, panel, 1, border_radius=8)
            drawText(self.screen, player.name, self.smallFont, border,
                     (panel.centerx, panel.top + 12))
            for card, rect in zip(player.hand, card_rects):
                card.draw(self.screen, rect, self.cardFont)
                self.visibleCards.append((rect, index, card))

        if len(game.players) == 3:
            for index, name in enumerate(game.bot_steps):
                x = 350 + index * 260
                drawText(self.screen, name + "’s last turn",
                         self.smallFont, gold, (x, 61))
                for row, step in enumerate(game.bot_steps[name]):
                    drawText(self.screen, step, self.stepFont, white, (x, 83 + row * 14))

        drawButton(self.screen, self.menuButton, "‹ Menu", self.smallFont)
        game.deck.draw(self.screen, self.deckRect, self.smallFont, self.back)
        drawText(self.screen, f"{len(game.deck.cards)} cards",
                 self.smallFont, white, (480, 355))
        for card, rect in zip(game.offer, self.offerRects):
            card.draw(self.screen, rect, self.cardFont)

        player = game.players[game.current]
        message = game.message
        if game.winner:
            message = f"{game.winner.name} wins!"
        elif game.offer:
            message = "Click one of the two cards to keep it."
        elif not message and game.used.get("Take Card", 0) == 0 and len(player.hand) < MAX_HAND:
            message = "Click an opponent’s card to take it."
        drawText(self.screen, message, self.smallFont, white, (480, 380))
        if game.winner is None:
            drawText(self.screen, f"{player.name}'s turn", self.smallFont, gold, (480, 405))
        for action, rect in self.buttons.items():
            drawButton(self.screen, rect, action, self.smallFont, self.button_enabled(action))

    def handle_click(self, position):
        if self.game is None:
            if self.singleButton.collidepoint(position):
                self.game = CoreLogic(True)
            elif self.multiButton.collidepoint(position):
                self.game = CoreLogic(False)
            return

        if self.menuButton.collidepoint(position):
            self.game = None
            self.visibleCards = []
            return

        game = self.game
        if game.winner:
            return
        if game.offer:
            for index, rect in enumerate(self.offerRects):
                if rect.collidepoint(position):
                    game.keep(index)
                    break
            return

        for action, rect in self.buttons.items():
            if rect.collidepoint(position) and self.button_enabled(action):
                if action == "End Turn":
                    game.end_turn()
                elif action == "Discard":
                    cards = self.selected_cards()
                    game.play(self.discard_action(cards), cards)
                else:
                    game.play(action)
                return

        for rect, index, card in self.visibleCards:
            if rect.collidepoint(position):
                if index == game.current:
                    card.selected = not card.selected
                else:
                    game.play("Take Card", [card], index)
                return

    def run(self):
        running = True
        while running:
            self.background.draw(self.screen)
            if self.game is None:
                drawText(self.screen, "Jubilee", self.titleFont, gold, (480, 145))
                drawButton(self.screen, self.singleButton, "Single Player", self.smallFont)
                drawButton(self.screen, self.multiButton, "Multiplayer", self.smallFont)
            else:
                self.draw_game()
            pygame.display.flip()

            clicked = False
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and not clicked:
                    self.handle_click(event.pos)
                    clicked = True
            self.clock.tick(60)
        pygame.quit()


if __name__ == "__main__":
    Main().run()
