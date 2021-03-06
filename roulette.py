import random
import dataclasses
import matplotlib.pyplot as plt
from typing import List
from functools import lru_cache
import argparse


def parse_args():
    parser = argparse.ArgumentParser(description='')
    parser.add_argument("--mode",
                        "-m",
                        help="[martingale,cocomo,1235,1326,2in1]",
                        type=str)
    parser.add_argument("--amount",
                        "-a",
                        help="initial player's amount",
                        type=int,
                        default=0)
    parser.add_argument("--ntries",
                        "-n",
                        help="number of tries to experiment",
                        type=int,
                        default=100)
    parser.add_argument("--output",
                        "-o",
                        help="plot with matplotlib",
                        type=str,
                        default="")
    return parser.parse_args()


@lru_cache(maxsize=None)
def fibonacci(n):
    if n == 1 or n == 2:
        return 1
    return fibonacci(n - 1) + fibonacci(n - 2)


class Roulette:
    def __init__(self, hole=37):
        self.hole = hole

    def tries(self):
        return random.randrange(self.hole)

    def deal(self, bet, payback_rate):
        number = self.tries()
        if 1 <= number < self.hole // payback_rate:
            return bet * payback_rate
        else:
            return 0


@dataclasses.dataclass
class Player:
    amount: float = 0
    history: List[float] = dataclasses.field(default_factory=list)
    win: int = 0
    lose: int = 0
    max_win: int = 0
    max_lose: int = 0


class Simulation:
    def __init__(self, player, game, ntries, mode, init_bet=1):
        self.player = player
        self.game = game
        self.ntries = ntries
        self.init_bet = init_bet
        self.n = 1  # for cocomo
        self.mode = mode
        self.set_payback_rate(mode)
        self.win_streak = 0  # be negative if lose_streak
        self.twoinone = []
        if mode == "1235":
            self.rotation = [1, 2, 3, 5]
        elif mode == "1326":
            self.rotation = [1, 3, 2, 6]
        self.bet = self.init_bet

    def set_payback_rate(self, mode):
        if mode == "martingale" or mode == "1235" or mode == "1326" or mode == "2in1":
            self.payback_rate = 2
        elif mode == "cocomo":
            self.payback_rate = 3

    def tries(self, bet, payback_rate):
        payback = self.game.deal(bet, payback_rate)
        return payback

    def record(self, bet, payback):
        self.player.amount = self.player.amount - bet + payback
        self.player.history.append(self.player.amount)
        if not payback:
            self.player.lose += 1
            self.win_streak = 0 if 0 < self.win_streak else self.win_streak
            self.win_streak -= 1
        else:
            self.player.win += 1
            self.win_streak = 0 if self.win_streak < 0 else self.win_streak
            self.win_streak += 1
        self.player.max_win = self.win_streak if self.player.max_win < self.win_streak else self.player.max_win
        self.player.max_lose = self.win_streak if self.player.max_lose > self.win_streak else self.player.max_lose

    def set_bet(self):
        if self.win_streak == 0:
            self.bet == self.init_bet
        elif 0 < self.win_streak:
            # win
            if self.mode == "martingale" or self.mode == "cocomo" or self.mode == "2in1":
                self.bet = self.init_bet
            elif self.mode == "1235" or self.mode == "1326":
                self.bet = self.rotation[-1] if len(
                    self.rotation) <= self.win_streak else self.rotation[
                        self.win_streak - 1]
        else:
            # lose
            if self.mode == "martingale":
                self.bet *= 2
            elif self.mode == "cocomo":
                self.bet = fibonacci(-self.win_streak)
            elif self.mode == "1235" or self.mode == "1326":
                self.bet = self.init_bet
            elif self.mode == "2in1":
                if 2 <= len(self.twoinone):
                    self.twoinone.append(1)
                else:
                    self.twoinone.append(self.bet)
        if self.mode == "2in1":
            if 2 <= len(self.twoinone):
                self.bet = self.twoinone[0] + self.twoinone[-1]
            else:
                self.bet = self.init_bet

    def experiment(self):
        for _ in range(self.ntries):
            self.set_bet()
            payback = self.tries(self.bet, self.payback_rate)
            self.record(self.bet, payback)


def main():
    args = parse_args()
    player = Player(amount=args.amount)
    roulette = Roulette()
    simulation = Simulation(player, roulette, args.ntries, args.mode, 1)
    simulation.experiment()
    print(player)
    if args.output:
        plt.plot(player.history)
        plt.savefig(args.output)
        print(f"saved as {args.output}")


if __name__ == "__main__":
    main()
