def tokenise_regex(regex_str):
    tokens = []
    i = 0
    length = len(regex_str)

    while i < length:
        if regex_str[i] == '\\' and i + 1 < length:
            # Group the backslash and the escaped character as one token
            tokens.append('\\' + regex_str[i+1])
            i += 2
        else:
            tokens.append(regex_str[i])
            i += 1

    return tokens


def is_operand(token):
    # If the token is an escaped character (eg. '\.'), it is always an operand
    if len(token) > 1 and token.startswith('\\'):
        return True

    # Otherwise, it's an operand if it's not a metacharacter
    allowed_ops = set("+*|.()+?[]-")
    return token not in allowed_ops


def is_malformed(tokens):
    if not tokens:
        return False

    # Check for stacked quantifiers
    quantifiers = set(["*", "+", "?"])
    for i in range(len(tokens) - 1):
        if tokens[i] in quantifiers and tokens[i+1] in quantifiers:
            return True

        # Check for empty or missing operands with '|'
        if tokens[i] == '|' and tokens[i+1] == '|':
            return True

    # Check if the tokens starts or ends without an operand before an operator
    if tokens[0] in {'|', '*', '+', '?'}:
        return True
    if tokens[-1] == '|':
        return True

    # Check for unbalanced paranthesis/brackets
    if tokens.count('(') != tokens.count(')'):
        return True
    if tokens.count('[') != tokens.count(']'):
        return True

    return False


def preprocess_character_classes(tokens):
    result = []
    i = 0
    length = len(tokens)

    while i < length:
        if tokens[i] == '[':
            i += 1  # Move past '['
            class_chars = []

            # Collect everything inside the brackets
            while i < length and tokens[i] != ']':
                class_chars.append(tokens[i])
                i += 1

            # Expand ranges ([a-z]) and individual characters ([abc])
            expanded = []
            j = 0
            while j < len(class_chars):
                # Check if it is a character range like [a-z]
                if j + 2 < len(class_chars) and class_chars[j+1] == '-':
                    # Use [-1] to get the actual character, ignoring the '\' if it was escaped
                    start_char = ord(class_chars[j][-1])
                    end_char = ord(class_chars[j+2][-1])

                    for ascii_val in range(start_char, end_char + 1):
                        expanded.append(chr(ascii_val))
                    j += 3  # Skip the 'a', '-' and 'z'
                else:
                    # It is a character class like [abc]
                    expanded.append(class_chars[j])
                    j += 1

            # Join them with or operator and wrap in parentheses
            # So [abc] becomes (a|b|c)
            result.append('(')
            for idx, char in enumerate(expanded):
                result.append(char)
                if idx < len(expanded) - 1:
                    result.append('|')
            result.append(')')
        else:
            # Not part of a character class, just append the character normally
            result.append(tokens[i])

        i += 1

    return result


def add_concatenation(tokens):
    parsed = []
    length = len(tokens)

    # Characters that can appear on the left side of a concatenation
    left_set = set(")*+?")
    # Characters that can appear on the right side of a concatenation
    right_set = set("([")

    for i in range(length):
        parsed.append(tokens[i])

        # Ensures the checks stay within the string
        if i + 1 < length:
            char1 = tokens[i]
            char2 = tokens[i+1]

            # A '.' is needed if: (Left is alnum or in left_set) and (Right in alnum or in right_set)
            if (is_operand(char1) or char1 in left_set) and (is_operand(char2) or char2 in right_set):
                parsed.append('.')

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


def postfix_conversion(tokens):
    postfix = []
    stack = []

    for char in tokens:
        if is_operand(char):
            postfix.append(char)
        elif char == '(':
            stack.append(char)
        elif char == ')':
            while stack and stack[-1] != '(':
                postfix.append(stack.pop())
            if stack:
                stack.pop() # Remove the '('
        else:   # It's an operator: |, ., *, +, or ?
            while stack and stack[-1] != '(' and precedence(char) <= precedence(stack[-1]):
                postfix.append(stack.pop())
            stack.append(char)

    # Pop any remaing operators off the stack
    while stack:
        postfix.append(stack.pop())

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
                stack.append(left + right + ['.'])

            case '|':
                # Union pops two operands
                right = stack.pop()
                left = stack.pop()
                stack.append(left + right + ['|'])

            case '*':
                # Kleene star pops one operands
                operand = stack.pop()
                stack.append(operand + ['*'])

            case '+':
                # + pops one operand (A) and pushes AA*
                operand = stack.pop()
                stack.append(operand + operand + ['*', '.'])

            case '?':
                # ? pops one operand (A) and pushes A|ε
                # 'ε' denotes an epsilon transition
                operand = stack.pop()
                stack.append(operand + ['ε', '|'])

            case _:
                # It's an operand. Push it to the stack as a list to concatenate later.
                stack.append([char])

    # If the regex is valid, the stack will contain exactly one string at the end
    return stack[0] if stack else []
