from lexicalAnalyzerGenerator.yalParser import parse_yalex
from dfaGenerator.toPostfix.regexToSY import infix_a_postfix
from dfaGenerator.toAST.syToSyntaxTree import postfix_a_arbol_sintactico, visualizar_arbol_sintactico
from dfaGenerator.directConstructionDFA.astToDFA import direct_dfa_from_ast
from dfaGenerator.minimizeDFA.AFDtoMinimizedAFD import improve_minimize_dfa
from symbolTable.symbolTableGenerator import SymbolTable
from lexicalAnalyzerGenerator.readFile import read_file
from syntaxChecker.errorChecker import report_lexical_error
from dfaGenerator.utils.visualizeLexeme import visualize_lexeme
import re
import sys
import codecs

def is_escaped(s: str, pos: int) -> bool:
    """
    Devuelve True si el carácter en la posición pos está escapado,
    es decir, precedido por un número impar de barras invertidas.
    """
    count = 0
    pos -= 1
    while pos >= 0 and s[pos] == '\\':
        count += 1
        pos -= 1
    return (count % 2) == 1

def tokenize_regex_str(s: str) -> list:
    """
    Tokeniza la cadena de la expresión regular.
    Retorna una lista de tuplas (tipo, valor) donde:
      - "QUOTED": literal entre comillas (se preservan espacios y escapes).
      - "CLASS": contenido entre corchetes [].
      - "OP": símbolos considerados operadores (como (), |, ., *, +, ? o ~, etc.)
      - "LITERAL": secuencia de caracteres sin espacios ni operadores especiales.
    Se omiten los espacios que estén fuera de literales o clases.
    """
    tokens = []
    i = 0
    while i < len(s):
        # Omitir espacios fuera de tokens
        if s[i].isspace():
            i += 1
            continue

        if s[i] == '"':
            # Token QUOTED: leer hasta la comilla de cierre que no esté escapada
            token_val = s[i]  # incluir la comilla de apertura
            i += 1
            while i < len(s):
                token_val += s[i]
                if s[i] == '"' and not is_escaped(s, i):
                    i += 1
                    break
                i += 1
            tokens.append(("QUOTED", token_val))
        elif s[i] == '[':
            # Token CLASS: leer hasta el cierre de ]
            token_val = s[i]
            i += 1
            while i < len(s) and s[i] != ']':
                token_val += s[i]
                i += 1
            if i < len(s) and s[i] == ']':
                token_val += s[i]
                i += 1
            tokens.append(("CLASS", token_val))
        elif s[i] in '()|.*+?~\\':
            # Token de operador (se tratan individualmente)
            tokens.append(("OP", s[i]))
            i += 1
        else:
            # Acumular caracteres que no son espacios, comillas, corchetes ni operadores
            literal_val = ''
            while i < len(s) and (not s[i].isspace()) and s[i] not in '"[]()|.*+?~\\':
                literal_val += s[i]
                i += 1
            if literal_val:
                tokens.append(("LITERAL", literal_val))
    return tokens

def preprocess_regex(s: str) -> str:
    """
    Reensambla la expresión regular a partir de los tokens, eliminando los espacios
    que estén fuera de literales (QUOTED) y clases (CLASS).
    """
    tokens = tokenize_regex_str(s)
    return "".join(token_val for token_type, token_val in tokens)


def scan_input(transitions, initial, accepting, input_str, symbol_table, dfa_states_mapping, start_line=1):
    
    print(f"\n[main] Contenido raw (repr): {repr(input_str)}")

    if not input_str.endswith('$'):
        input_str += '$'

    tokens = []
    pos = 0
    n = len(input_str)
    linea = start_line

    while pos < n - 1:
        # while pos < n - 1 and input_str[pos].isspace():
        #     if input_str[pos] == '\n':
        #         linea += 1
        #     pos += 1

        if pos >= n - 1:
            break

        current_state = initial
        last_accept_pos = -1
        last_accept_token = None
        current_pos = pos

        while current_pos < n:
            char = input_str[current_pos]
            if char == '$' and current_pos == n - 1:
                break
            if char in transitions.get(current_state, {}):
                current_state = transitions[current_state][char]
                current_pos += 1
                state_id = dfa_states_mapping[current_state]
                if state_id in accepting:
                    last_accept_pos = current_pos
                    last_accept_token = accepting[state_id]
            else:
                break

        if last_accept_pos == -1:
            report_lexical_error(pos, input_str, start_line)
            return None

        lexema = input_str[pos:last_accept_pos]
        tokens.append((last_accept_token, lexema))

        if last_accept_token == "ID":
            symbol_table.add(lexema, linea)

        linea += lexema.count('\n')
        pos = last_accept_pos

    return tokens

