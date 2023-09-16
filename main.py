import argparse
from dataclasses import asdict
from enum import Enum
import json
import socket
import textwrap
import traceback
import engine
import sys
from game.character.action.ability_action import AbilityAction
from game.character.action.attack_action import AttackAction
from game.character.action.move_action import MoveAction
from game.character.character_class_type import CharacterClassType
from game.game_state import GameState

from network.client import Client
from network.received_message import ReceivedMessage
from strategy.choose_strategy import choose_strategy


# A argument parser that will also print help upon error
class HelpArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        sys.stderr.write("error: %s\n" % message)
        self.print_help()
        sys.exit(2)


class RunOpponent(Enum):
    SELF = "self"
    COMPUTER = "computer"


def run(opponent: RunOpponent):
    print(f"Running against opponent {opponent.value}")
    engine.update_if_not_latest()


def serve(port: int):
    print(f"Connecting to server on port {port}...")

    client = Client(port)

    client.connect()

    while True:
        raw_received = client.read()

        if raw_received:
            try:
                received = json.loads(raw_received)
                received_message = ReceivedMessage.deserialize(received)
                is_zombie = received_message.is_zombie
                type = received_message.type
                message = received_message.message
                turn = message["turn"]

                if type != "CHOOSE_CLASSES_PHASE" and type != "FINISH":
                    game_state = GameState.deserialize(message)

                if type != "FINISH":
                    print(f"[TURN {turn}]: Getting your bot's response to {type}...")
                    strategy = choose_strategy(is_zombie)

                if type == "CHOOSE_CLASSES_PHASE":
                    raw_possible_classes: list = message["choices"]
                    possible_classes: list[CharacterClassType] = list(
                        map(lambda x: CharacterClassType[x], raw_possible_classes)
                    )
                    num_to_pick = message["numToPick"]
                    max_per_same_class = message["maxPerSameClass"]

                    raw_output = strategy.decide_character_classes(
                        possible_classes, num_to_pick, max_per_same_class
                    )

                    output = dict()

                    for [class_type, num] in raw_output.items():
                        output[class_type.value] = num

                    response = json.dumps(output)

                    print(response)

                    client.write(response)
                elif type == "MOVE_PHASE":
                    raw_possible_moves: dict = message["possibleMoves"]
                    possible_moves = dict()

                    for [id, possibles] in raw_possible_moves.items():
                        actions: list[MoveAction] = list()
                        for possible in possibles:
                            actions.append(MoveAction.deserialize(possible))

                        possible_moves[id] = actions

                    output = strategy.decide_moves(possible_moves, game_state)

                    response = json.dumps(list(map(MoveAction.serialize, output)))

                    client.write(response)
                elif type == "ATTACK_PHASE":
                    raw_possible_attacks: dict = message["possibleAttacks"]
                    possible_attacks = dict()

                    for [id, possibles] in raw_possible_attacks.items():
                        actions: list[AttackAction] = list()
                        for possible in possibles:
                            actions.append(AttackAction.deserialize(possible))

                        possible_attacks[id] = actions

                    output = strategy.decide_attacks(possible_attacks, game_state)

                    response = json.dumps(list(map(AttackAction.serialize, output)))

                    client.write(response)
                elif type == "ABILITY_PHASE":
                    raw_possible_abilities: dict = message["possibleAbilities"]
                    possible_abilities = dict()

                    for [id, possibles] in raw_possible_abilities.items():
                        actions: list[AbilityAction] = list()
                        for possible in possibles:
                            actions.append(AbilityAction.deserialize(possible))

                        possible_abilities[id] = actions

                    output = strategy.decide_abilities(possible_abilities, game_state)

                    response = json.dumps(list(map(AbilityAction.serialize, output)))

                    client.write(response)
                elif type == "FINISH":
                    humans_score = message["scores"]["humans"]
                    zombies_score = message["scores"]["zombies"]
                    humans_left = message["stats"]["humansLeft"]
                    zombies_left = message["stats"]["zombiesLeft"]
                    turn = message["stats"]["turns"]

                    print(
                        f"Finished game on turn {turn} with {humans_left} humans and {zombies_left} zombies.\n"
                        + f"Score: {humans_score}-{zombies_score} (H-Z). You were the {'humans' if not is_zombie else 'zombies'}."
                    )
                    break
                else:
                    raise RuntimeError(f"Unknown phase type {type}")

                print(f"[TURN {turn}]: Send response to {type} to server!")

            except Exception as e:
                print(f"Something went wrong running your bot: {e}")
                traceback.print_exc()


def main():
    parser = HelpArgumentParser(description="MechMania 29 bot runner")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    serve_parser = subparsers.add_parser(
        "serve",
        help="Serves your bot to an engine on the port passed, requires engine to be running there",
    )
    serve_parser.add_argument("port", type=int, help="Port to connect to")

    run_parser = subparsers.add_parser("run", help="Run your bot against an opponent")
    run_parser.add_argument(
        "opponent",
        choices=list(map(lambda opponent: opponent.value, list(RunOpponent))),
        help="Opponent to put your bot against, where self is your own bot or computer is against a simple computer bot",
    )

    args = parser.parse_args()

    # Match to a valid command
    if args.command == "serve":
        return serve(args.port)
    elif args.command == "run":
        for opponent in list(RunOpponent):
            if opponent.value == args.opponent:
                return run(opponent)

    # If no valid command, print help
    parser.print_help()


if __name__ == "__main__":
    main()
