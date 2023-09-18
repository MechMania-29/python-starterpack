import argparse
from datetime import datetime
from enum import Enum
import json
import os
import subprocess
import threading
import time
import traceback
from typing import IO
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

raw_debug_env = os.environ.get("DEBUG")
DEBUG = raw_debug_env == "1" or raw_debug_env == "true"


# A argument parser that will also print help upon error
class HelpArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        sys.stderr.write("error: %s\n" % message)
        self.print_help()
        sys.exit(2)


class RunOpponent(Enum):
    SELF = "self"
    HUMAN_COMPUTER = "humanComputer"
    ZOMBIE_COMPUTER = "zombieComputer"


COMMANDS_FOR_OPPONENT: dict[RunOpponent, list[tuple[str, str]]] = {
    RunOpponent.SELF: [
        ("Engine", "java -jar engine/engine.jar 9001 9002"),
        ("Human", "python main.py serve 9001"),
        ("Zombie", "python main.py serve 9002"),
    ],
    RunOpponent.HUMAN_COMPUTER: [
        ("Engine", "java -jar engine/engine.jar 0 9002"),
        ("Zombie", "python main.py serve 9002"),
    ],
    RunOpponent.ZOMBIE_COMPUTER: [
        ("Engine", "java -jar engine/engine.jar 9001 0"),
        ("Human", "python main.py serve 9001"),
    ],
}


