import re
from pathlib import Path


class Stack:
    """A simple Last In, First Out (LIFO) stack."""

    def __init__(self):
        self._items = []

    def push(self, item):
        self._items.append(item)

    def pop(self):
        if self.is_empty():
            raise ValueError("Cannot pop from an empty stack.")
        return self._items.pop()

    def peek(self):
        if self.is_empty():
            raise ValueError("Cannot peek at an empty stack.")
        return self._items[-1]

    def is_empty(self):
        return len(self._items) == 0

    def size(self):
        return len(self._items)


TOKEN_PATTERN = re.compile(r"\d+(?:\.\d*)?|\.\d+|[()+\-*/]")


def tokenize(expression):
    """Convert an expression into number/operator/parenthesis tokens."""
    tokens = []
    position = 0

    while position < len(expression):
        if expression[position].isspace():
            position += 1
            continue

        match = TOKEN_PATTERN.match(expression, position)
        if not match:
            raise ValueError(
                f"Invalid character {expression[position]!r} at position {position + 1}."
            )

        tokens.append(match.group())
        position = match.end()

    if not tokens:
        raise ValueError("Expression is empty.")

    return tokens


def is_number(token):
    try:
        float(token)
        return True
    except (TypeError, ValueError):
        return False


def precedence(operator):
    if operator in ("+", "-"):
        return 1
    if operator in ("*", "/"):
        return 2
    if operator in ("u+", "u-"):
        return 3
    return 0


def infix_to_postfix(tokens):
    """Convert infix tokens to postfix notation using a stack."""
    output = []
    operators = Stack()
    previous_kind = "start"

    for token in tokens:
        if is_number(token):
            if previous_kind in ("number", "right_paren"):
                raise ValueError("Missing operator between values.")
            output.append(token)
            previous_kind = "number"

        elif token == "(":
            if previous_kind in ("number", "right_paren"):
                raise ValueError("Missing operator before '('.")
            operators.push(token)
            previous_kind = "left_paren"

        elif token == ")":
            if previous_kind in ("start", "operator", "left_paren"):
                raise ValueError("Empty or incomplete parentheses.")
            while not operators.is_empty() and operators.peek() != "(":
                output.append(operators.pop())
            if operators.is_empty():
                raise ValueError("Mismatched closing parenthesis.")
            operators.pop()  # Remove '('
            previous_kind = "right_paren"

        elif token in ("+", "-", "*", "/"):
            unary = previous_kind in ("start", "operator", "left_paren")
            operator = ("u" + token) if unary and token in ("+", "-") else token

            if unary and token in ("*", "/"):
                raise ValueError(f"Operator {token!r} cannot be unary.")

            # Unary operators are right-associative; binary operators are left-associative.
            while not operators.is_empty() and operators.peek() != "(":
                top = operators.peek()
                if operator in ("u+", "u-"):
                    should_pop = precedence(top) > precedence(operator)
                else:
                    should_pop = precedence(top) >= precedence(operator)
                if not should_pop:
                    break
                output.append(operators.pop())

            operators.push(operator)
            previous_kind = "operator"

        else:
            raise ValueError(f"Unsupported token: {token}")

    if previous_kind in ("start", "operator", "left_paren"):
        raise ValueError("Expression ends unexpectedly.")

    while not operators.is_empty():
        operator = operators.pop()
        if operator == "(":
            raise ValueError("Mismatched opening parenthesis.")
        output.append(operator)

    return output


def evaluate_postfix(postfix_tokens):
    """Evaluate postfix tokens using a value stack."""
    values = Stack()

    for token in postfix_tokens:
        if is_number(token):
            values.push(float(token))
        elif token in ("u+", "u-"):
            if values.size() < 1:
                raise ValueError("Unary operator is missing an operand.")
            value = values.pop()
            values.push(value if token == "u+" else -value)
        elif token in ("+", "-", "*", "/"):
            if values.size() < 2:
                raise ValueError("Binary operator is missing an operand.")
            right = values.pop()
            left = values.pop()

            if token == "+":
                result = left + right
            elif token == "-":
                result = left - right
            elif token == "*":
                result = left * right
            else:
                if right == 0:
                    raise ZeroDivisionError("division by zero")
                result = left / right

            values.push(result)
        else:
            raise ValueError(f"Unsupported postfix token: {token}")

    if values.size() != 1:
        raise ValueError("Malformed expression.")

    return values.pop()


def evaluate_expression(expression):
    """Evaluate one mathematical expression."""
    tokens = tokenize(expression)
    postfix = infix_to_postfix(tokens)
    result = evaluate_postfix(postfix)

    if result.is_integer():
        return str(int(result))
    return f"{result:.10g}"


def is_separator(line):
    """Treat lines containing only repeated non-alphanumeric punctuation as separators."""
    stripped = line.strip()
    return len(stripped) >= 3 and all(not char.isalnum() and not char.isspace() for char in stripped)


def process_file(input_file="input.txt", output_file="output.txt"):
    """Read expressions and write results, retaining separator and blank lines."""
    input_path = Path(input_file)
    output_path = Path(output_file)

    if not input_path.exists():
        raise FileNotFoundError(
            f"Input file '{input_path}' was not found. Put it in the same folder as this program."
        )

    output_lines = []
    for line_number, original_line in enumerate(
        input_path.read_text(encoding="utf-8").splitlines(), start=1
    ):
        stripped = original_line.strip()

        if not stripped:
            output_lines.append(original_line)
        elif is_separator(stripped):
            output_lines.append(original_line)
        else:
            try:
                output_lines.append(evaluate_expression(stripped))
            except Exception as error:
                output_lines.append(f"ERROR (line {line_number}): {error}")

    output_path.write_text("\n".join(output_lines) + "\n", encoding="utf-8")
    print(f"Finished. Results were written to '{output_path}'.")


if __name__ == "__main__":
    try:
        process_file()
    except (OSError, ValueError) as error:
        print(f"Program could not complete: {error}")

