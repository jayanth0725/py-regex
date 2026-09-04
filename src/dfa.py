def epsilon_closure(nfa_states):
    # Computes the epsilon-closure for a set of NFA states.
    # nfa_states: an iterable (list or set) of State objects.
    stack = list(nfa_states)
    closure = set(nfa_states)

    while stack:
        current_state = stack.pop()

        # Check if the current state has any 'ε' transitions
        if 'ε' in current_state.transitions:
            for next_state in current_state.transitions['ε']:
                # If we haven't visited this state yet, add it to our closure and stack
                if next_state not in closure:
                    closure.add(next_state)
                    stack.append(next_state)

    # The function returns a frozenset.
    # Because a DFA state is a set of NFA states, this set must be hashable so it can be used as a dictionary key later on.
    return frozenset(closure)


def build_dfa(nfa_start, nfa_accept, postfix):
    # Extract the active alphabet (sorted in ASCII order)
    operators = {'*', '+', '?', '.', '|', 'ε'}
    alphabet = sorted(list(set(char for char in postfix if char not in operators)))

    # Dictionary mapping a frozenset of NFA states -> DFA integer ID
    dfa_states = {}

    # Dictionary mapping DFA ID -> {char: destiantion DFA ID}
    dfa_transitions = {}

    # Set of DFA integer IDs that are accepting states
    dfa_accept_states = set()

    # Initialise the start state
    start_subset = epsilon_closure([nfa_start])
    dfa_states[start_subset] = 0
    unprocessed = [start_subset]

    if nfa_accept in start_subset:
        dfa_accept_states.add(0)

    next_id = 1

    # Breadth-First Search
    while unprocessed:
        curr_subset = unprocessed.pop(0)
        curr_id = dfa_states[curr_subset]
        dfa_transitions[curr_id] = {}

        for char in alphabet:
            # Find all NFA states that can be reached by consuming 'char'
            reachable_by_char = []
            for nfa_state in curr_subset:
                if char in nfa_state.transitions:
                    reachable_by_char.extend(nfa_state.transitions[char])

            # If no states are reachable, the transition goes to a dead state.
            # This is represented by not adding it to the transitions dictionary.
            if not reachable_by_char:
                continue

            # Take the epsilon closure of the reachable_states
            dest_subset = epsilon_closure(reachable_by_char)

            # If this new DFA state hasn't been seen yet, assign it an ID and queue it
            if dest_subset not in dfa_states:
                dfa_states[dest_subset] = next_id
                if nfa_accept in dest_subset:
                    dfa_accept_states.add(next_id)

                unprocessed.append(dest_subset)
                next_id += 1

            # Record the transition
            dfa_transitions[curr_id][char] = dfa_states[dest_subset]

    return dfa_states, dfa_transitions, dfa_accept_states, alphabet


def simulate_dfa(input_words, dfa_transitions, dfa_accept_states):
    for word in input_words:
        # State 0 is always the start stae based on the build_dfa logic
        current_state = 0
        is_dead_end = False

        # Run the word through the DFA character by character
        for char in word:
            # Check if there is a valid transition for this character
            if current_state in dfa_transitions and char in dfa_transitions[current_state]:
                current_state = dfa_transitions[current_state][char]
            else:
                # No transition exists; a dead state has been reached
                is_dead_end = True
                break

        # If we didn't hit a dead end and we finsihed in an accepting state, it is a match
        if not is_dead_end and current_state in dfa_accept_states:
            print(word)
