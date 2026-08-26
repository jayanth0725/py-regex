import sys
import argparse
import csv


class State:
    _id_counter = 0

    def __init__(self):
        # Assign a globally uniqu ID to each state for debugging and DFA conversion
        self.id = State._id_counter
        State._id_counter += 1

        # Dictionary mapping a character (or 'ε') to a list of destination States
        self.transitions = {}

    def add_transition(self, char, dest_state):
        if char not in self.transitions:
            self.transitions[char] = []
        self.transitions[char].append(dest_state)


class NFA_Fragment:
    def __init__(self, start_state, accept_state):
        self.start = start_state
        self.accept = accept_state


def build_nfa(postfix):
    # Reset the counter so every new regex starts at State 0
    State._id_counter = 0
    stack = []

    for char in postfix:
        if char == '.':
            # Concatenation
            frag_B = stack.pop()
            frag_A = stack.pop()

            # Connect A's accept to B's start with an ε transition
            frag_A.accept.add_transition('ε', frag_B.start)

            # The new fragement spans from A's start to B's accept
            stack.append(NFA_Fragment(frag_A.start, frag_B.accept))

        elif char == '|':
            # Union
            frag_B = stack.pop()
            frag_A = stack.pop()

            start = State()
            accept = State()

            # ε transitions from the new start state to both fragments
            start.add_transition('ε', frag_A.start)
            start.add_transition('ε', frag_B.start)

            # ε transitions from both fragments to the new accept
            frag_A.accept.add_transition('ε', accept)
            frag_B.accept.add_transition('ε', accept)

            stack.append(NFA_Fragment(start, accept))

        elif char == '*':
            # Kleene Star
            frag_A = stack.pop()

            start = State()
            accept = State()

            # Loop back to the start of A, and skip to the accept state
            frag_A.accept.add_transition('ε', frag_A.start)
            frag_A.accept.add_transition('ε', accept)

            # Enter A, or bypass A entirely (O occurrences)
            start.add_transition('ε', frag_A.start)
            start.add_transition('ε', accept)

            stack.append(NFA_Fragment(start, accept))
            
        else:
            # Base Case (Literal character or 'ε' from desugaring)
            start = State()
            accept = State()

            start.add_transition(char, accept)

            stack.append(NFA_Fragment(start, accept))

    # The final item on the stack is the completed NFA for the whole regex
    return stack[0] if stack else None


def is_malformed(regex):
    allowed_ops = set("+*|.()+?[]-")

    # Check for unsupported characters/operators
    for char in regex:
        if not char.isalnum() and char not in allowed_ops:
            return True

    # Check for stacked quantifiers
    quantifiers = set("*+?")
    for i in range(len(regex) - 1):
        if regex[i] in quantifiers and regex[i+1] in quantifiers:
            return True

        # Check for empty or missing operands with '|'
        if regex[i] == '|' and regex[i+1] == '|':
            return True

    # Check if the regex starts or ends without an operand before an operator
    if regex.startswith('|') or regex.endswith('|'):
        return True
    if regex.startswith('*') or regex.startswith('+') or regex.startswith('?'):
        return True

    # Check for unbalanced paranthesis/brackets
    if regex.count('(') != regex.count(')'):
        return True
    if regex.count('[') != regex.count(']'):
        return True

    return False


def preprocess_character_classes(regex):
    result = ""
    i = 0
    length = len(regex)

    while i < length:
        if regex[i] == '[':
            i += 1  # Move past '['
            class_chars = []

            # Collect everything inside the brackets
            while i < length and regex[i] != ']':
                class_chars.append(regex[i])
                i += 1

            # Expand ranges ([a-z]) and individual characters ([abc])
            expanded = []
            j = 0
            while j < len(class_chars):
                # Check if it is a character range like [a-z]
                if j + 2 < len(class_chars) and class_chars[j+1] == '-':
                    start_char = ord(class_chars[j])
                    end_char = ord(class_chars[j+2])

                    for ascii_val in range(start_char, end_char + 1):
                        expanded.append(chr(ascii_val))
                    j += 3  # Skip the 'a', '-' and 'z'
                else:
                    # It is a character class like [abc]
                    expanded.append(class_chars[j])
                    j += 1

            # Join them with or operator and wrap in parentheses
            # So [abc] becomes (a|b|c)
            result += '(' + '|'.join(expanded) + ')'

        else:
            # Not part of a character class, just append the character normally
            result += regex[i]

        i += 1

    return result


def add_concatenation(regex):
    parsed = ""
    length = len(regex)

    # Characters that can appear on the left side of a concatenation
    left_set = set(")*+?")
    # Characters that can appear on the right side of a concatenation
    right_set = set("([")

    for i in range(length):
        parsed += regex[i]

        # Ensures the checks stay within the string
        if i + 1 < length:
            char1 = regex[i]
            char2 = regex[i+1]

            # A '.' is needed if: (Left is alnum or in left_set) and (Right in alnum or in right_set)
            if (char1.isalnum() or char1 in left_set) and (char2.isalnum() or char2 in right_set):
                parsed += '.'

    return parsed


def precedence(op):
    match op:
        case '|':
            return 1
        case '.':
            return 2
        case '*' | '+' | '?':
            return 3
    return 0


def postfix_conversion(parsed):
    postfix = ""
    stack = []

    for char in parsed:
        if char.isalnum():
            postfix += char
        elif char == '(':
            stack.append(char)
        elif char == ')':
            while stack and stack[-1] != '(':
                postfix += stack.pop()
            if stack:
                stack.pop() # Remove the '('
        else:   # It's an operator: |, ., *, +, or ?
            while stack and stack[-1] != '(' and precedence(char) <= precedence(stack[-1]):
                postfix += stack.pop()
            stack.append(char)

    # Pop any remaing operators off the stack
    while stack:
        postfix += stack.pop()
            
    return postfix


def desugar_postfix(postfix):
    stack = []

    # The set of operators to check against
    operators = {'*', '+', '?', '.', '|'}

    for char in postfix:
        match char:
            case '.':
                # Concatenation pops two operands
                right = stack.pop()
                left = stack.pop()
                stack.append(left + right + '.')

            case '|':
                # Union pops two operands
                right = stack.pop()
                left = stack.pop()
                stack.append(left + right + '|')

            case '*':
                # Kleene star pops one operands
                operand = stack.pop()
                stack.append(operand + '*')

            case '+':
                # + pops one operand (A) and pushes AA*
                operand = stack.pop()
                stack.append(operand + operand + '*' + '.')

            case '?':
                # ? pops one operand (A) and pushes A|ε
                # 'ε' denotes an epsilon transition
                operand = stack.pop()
                stack.append(operand + 'ε' + '|')

            case _:
                if char not in operators:
                    # It's an operand. Push it to the stack.
                    stack.append(char)

    # If the regex is valid, the stack will contain exactly one string at the end
    return stack[0] if stack else ""


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
