from strategy.random_strategy import RandomStrategy
from strategy.simple_human_strategy import SimpleHumanStrategy
from strategy.simple_zombie_strategy import SimpleZombieStrategy
from strategy.strategy import Strategy


def choose_strategy(is_zombie: bool) -> Strategy:
    if is_zombie:
        return SimpleZombieStrategy()
    else:
        return SimpleHumanStrategy()

