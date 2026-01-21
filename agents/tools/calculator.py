# agents/tools/calculator.py

def run(a: float, b: float, operation: str = "add"):
    if operation == "add":
        return a + b
    if operation == "subtract":
        return a - b
    if operation == "multiply":
        return a * b
    if operation == "divide":
        if b == 0:
            raise ValueError("Division by zero")
        return a / b

    raise ValueError("Invalid operation")
