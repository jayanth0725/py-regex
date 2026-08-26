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