def combine_rules(rules):
    combined = []
    token_priority = {}
    for i, (regex, token) in enumerate(rules.items()):
        regex = regex.rstrip('$').strip()
        if regex.startswith('"') and regex.endswith('"'):
            literal = codecs.decode(regex[1:-1], 'unicode_escape')
            processed_regex = ''.join(re.escape(c) for c in literal)
        else:
            processed_regex = preprocess_regex(regex)
        alternative = f"({processed_regex}.{re.escape('$')})~{token}"         
        token_priority[token] = i
        print(f"[combine_rules] Regla procesada: {regex} -> {alternative}")
        combined.append(alternative)

    combined_regex = "(" + "|".join(combined) + ")"
    print(f"[combine_rules] Regex combinada: {combined_regex}")
    return combined_regex, token_priority

def remove_braces_and_dedent(block: str) -> str:
    import textwrap
    match = re.match(r'^\{(.*)\}$', block.strip(), re.DOTALL)
    if match:
        content = match.group(1)
        return textwrap.dedent(content).strip()
    return block.strip()

def main():
    yalex_file = "hard_lex.yal"
    archivo_a_procesar = "teste1.txt"

    original_stdout = sys.stdout
    with open("console_output.txt", "w", encoding="utf-8") as f:
        sys.stdout = f

        parsed = parse_yalex(yalex_file)
        rules = parsed['rules']
        header = parsed.get('header', '')
        trailer = parsed.get('trailer', '')

        print("\nReglas extraídas:")
        for regex, token in rules.items():
            print(f"  {regex} -> {token}")

        combined_regex, token_priority = combine_rules(rules)
        postfix_tokens = infix_a_postfix(combined_regex)
        print(f"[main] Postfix generado: {postfix_tokens}")

        ast_root = postfix_a_arbol_sintactico(postfix_tokens)
        
        print("\n[main] AST generado:")
        print(ast_root)
        visualizar_arbol_sintactico(ast_root, "syntax_tree")


        dfa_states, transitions, accepting_states, pos_dict, followpos = direct_dfa_from_ast(ast_root, token_priority)

        # Convertir los estados con conjuntos (frozenset) a enteros
        converted_transitions = {}
        for state_set, trans in transitions.items():
            state_id = dfa_states[state_set]
            converted_transitions[state_id] = {}
            for sym, target_set in trans.items():
                converted_transitions[state_id][sym] = dfa_states[target_set]

        accepting_state_to_token = accepting_states

        print("\n[main] Iniciando minimización del AFD...")
        min_initial, min_transitions, min_accepting_set, state_to_block, blocks = improve_minimize_dfa(
            converted_transitions,
            set(accepting_state_to_token.keys()),
            accepting_state_to_token
        )        
        print("[main] Minimización completada.")
        min_accepting = {}
        block_to_tokens = {}

        # Recolectar todos los tokens aceptantes por bloque
        for old_state, token in accepting_state_to_token.items():
            if old_state in state_to_block:
                block_id = state_to_block[old_state]
                if block_id not in block_to_tokens:
                    block_to_tokens[block_id] = set()
                block_to_tokens[block_id].add(token)

        # Elegir el token de mayor prioridad por bloque
        for block_id, tokens in block_to_tokens.items():
            best_token = min(tokens, key=lambda t: token_priority.get(t, float('inf')))
            min_accepting[block_id] = best_token

        print("\n[min] Estados aceptantes después de minimización:")
        for estado, token in min_accepting.items():
            print(f"  Estado {estado} -> {token}")

        tabla_simbolos = SymbolTable()
        try:
            contenido = read_file(archivo_a_procesar)

            print(f"\n[main] Contenido procesado con header/trailer:\n{contenido}\n")

            tokens = scan_input(min_transitions, min_initial, min_accepting, contenido, tabla_simbolos, {v: v for v in min_transitions})
            if tokens is not None:
                print("\nTokens reconocidos:")
                for tipo, lex in tokens:
                    printable_lex = visualize_lexeme(tipo, lex)
                    print(f"  {tipo}: '{printable_lex}'")
                print("\nTabla de símbolos generada:")
                tabla_simbolos.print_table()

            header_clean = remove_braces_and_dedent(header)
            trailer_clean = remove_braces_and_dedent(trailer)

            if header or trailer:
                    with open("lexer.txt", "w", encoding="utf-8") as out:
                        out.write(f"{header_clean}\n\n{contenido}\n\n{trailer_clean}")
                        print("\n[main] Archivo 'lexer.txt' generado con header y trailer.")

        except Exception as e:
            print(f"[main] Error al leer o procesar archivo: {e}")

    sys.stdout = original_stdout

if __name__ == "__main__":
    main()

    #12+34*(56)