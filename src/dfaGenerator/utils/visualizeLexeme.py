def visualize_lexeme(token_type: str, lexeme: str) -> str:
    if token_type == "WHITESPACE":
        if lexeme == " ":
            return "' '"  # un espacio
        elif lexeme == "\t":
            return r"'\t'"
        elif lexeme == "\n":
            return r"'\n'"
        else:
            # Por si vienen varios juntos
            return repr(lexeme)
    return lexeme