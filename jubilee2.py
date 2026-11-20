import pygame
import random
cardColors = {
    "red": (180, 42, 58),
    "green": (26, 113, 65),
    "yellow": (237, 183, 35),
    "black": (39, 43, 52),
    "blue": (35, 86, 164),
}


class Card:
    def __init__(self, color, number):
        self.color = color
        self.number = number

    def draw(self, screen, rect, font):
        pygame.draw.rect(screen, cardColors[self.color], rect, border_radius=10)
        num = str(self.number)
        whiteNum = font.render(num, True, (255,255,255))
        position = whiteNum.get_rect(center=rect.center)
        screen.blit(whiteNum, position)

class Background:
    def __init__(self):
        self.color = (8,24,58)

    def draw(self, screen):
        screen.fill(self.color)

class Deck:
    def __init__(self):
        self.cards = []
        for color in cardColors:
            for cardNumber in range(1,10):
                self.cards.append(Card(color, cardNumber))
                self.cards.append(Card(color, cardNumber))
        random.shuffle(self.cards)      

    def draw(self):
        return self.cards.pop()

def  main():
    pygame.init()
    screen = pygame.display.set_mode((900,540))
    pygame.display.set_caption("Jubilee Card Game")
    background = Background()
    deck = Deck()
    hand = []
    font = pygame.font.Font(None, 60)
    clock = pygame.time.Clock()

    dealStart = None
    cardDelay = 50
    slideTime = 300

    deckRect = pygame.Rect(0,0, 75, 110)
    deckRect.center = screen.get_rect().center

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if deckRect.collidepoint(event.pos) and len(hand) == 0:
                    for i in range(7):
                        hand.append(deck.draw())

                    dealStart = pygame.time.get_ticks()

        background.draw(screen)

        pygame.draw.rect(screen, (60,95, 155), deckRect, border_radius=10)
        pygame.draw.rect(screen, (255,255,255), deckRect, width=2, border_radius=10)

        if dealStart is not None:
            elapsed = pygame.time.get_ticks() - dealStart

            for i, card in enumerate(hand):
                cardTime = elapsed - i*cardDelay
                if cardTime<0:
                    continue
                progress = min(cardTime/slideTime,1)

                tX = 150 +i*90
                tY = 400

                x = deckRect.x +(tX - deckRect.x)*progress
                y = deckRect.y + (tY - deckRect.y)*progress
                cardRect = pygame.Rect(x,y,75,110)

                card.draw(screen, cardRect, font)

        pygame.display.flip()
        clock.tick(60)
    pygame.quit()

main()