def run(opponent: RunOpponent):
    engine.update_if_not_latest()

    print(
        f"Running against opponent {opponent.value}... (might take a minute, please wait)"
    )

    info = COMMANDS_FOR_OPPONENT[opponent]
    prefixes = list(map(lambda x: x[0], info))
    commands = list(map(lambda x: x[1], info))

    now = datetime.now()
    formatted_now = now.strftime("%Y_%m_%d__%H_%M_%S")
    gamelog_name = f"gamelog_{formatted_now}"
    output_loc = f"gamelogs/{gamelog_name}.json"
    new_env = os.environ.copy()
    new_env["OUTPUT"] = output_loc

    # Launch each command in a separate terminal
    processes: list[subprocess.Popen] = []
    for command in commands:
        process = subprocess.Popen(
            command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            bufsize=1,
            text=True,
            env=new_env,
        )
        processes.append(process)

    outputs: list[list[tuple[bool, int, int, str]]] = []

    def run_and_output(io: IO, i: int, is_err: True):
        list = []
        for line in iter(io.readline, ""):
            line: str
            list.append((is_err, time.time_ns(), i, line.strip()))

        outputs.append(list)

    threads: list[threading.Thread] = []
    for i in range(len(processes) - 1, -1, -1):
        process = processes[i]

        thread_stdout = threading.Thread(
            target=run_and_output, args=(process.stdout, i, False)
        )
        thread_stderr = threading.Thread(
            target=run_and_output, args=(process.stderr, i, True)
        )
        thread_stdout.start()
        thread_stderr.start()
        threads.append(thread_stdout)
        threads.append(thread_stderr)

    for thread in threads:
        thread.join()

    all = []

    for output in outputs:
        for data in output:
            all.append(data)

    all.sort(key=lambda x: x[1])

    last = -1

    for data in all:
        is_err, time_ns, i, line = data

        if i != last:
            last = i
            print(f"[{prefixes[i]}]:")

        print(f"\t{line}")

    files = []

    prefix = f"logs/{gamelog_name}/"
    if not os.path.exists(prefix):
        os.makedirs(prefix, exist_ok=True)

    for i in range(len(processes)):
        filename = f"{prefix}{prefixes[i].lower()}.txt"
        files.append(filename)
        output = list(map(lambda x: x[3], filter(lambda x: x[2] == i, all)))

        with open(filename, "w") as file:
            file.write("\n".join(output))

    print(
        "\nNote that output above may not be in the exact order it was output, due to terminal limitations.\n"
        + f"For separated ordered output, see: {', '.join(files)}"
    )


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
                phase = received_message.phase
                message = received_message.message
                turn = message["turn"]

                if phase != "CHOOSE_CLASSES" and phase != "FINISH":
                    game_state = GameState.deserialize(message)

                if phase != "FINISH":
                    if DEBUG:
                        print(
                            f"[TURN {turn}]: Getting your bot's response to {phase} phase..."
                        )
                    strategy = choose_strategy(is_zombie)

                if phase == "CHOOSE_CLASSES":
                    raw_possible_classes: list = message["choices"]
                    possible_classes: list[CharacterClassType] = list(
                        map(lambda x: CharacterClassType[x], raw_possible_classes)
                    )
                    num_to_pick = message["numToPick"]
                    max_per_same_class = message["maxPerSameClass"]

                    raw_output = strategy.decide_character_classes(
                        possible_classes, num_to_pick, max_per_same_class
                    )

                    if raw_output == None:
                        raise RuntimeError(
                            "Your decide_character_classes strategy returned nothing (None)!"
                        )

                    output = dict()

                    for [class_type, num] in raw_output.items():
                        output[class_type.value] = num

                    response = json.dumps(output)

                    client.write(response)
                elif phase == "MOVE":
                    raw_possible_moves: dict = message["possibleMoves"]
                    possible_moves = dict()

                    for [id, possibles] in raw_possible_moves.items():
                        actions: list[MoveAction] = list()
                        for possible in possibles:
                            actions.append(MoveAction.deserialize(possible))

                        possible_moves[id] = actions

                    output = strategy.decide_moves(possible_moves, game_state)

                    if output == None:
                        raise RuntimeError(
                            "Your decide_moves strategy returned nothing (None)!"
                        )

                    response = json.dumps(list(map(MoveAction.serialize, output)))

                    client.write(response)
                elif phase == "ATTACK":
                    raw_possible_attacks: dict = message["possibleAttacks"]
                    possible_attacks = dict()

                    for [id, possibles] in raw_possible_attacks.items():
                        actions: list[AttackAction] = list()
                        for possible in possibles:
                            actions.append(AttackAction.deserialize(possible))

                        possible_attacks[id] = actions

                    output = strategy.decide_attacks(possible_attacks, game_state)

                    if output == None:
                        raise RuntimeError(
                            "Your decide_attacks strategy returned nothing (None)!"
                        )

                    response = json.dumps(list(map(AttackAction.serialize, output)))

                    client.write(response)
                elif phase == "ABILITY":
                    raw_possible_abilities: dict = message["possibleAbilities"]
                    possible_abilities = dict()

                    for [id, possibles] in raw_possible_abilities.items():
                        actions: list[AbilityAction] = list()
                        for possible in possibles:
                            actions.append(AbilityAction.deserialize(possible))

                        possible_abilities[id] = actions

                    output = strategy.decide_abilities(possible_abilities, game_state)

                    if output == None:
                        raise RuntimeError(
                            "Your decide_abilities strategy returned nothing (None)!"
                        )

                    response = json.dumps(list(map(AbilityAction.serialize, output)))

                    client.write(response)
                elif phase == "FINISH":
                    humans_score = message["scores"]["humans"]
                    zombies_score = message["scores"]["zombies"]
                    humans_left = message["stats"]["humansLeft"]
                    zombies_left = message["stats"]["zombiesLeft"]
                    turn = message["stats"]["turns"]
                    errors = message["errors"]
                    your_errors = errors["zombieErrors" if is_zombie else "humanErrors"]
                    formatted_errors = "\n".join(your_errors)
                    formatted_errors_message = (
                        f"Your bot had {len(your_errors)} errors:\n${formatted_errors}"
                        if len(your_errors) > 0
                        else "Your bot had no errors."
                    )

                    print(
                        f"\n{formatted_errors_message}\n\n"
                        f"Finished game on turn {turn} with {humans_left} humans and {zombies_left} zombies.\n"
                        + f"Score: {humans_score}-{zombies_score} (H-Z). You were the {'humans' if not is_zombie else 'zombies'}."
                    )
                    break
                else:
                    raise RuntimeError(f"Unknown phase type {phase}")

                if DEBUG:
                    print(f"[TURN {turn}]: Send response to {phase} phase to server!")

            except Exception as e:
                print(f"Something went wrong running your bot: {e}", file=sys.stderr)
                traceback.print_exc(file=sys.stderr)
                client.write("null")


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
