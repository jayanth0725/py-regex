import sys
import argparse
import csv

from regex_parser import is_malformed, preprocess_character_classes, add_concatenation, postfix_conversion, desugar_postfix
from nfa import build_nfa


def debug_mode():
    pass


parser = argparse.ArgumentParser()
parser.add_argument('--debug', action='store_true')

args = parser.parse_args()

regex = input().replace(" ", "")

input_text = sys.stdin.read()

if is_malformed(regex):
    print("Parse error: Malformed regex", file = sys.stderr)
    exit(1)

else:
    input_words = input_text.split()
    answer = []

    # Expand [a-z] into (a|b|...|z)
    no_classes_regex = preprocess_character_classes(regex)

    # Insert '.' operators for concatenation
    concatenated_regex = add_concatenation(no_classes_regex)

    # Convert infix to postfix using Shunting-yard algorithm
    postfix = postfix_conversion(concatenated_regex)

    # Desugar the '+' and '?' operators using the stack method
    final_postfix = desugar_postfix(postfix)

    # Stage 2: Build the NFA for the regex by Thompson's Construction
    final_nfa = build_nfa(final_postfix)

    if args.debug:
        debug_mode()

    for word in answer:
        print(word)