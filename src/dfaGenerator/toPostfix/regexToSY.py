OPERADORES = {'|', '.', '*', '+', '?'}
PRECEDENCIA = {'*': 4, '+': 4, '?': 4, '.': 3, '|': 2}
ASOCIATIVIDAD = {'*': 'right', '+': 'right', '?': 'right', '.': 'left', '|': 'left'}

def tokenize(regex: str):
    """
    Convierte la cadena de la expresión regular en una lista de tokens.
    Cada token es una tupla (tipo, valor), donde el tipo puede ser:
      - "LITERAL": un carácter literal.
      - "BRACKET": una clase/rango de caracteres, ej. "[A-M]".
      - "OPERATOR": alguno de los operadores ('|', '.', '*', '+').
      - "PAREN": paréntesis, con valor "(" o ")".
    Se procesan secuencias escapadas y clases entre corchetes.
    """
    tokens = []
    i = 0
    while i < len(regex):
        char = regex[i]
        if char == '\\':
            i += 1
            if i >= len(regex):
                raise ValueError("Secuencia de escape incompleta.")
            # Se guarda el carácter escapado como literal.
            tokens.append(("LITERAL", regex[i]))
        elif char == '[':
            # Reconocer clase de caracteres o rango.
            j = i + 1
            bracket_content = ""
            while j < len(regex) and regex[j] != ']':
                if regex[j] == '\\':
                    j += 1
                    if j >= len(regex):
                        raise ValueError("Secuencia de escape incompleta en clase de caracteres.")
                    bracket_content += regex[j]
                else:
                    bracket_content += regex[j]
                j += 1
            if j >= len(regex) or regex[j] != ']':
                raise ValueError("Expresión de clase de caracteres sin cerrar.")
            token_value = "[" + bracket_content + "]"
            tokens.append(("BRACKET", token_value))
            i = j  # se ubicará en el ']' y luego se incrementa
        elif char in {'(', ')'}:
            tokens.append(("PAREN", char))
        elif char in OPERADORES:
            tokens.append(("OPERATOR", char))
        else:
            tokens.append(("LITERAL", char))
        i += 1
    return tokens

def insertar_operador_concatenacion_tokens(tokens):
    """
    Inserta explícitamente el operador de concatenación ('.') en la lista de tokens.
    Se inserta cuando:
      - El token actual es de tipo "LITERAL" o "BRACKET", o es un paréntesis de cierre,
        o es un operador de repetición (postfijo) ('*' o '+'),
      - Y el siguiente token es de tipo "LITERAL" o "BRACKET" o es un paréntesis de apertura.
    """
    new_tokens = []
    for i in range(len(tokens)):
        new_tokens.append(tokens[i])
        if i < len(tokens) - 1:
            current = tokens[i]
            next_tok = tokens[i + 1]
            # Determinamos si current es "operand-like"
            if (current[0] in ["LITERAL", "BRACKET"]) or (current[0] == "PAREN" and current[1] == ")") or (current[0] == "OPERATOR" and current[1] in ["*", "+", "?"]):
                # Determinamos si next_tok es "operand-like" (para concatenar)
                if (next_tok[0] in ["LITERAL", "BRACKET"]) or (next_tok[0] == "PAREN" and next_tok[1] == "("):
                    new_tokens.append(("OPERATOR", "."))
    return new_tokens

def insertar_operador_concatenacion(regex: str) -> list:
    """
    Tokeniza la expresión regular e inserta operadores de concatenación explícitos.
    Devuelve la lista de tokens resultante.
    """
    tokens = tokenize(regex)
    tokens_with_concat = insertar_operador_concatenacion_tokens(tokens)
    return tokens_with_concat

def infix_a_postfix_tokens(tokens):
    """
    Convierte una lista de tokens en notación infix a una lista de tokens en notación postfix (RPN)
    usando el algoritmo de Shunting Yard.
    """
    salida = []
    pila = []
    for token in tokens:
        token_type, token_value = token
        if token_type in ["LITERAL", "BRACKET"]:
            salida.append(token)
        elif token_type == "OPERATOR":
            while pila and pila[-1][0] == "OPERATOR":
                top_op = pila[-1][1]
                if ((ASOCIATIVIDAD[token_value] == 'left' and PRECEDENCIA[token_value] <= PRECEDENCIA[top_op]) or
                    (ASOCIATIVIDAD[token_value] == 'right' and PRECEDENCIA[token_value] < PRECEDENCIA[top_op])):
                    salida.append(pila.pop())
                else:
                    break
            pila.append(token)
        elif token_type == "PAREN":
            if token_value == "(":
                pila.append(token)
            elif token_value == ")":
                while pila and not (pila[-1][0] == "PAREN" and pila[-1][1] == "("):
                    salida.append(pila.pop())
                if not pila:
                    raise ValueError("Error: Paréntesis no balanceados.")
                pila.pop()  # descartar el '('
        else:
            raise ValueError(f"Token desconocido: {token}")
    while pila:
        if pila[-1][0] == "PAREN":
            raise ValueError("Error: Paréntesis no balanceados.")
        salida.append(pila.pop())
    return salida

def infix_a_postfix(regex: str) -> list:
    """
    Procesa la expresión regular:
      1. Tokeniza y añade concatenaciones explícitas.
      2. Convierte la lista de tokens en notación postfix.
    Devuelve la lista de tokens en postfix.
    """
    tokens = insertar_operador_concatenacion(regex)
    postfix_tokens = infix_a_postfix_tokens(tokens)
    return postfix_tokens
