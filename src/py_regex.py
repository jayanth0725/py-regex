import sys
import argparse

from regex_parser import tokenise_regex, is_malformed, preprocess_character_classes, add_concatenation, postfix_conversion, desugar_postfix
from nfa import build_nfa
from dfa import build_dfa, simulate_dfa


def debug_mode(dfa_transitions, dfa_accept_states, alphabet):
    # Print the header row
    header = ["State"] + alphabet
    print(", ".join(header), file=sys.stderr)

    # Iterate through all discovered DFA states
    # The keys are sorted through to make the output predictable
    for state_id in sorted(dfa_transitions.keys()):
        # Determine the correct prefix
        prefix = ""
        if state_id == 0:
            prefix += "->"
        if state_id in dfa_accept_states:
            prefix += "*"

        state_label = f"{prefix}{state_id}"
        row = [state_label]

        # Process transitions for each character in the sorted alphabet
        for char in alphabet:
            if char in dfa_transitions[state_id]:
                # If there is a valid transition, append the destination ID
                row.append(str(dfa_transitions[state_id][char]))
            else:
                # If it is a dead end, append a dash
                row.append("-")

        # Print the row as a comma-separated string to stderr
        print(", ".join(row), file=sys.stderr)


parser = argparse.ArgumentParser()
parser.add_argument('--debug', action='store_true')

args = parser.parse_args()

regex_string = input().replace(" ", "")

input_text = sys.stdin.read()

regex_tokens = tokenise_regex(regex_string)

if is_malformed(regex_tokens):
    print("Parse error: Malformed regex", file = sys.stderr)
    exit(1)

else:
    input_words = input_text.split()

    # Expand [a-z] into (a|b|...|z)
    no_classes_regex = preprocess_character_classes(regex_tokens)

    # Insert '.' operators for concatenation
    concatenated_regex = add_concatenation(no_classes_regex)

    # Convert infix to postfix using Shunting-yard algorithm
    postfix = postfix_conversion(concatenated_regex)

    # Desugar the '+' and '?' operators using the stack method
    final_postfix_list = desugar_postfix(postfix)

    # Stage 2: Build the NFA for the regex by Thompson's Construction
    final_nfa = build_nfa(final_postfix_list)

    # Stage 3: Subset Construction
    # final_nfa.start and final_nfa.accept are passed so the function can trace the graph
    dfa_states, dfa_transitions, dfa_accept_states, alphabet = build_dfa(final_nfa.start, final_nfa.accept, final_postfix_list)

    if args.debug:
        debug_mode(dfa_transitions, dfa_accept_states, alphabet)

    # Final step: Simulate the text against the DFA and print matches to stdout
    simulate_dfa(input_words, dfa_transitions, dfa_accept_states)


