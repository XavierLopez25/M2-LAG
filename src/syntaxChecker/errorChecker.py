from lexicalAnalyzerGenerator.token import Token

def check_syntax(tokens: list[Token]) -> bool:
    # Esto es una gramática dummy, la real depende del lenguaje.
    for token in tokens:
        if token.type not in {"NUMBER", "PLUS", "TIMES", "LPAREN", "RPAREN"}:
            return False, f"Token inesperado: {token.type} en línea {token.line}"
    return True, None
