from dataclasses import asdict, dataclass
from typing import Optional
from game.character.action.ability_action_type import AbilityActionType
from game.util.assert_blob_has_key_of_type import assert_blob_has_key_of_type
from game.util.position import Position


@dataclass
class AbilityAction:
    """
    An attack action from one character to an object
    """

    executing_character_id: str
    character_id_target: Optional[int]
    positional_target: Optional[Position]
    type: AbilityActionType

    def deserialize(blob: object) -> "AbilityAction":
        try:
            assert_blob_has_key_of_type(blob, "executingCharacterId", str)
            assert_blob_has_key_of_type(blob, "type", str)
            assert any(
                blob["type"] == item.value for item in AbilityActionType
            ), "Invalid attack action type"

            character_id_target = (
                blob["characterIdTarget"]
                if "characterIdTarget" in blob and blob["characterIdTarget"] != None
                else None
            )
            positional_target = (
                Position.deserialize(blob["positionalTarget"])
                if "positionalTarget" in blob and blob["positionalTarget"] != None
                else None
            )

            action = AbilityAction(
                blob["executingCharacterId"],
                character_id_target,
                positional_target,
                AbilityActionType[blob["type"]],
            )
        except:
            print("Failed to validate AbilityAction json")
            raise

        return action

    def serialize(self) -> dict[str, object]:
        return {
            "executingCharacterId": self.executing_character_id,
            "characterIdTarget": self.character_id_target,
            "positionalTarget": self.positional_target.serialize()
            if self.positional_target
            else None,
            "type": self.type.value,
        }
