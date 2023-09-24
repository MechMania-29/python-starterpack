<div align="center">

<a href="https://mechmania.org"><img width="25%" src="https://github.com/MechMania-29/engine/" alt="MechMania 29"></a>

### [website](https://mechmania.org) | python-starterpack | [java-starterpack](https://github.com/MechMania-29/java-starterpack) | [visualizer](https://github.com/MechMania-29/visualizer) | [engine](https://github.com/MechMania-29/engine) | [wiki](https://github.com/MechMania-29/Wiki)

# MechMania Python Starterpack

Welcome to MechMania! The python starterpack will allow you to write a python bot to compete against others.
Two bots will be faced against each other, and then the [engine](https://github.com/MechMania-29/engine) will run a simulation to see who wins!
After the engine runs you'll get a gamelog (a large json file) that you can use in the [visualizer](https://github.com/MechMania-29/visualizer) to
visualize the game's progress and end result.

</div>

---

## Installation

To begin, make sure you have Java 17+ installed. You can test this by running:

```sh
java --version
```

Also, you'll need python 3.9+, and you can make sure you have it by running:

```sh
python --version
```

Make sure you're using 3.9+, or things will break!

To install the engine, you can simply run:

```
python engine.py
```

and you should see an engine.jar appear in engine/engine.jar!

If you don't, you can manually install it by following the instructions on the [engine](https://github.com/MechMania-29/engine) page.

## Getting started

If you haven't read the [wiki](https://github.com/MechMania-29/Wiki) yet, do that first! This starterpack provides the basics for you to get started. All the files you need to worry about editing are located in the `strategy/` directory. `choose_strategy.py` will select the specific strategy to use. You can use this to select different strategies based on whether you're a zombie or not. Each strategy has to implement 4 functions which will determine how your bot responds in each phase. Let's explain them.
- `def decide_character_classes(self,  possible_classes: list[CharacterClassType], num_to_pick: int,  max_per_same_class: int) -> dict[CharacterClassType, int]`
  - This function will return what classes you'll select when you're the human.
  - `possible_classes` gives you the list of possible classes you can choose from, `num_to_pick` gives the total number you can pick, and `max_per_same_class` defines the max of how many characters can be in the same class.
  - You will return a dictionary pairing `CharacterClassType` to the count you want of that.
  - For example, if you wanted 5 medics, you could simply do:
  - ```py
    return {
      CharacterClassType.MEDIC: 5,
    }
    ```
- `def decide_moves(self, possible_moves: dict[str, list[MoveAction]], game_state: GameState) -> list[MoveAction]`
  - This function will return the moves that each character will make.
  - `possible_moves` maps each character id to it's possible MoveActions it can take. You can use this to validate if a move is possible, or pick from this list.
  - `game_state` is the current state of all characters and terrain on the map, you can use this to inform which move you want to make for each character
  - A MoveAction just defines where the character will end up. You don't have to compute the possible moves manually - we give you the possible ones.
  - A character id is just a unqiue string that represents a specific character. You can get a character by id with `game_state.characters.get(id)` -> `Character`
  - You will return a list of moves to take, which should effectively be a move for each character.
- `def decide_attacks(self, possible_attacks: dict[str, list[AttackAction]], game_state: GameState) -> list[AttackAction]`
  - This function will return the attacks that each character will make.
  - `possible_attacks` maps each character id to it's possible AttackActions it can take. You can use this to validate if a move is possible, or pick from this list.
  - `game_state` is the same as above. Use it to inform your actions.
  - An AttackAction can be on terrain or a character, so be careful not to just attack everything. See the file it's defined in for more info.
  - You will return a list of attacks to make, which should be a attack for each character that can attack.
- `def decide_abilities(self, possible_abilities: dict[str, list[AbilityAction]], game_state: GameState) -> list[AbilityAction]`
  - This function will return the abilities that each character will make.
  - `possible_abilities` maps each character id to it's possible AbilityActions it can take.
  - `game_state` is same as above.
  - An AbilityAction can be building a barricade or healing. Use type to determine which.
  - Healing targets a character and building targets a position, so consider that accordingly.

**Several useful tips:**
- Read the docs! Reading the wiki is really important as well as the rest of this README. Don't make this harder!
- All code for MechMania is open source, take advantage of that! For example, [the map can be found on the engine](https://github.com/MechMania-29/engine/blob/main/src/main/resources/maps/main.json).
- You [only have 2.5 seconds](https://github.com/MechMania-29/engine/blob/main/src/main/java/mech/mania/engine/Config.java#L112) to make a decision for each phase! Don't try anything too complicated. (O^4 = bad)
- You cannot import any external libraries.

## Usage

To run your client, you can use the following commands:

### Run your bot against itself

```sh
python main.py run self
```

### Run your bot against the human computer (your bot plays zombies)

```sh
python main.py run humanComputer
```

### Run your bot against the zombie computer (your bot plays humans)

```sh
python main.py run zombieComputer
```

### Serve your bot to a port

You shouldn't need to do this, unless none of the other methods work.
<details>
<summary>Expand instructions</summary>

To serve your bot to a port, you can run it like this:

```sh
python main.py serve [port]
```

Where port is the port you want to serve to, like 9001 for example:

```sh
python main.py serve 9001
```

A full setup with the engine might look like (all 3 commands in separate terminal windows):

```sh
python main.py serve 9001
python main.py serve 9002
java -jar engine.jar 9001 9002
```

</details>

## Uploading

Using the cli, you can upload your bot using:

```ssh
python build.py
mm29 upload build/bot.pyz
```

