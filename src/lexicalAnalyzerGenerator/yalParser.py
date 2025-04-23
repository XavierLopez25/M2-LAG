import re
import codecs

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
    lets, rules = {}, {}
    header_lines, rule_lines, trailer_lines = [], [], []

    with open(filepath, 'r', encoding='utf-8') as f:
        raw_lines = f.readlines()

    phase = 'header'
    for line in raw_lines:
        stripped = line.strip()
        if phase == 'header':
            if stripped.startswith('rule tokens'):
                phase = 'rules'
            else:
                header_lines.append(line)
        elif phase == 'rules':
            # si encontramos un bloque sin 'return', quizá empieza el trailer
            if stripped.startswith('{') and 'return' not in stripped and not stripped.endswith('return'):
                phase = 'trailer'
                trailer_lines.append(line)
            else:
                rule_lines.append(line)
        else:  # trailer
            trailer_lines.append(line)

    # 1) extrae las variables let
    for ln in header_lines:
        m = re.match(r"let (\w+)\s*=\s*(.+)", ln)
        if m:
            ident, rex = m.groups()
            lets[ident] = rex

    # 2) expande lets
    def expand_lets(expr):
        while any(ident in expr for ident in lets):
            for ident, val in lets.items():
                expr = expr.replace(ident, f"({val})")
        return expr

    # 3) parsea reglas
    for ln in rule_lines:
        m = re.match(r'(.*?)\s*\{\s*return\s+(\w+)\s*\}', ln)
        if m:
            raw_regex, token = m.groups()
            raw_regex = expand_lets(raw_regex.strip())
            rules[codecs.decode(raw_regex, 'unicode_escape')] = token

    return {
        'rules': rules,
        'header':  "".join(header_lines).strip(),
        'trailer': "".join(trailer_lines).strip()
    }