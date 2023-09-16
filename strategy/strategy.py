# This defines the general layout your strategy method will inherit. Do not edit this.

from game.character.action.attack_action import AttackAction
from game.character.action.move_action import MoveAction
from game.character.character_class_type import CharacterClassType
from game.game_state import GameState
from game.util.position import Position


class Strategy:
    def decide_character_classes(
        self,
        possible_classes: list[CharacterClassType],
        num_to_pick: int,
        max_per_same_class: int,
    ) -> dict[CharacterClassType, int]:
        """
        Decide the character classes your humans will use (only called on humans first turn)

        possible_classes: A list of the possible classes you can select from
        num_to_pick: The total number of classes you are allowed to select
        max_per_same_class: The max number of characters you can have in the same class

        You should return a dictionary of class type to the number you want to use of that class
        """
        raise NotImplementedError("Must implement the decide_moves method!")

    def decide_moves(
        self, possible_moves: dict[str, list[MoveAction]], game_state: GameState
    ) -> list[MoveAction]:
        """
        Decide the moves for each character based on the current game state

        possible_moves: Maps character id to it's possible moves. You can use this to validate if a move is possible, or pick from this list.
        game_state: The current state of all characters and terrain on the map
        """
        raise NotImplementedError("Must implement the decide_moves method!")

    def decide_attacks(
        self, possible_attacks: dict[str, list[AttackAction]], game_state: GameState
    ) -> list[AttackAction]:
        """
        Decide the attacks for each character based on the current game state
        """
        raise NotImplementedError("Must implement the decide_attacks method!")
