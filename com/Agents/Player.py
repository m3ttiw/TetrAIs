from com.Core.BaseGame import BaseGame
import pygame


class Player(BaseGame, metaclass=ABCMeta):
    print('player')

    def __init__(self, r_p):
        super().__init__(r_p)
        print("game")
        self.player = True

    def move(self):
        pass


if __name__ == "__main__":
    caption = "Game {game}".format(game=1)
    pygame.display.set_caption(caption)
    # q = Square(4)

    p = Player('r')
    print("fuori")
    newScore, weights = p.run()
    print("Game achieved a score of: ", newScore)
    print("weights ", weights)
