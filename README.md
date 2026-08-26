# py-regex

A lightweight, from-scratch regular expression engine written in Python. 

Unlike standard backtracking engines, **py-regex** programmatically constructs a Non-deterministic Finite Automaton (NFA) using Thompson's Construction, and then converts it into a Deterministic Finite Automaton (DFA) via subset construction for efficient, $O(n)$ string matching.

## Architecture
The engine is broken down into three core pipeline stages to separate parsing logic from automata theory:
* **`regex_parser.py`**: Tokenizes the input, desugars syntactic sugar (`+`, `?`, `[a-z]`), and applies the Shunting-yard algorithm to convert infix expressions to postfix notation.
* **`nfa.py`**: Takes the postfix string and builds a state-graph using Thompson's Construction.
* **`py_regex.py`**: The main execution script that orchestrates the pipeline.

## Features
* **Core Operators:** Union (`|`), Concatenation (implicit and explicit), and Kleene Star (`*`).
* **Syntactic Sugar:** Supports One-or-more (`+`), Zero-or-one (`?`), and character classes (`[a-z]`, `[abc]`).
* **Algorithmic Parsing:** Utilizes the Shunting-yard algorithm for parsing and explicit syntax desugaring.
* **No Backtracking:** Strictly simulates input against the compiled DFA, avoiding catastrophic backtracking vulnerabilities.

## Usage

Run the engine by passing text via standard input. The first line is evaluated as the regular expression, and all subsequent lines are treated as the text block to search.

```bash
python3 src/py_regex.py < input.txt
```

## Debug Mode

To inspect the underlying DFA transition matrix before text evaluation, use the `--debug` flag:

```bash
python3 src/py_regex.py --debug < input.txt
```
