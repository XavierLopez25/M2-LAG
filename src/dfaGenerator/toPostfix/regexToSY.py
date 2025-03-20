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
    last_token_was_expression = False

    while i < len(regex):
        char = regex[i]
        if char == '\\':
            i += 1
            if i >= len(regex):
                raise ValueError("Secuencia de escape incompleta.")
            tokens.append(("LITERAL", regex[i]))
            last_token_was_expression = True

        elif char == '[':
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
            last_token_was_expression = True
            i = j

        elif char == '~':
            if not last_token_was_expression:
                raise ValueError(f"Error: `TOKEN` sin expresión previa en {regex}.")
            j = i + 1
            token_name = ""
            while j < len(regex) and regex[j].isalnum():
                token_name += regex[j]
                j += 1
            tokens.append(("TOKEN", "~" + token_name))
            last_token_was_expression = False
            i = j - 1

        elif char in {'(', ')'}:
            tokens.append(("PAREN", char))
            if char == ')':
                last_token_was_expression = True
            else:
                last_token_was_expression = False

        elif char in OPERADORES:
            tokens.append(("OPERATOR", char))
            last_token_was_expression = False

        elif char not in {'"'}:  # Ahora NO se ignora '$'
            tokens.append(("LITERAL", char))
            last_token_was_expression = True
        
        i += 1
    return tokens

def insertar_operador_concatenacion_tokens(tokens):
    """
    Inserta explícitamente el operador de concatenación ('.') en la lista de tokens.
    Se evita insertar concatenación cuando el siguiente token es de tipo TOKEN,
    ya que este sirve para marcar la expresión y no es un operando a concatenar.
    """
    new_tokens = []
    for i in range(len(tokens)):
        new_tokens.append(tokens[i])
        if i < len(tokens) - 1:
            current = tokens[i]
            next_tok = tokens[i + 1]
            # Consideramos como operando para el token actual:
            # LITERAL, BRACKET, TOKEN o ")" de PAREN.
            if (current[0] in ["LITERAL", "BRACKET", "TOKEN"] or 
                (current[0] == "PAREN" and current[1] == ")")):
                # Para el siguiente token, NO consideramos TOKEN como operando.
                if (next_tok[0] in ["LITERAL", "BRACKET"] or 
                    (next_tok[0] == "PAREN" and next_tok[1] == "(")):
                    new_tokens.append(("OPERATOR", "."))
    return new_tokens

def insertar_operador_concatenacion(regex: str) -> list:
    """
    Tokeniza la expresión regular e inserta operadores de concatenación explícitos.
    """
    tokens = tokenize(regex)
    tokens_with_concat = insertar_operador_concatenacion_tokens(tokens)
    return tokens_with_concat

def infix_a_postfix_tokens(tokens):
    salida = []
    pila = []
    last_was_operand = False

    for token in tokens:
        token_type, token_value = token

        if token_type in ["LITERAL", "BRACKET"]:
            salida.append(token)
            last_was_operand = True

        elif token_type == "TOKEN":
            if not last_was_operand:
                raise ValueError(f"Error: `TOKEN` {token_value} sin expresión asociada.")
            salida.append(token)
            last_was_operand = False  # Un TOKEN no cuenta como operando

        elif token_type == "OPERATOR":
            while pila and pila[-1][0] == "OPERATOR":
                top_op = pila[-1][1]
                if ((ASOCIATIVIDAD[token_value] == 'left' and PRECEDENCIA[token_value] <= PRECEDENCIA[top_op]) or
                    (ASOCIATIVIDAD[token_value] == 'right' and PRECEDENCIA[token_value] < PRECEDENCIA[top_op])):
                    salida.append(pila.pop())
                else:
                    break
            pila.append(token)
            last_was_operand = False

        elif token_type == "PAREN":
            if token_value == "(":
                pila.append(token)
                last_was_operand = False
            elif token_value == ")":
                while pila and not (pila[-1][0] == "PAREN" and pila[-1][1] == "("):
                    salida.append(pila.pop())
                if not pila:
                    raise ValueError("Error: Paréntesis no balanceados.")
                pila.pop()  # descartar el '('
                last_was_operand = True  # Al cerrar un paréntesis, consideramos que hubo una expresión
            else:
                raise ValueError(f"Token desconocido en PAREN: {token}")
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
