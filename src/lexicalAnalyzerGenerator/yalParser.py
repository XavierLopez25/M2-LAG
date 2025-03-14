import re

def expand_lets(expression, lets):
    """
    Reemplaza recursivamente las variables definidas en `let` dentro de una expresión regular.
    """
    while any(ident in expression for ident in lets):  # Mientras haya `let` no reemplazados
        for ident, value in lets.items():
            expression = expression.replace(ident, value if "|" in value else f"({value})")
    return expression

def parse_yalex(filepath: str):
    """
    Parsea un archivo Lexer.yal y extrae:
    - Variables definidas con `let`.
    - Reglas definidas en `rule tokens`.

    Retorna un diccionario donde:
    - Claves: Expresiones regulares (ya reemplazando `let`).
    - Valores: Nombre del token asociado.
    """
    lets = {}  # Diccionario para almacenar las variables let
    rules = {}  # Diccionario para almacenar las reglas finales

    with open(filepath, 'r', encoding='utf-8') as file:
        lines = [line.strip() for line in file if line.strip()]  # Eliminar líneas vacías

    mode = None
    for line in lines:
        if line.startswith('let'):
            # Extraer variables `let`
            match = re.match(r"let (\w+) = (.+)", line)
            if match:
                ident, regex = match.groups()
                lets[ident] = regex
        elif line.startswith('rule tokens'):
            mode = 'rules'
        elif mode == 'rules' and '{' in line:
            # Extraer reglas de tokens
            match = re.match(r'(.*?)\s*\{\s*return\s*(\w+)\s*\}', line)
            if match:
                regex, token = match.groups()

                # Expandir `let` de forma completamente recursiva
                regex = expand_lets(regex, lets)

                # Guardar la regla en el diccionario con regex ya expandida
                rules[regex] = token

    return rules
