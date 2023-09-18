# python-starterpack

## Installation

To begin, make sure you have Java 17+ installed. You can test this by running:

```sh
java --version
```

Also, you'll need python3, and you can make sure you have it by running:

```sh
python --version
```

Make sure you're using 3, or things will break!

## Usage

To modify your strategy, you'll want to edit `strategy/strategy.py`.
You should only need to edit files in the strategy directory.

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
