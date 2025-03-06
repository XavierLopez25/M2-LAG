def validar_regex(regex: str) -> bool:
    """
    Valida que la expresión regular sólo contenga los caracteres permitidos:
      - Operandos: letras (a-z, A-Z), dígitos (0-9) y el símbolo '#' para cadena vacía.
      - Operadores: '|', '.', '*', '+' y paréntesis '(' y ')'.
      - Soporta secuencias escapadas (precedidas por '\') y clases de caracteres entre '[' y ']'.
    
    Verifica además que los paréntesis y las clases de caracteres (entre '[' y ']') estén balanceados.
    """
    # Definimos un conjunto de caracteres “permitidos” fuera de secuencias especiales.
    allowed = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789#$|.+*()?\\[]")
    i = 0
    while i < len(regex):
        char = regex[i]
        if char == '\\':
            i += 1
            if i >= len(regex):
                print("Error: secuencia de escape incompleta.")
                return False
            # Se acepta cualquier carácter escapado.
        elif char == '[':
            i += 1
            if i >= len(regex):
                print("Error: clase de caracteres sin cerrar.")
                return False
            while i < len(regex) and regex[i] != ']':
                if regex[i] == '\\':
                    i += 1
                    if i >= len(regex):
                        print("Error: secuencia de escape incompleta dentro de clase de caracteres.")
                        return False
                i += 1
            if i >= len(regex) or regex[i] != ']':
                print("Error: clase de caracteres sin cerrar.")
                return False
        else:
            if char not in allowed:
                print(f"Caracter inválido encontrado: '{char}'")
                return False
        i += 1

    # Verificar balance de paréntesis (excluyendo corchetes, ya comprobados)
    stack = []
    for char in regex:
        if char == '(':
            stack.append(char)
        elif char == ')':
            if not stack:
                print("Error: paréntesis de cierre sin correspondencia.")
                return False
            stack.pop()
    if stack:
        print("Error: paréntesis de apertura sin correspondencia.")
        return False

    return True
