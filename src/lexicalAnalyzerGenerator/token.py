class Token:
    def __init__(self, type: str, lexeme: str, line: int):
        self.type = type
        self.lexeme = lexeme
        self.line = line

    def __repr__(self):
        return f"Token({self.type}, {self.lexeme}, línea {self.line})"
