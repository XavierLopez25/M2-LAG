from lexicalAnalyzerGenerator.yalParser import parse_yalex
from dfaGenerator.toPostfix.regexToSY import infix_a_postfix
from dfaGenerator.toAST.syToSyntaxTree import postfix_a_arbol_sintactico
from dfaGenerator.directConstructionDFA.astToDFA import direct_dfa_from_ast
from dfaGenerator.minimizeDFA.AFDtoMinimizedAFD import minimize_dfa
from symbolTable.symbolTableGenerator import SymbolTable
import re

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


def scan_input(transitions, initial, accepting, input_str, symbol_table, dfa_states_mapping):
    """
    Simula el análisis de una cadena completa utilizando el DFA.

    - transitions: tabla de transiciones del DFA (minimizado).
    - initial: estado inicial del DFA.
    - accepting: conjunto de estados de aceptación.
    - input_str: cadena de entrada (se asume sin '$').

    La función implementa el algoritmo de "maximal munch": 
      desde cada posición, avanza mientras existan transiciones y registra
      la última posición en la que el estado fue aceptante.
    Devuelve una lista de tokens (en este ejemplo, simplemente las subcadenas).
    """
    # Asegurarse de que la cadena termine con el símbolo terminal
    if not input_str.endswith('$'):
        input_str += '$'
    
    tokens = []
    pos = 0
    n = len(input_str)
    linea = 1
    
    while pos < n - 1:
        # Omitir espacios en blanco fuera de literales
        while pos < n - 1 and input_str[pos].isspace():
            if input_str[pos] == '\n':
                linea += 1
            pos += 1

        if pos >= n - 1:
            break
        
        current_state = initial
        last_accept_pos = -1  # posición del último carácter aceptado
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
            print(f"Error: No se reconoce token a partir de la posición {pos} ('{input_str[pos:]}').")
            return None
        
        lexema = input_str[pos:last_accept_pos]
        tokens.append((last_accept_token, lexema))

        if last_accept_token == "ID":
            symbol_table.add(lexema, linea)

        linea += lexema.count('\n')
        pos = last_accept_pos
    
    return tokens


def combine_rules(rules):
    """
    Combina todas las reglas en una única expresión regular usando el operador '|'
    y añade un marcador de token a cada una.
    Si la regla está entre comillas (es literal), se remueven las comillas y se aplica re.escape
    para escapar automáticamente los caracteres especiales.
    """
    combined = []
    for regex, token in rules.items():
        # Quitar el '$' final si está presente y limpiar extremos
        if regex.endswith('$'):
            regex = regex[:-1].strip()
        else:
            regex = regex.strip()
        
        # Para reglas literales puras (empiezan y terminan con comillas y sin espacios internos)
        if regex.startswith('"') and regex.endswith('"') and ' ' not in regex[1:-1]:
            literal = regex[1:-1]
            processed_regex = re.escape(literal)
        else:
            processed_regex = preprocess_regex(regex)
        
        alternative = f"({processed_regex})~({token})"
        print(f"[combine_rules] Regla procesada: {regex} -> {alternative}")
        combined.append(alternative)
    
    combined_regex = "(" + "|".join(combined) + ")$"
    print(f"[combine_rules] Regex combinada: {combined_regex}")
    return combined_regex

def main():
    yalex_file = "hard_lex.yal"
    rules = parse_yalex(yalex_file)

    print("\nReglas extraídas:")
    for regex, token in rules.items():
        print(f"  {regex} -> {token}")

     # Combinar todas las reglas en una sola expresión regular
    combined_regex = combine_rules(rules)
    print("\nRegex combinada:", combined_regex)

    # Ahora, en lugar de iterar por cada regla, se procesa una sola regex combinada:
    postfix_tokens = infix_a_postfix(combined_regex)
    print(f"[main] Postfix generado: {postfix_tokens}")

    ast_root = postfix_a_arbol_sintactico(postfix_tokens)
    print("\n[main] AST generado:")
    print(ast_root)

    # Build the DFA from the AST
    dfa_states, transitions, accepting_states, pos_dict, followpos = direct_dfa_from_ast(ast_root)
    # print("Debug - dfa_states:", dfa_states)
    # print("Debug - transitions:", transitions)
    # print("Debug - accepting_states:", accepting_states)
    # print("Debug - pos_dict:", pos_dict)
    # print("Debug - followpos:", followpos)

    # Convert states and transitions to integers
    initial_frozenset = next(iter(transitions.keys()))
    initial_state_int = dfa_states[initial_frozenset]
    # print("Debug - initial_frozenset:", initial_frozenset)
    # print("Debug - initial_state_int:", initial_state_int)

    converted_transitions = {}
    for state, trans in transitions.items():
        int_state = dfa_states[state]
        converted_transitions[int_state] = {}
        for sym, next_state in trans.items():
            converted_transitions[int_state][sym] = dfa_states[next_state]
    # print("Debug - converted_transitions:", converted_transitions)

    print("\n DFA (antes de minimizar):")
    print("Estados:", converted_transitions.keys())
    for state, trans in converted_transitions.items():
        print(f"Estado {state}: {trans}")
    
    converted_accepting = { s if isinstance(s, int) else dfa_states[s] for s in accepting_states }
    
    # print("\n Estados de aceptación antes de minimizar:", accepting_states)

    # Minimizar el DFA
    minimized_initial, minimized_transitions, minimized_accepting, state_to_block, _ = minimize_dfa(converted_transitions, converted_accepting)
    
    if initial_state_int in state_to_block:
        new_initial = state_to_block[initial_state_int]
    else:
        new_initial = next(iter(state_to_block.values()))
    
    final_dfa = {
        "initial": new_initial,
        "transitions": minimized_transitions,
        "accepting": { s: s for s in minimized_accepting }
    }
    
    print("\n[main] Estados de aceptación después de minimizar:", minimized_accepting)

    print("\n[main] state_to_block generado:", state_to_block)

    print("\n[main] DFA minimizado generado:")
    print("[main] Estados:", final_dfa["transitions"].keys())
    print("[main] Estados finales:", final_dfa["accepting"])

    tabla_simbolos = SymbolTable()
    # Simulación: se pide la cadena completa y se escanean los tokens
    while True:
        input_str = input("\nIngrese la cadena completa a simular (sin dividir en tokens): ")
        if input_str.lower() == "exit":
            break
        tokens = scan_input(final_dfa["transitions"], final_dfa["initial"], final_dfa["accepting"], input_str, tabla_simbolos, state_to_block)
        if tokens is not None:
            print("\nTokens reconocidos:")
            for t in tokens:
                print(f"  {t}")
            print("\n Tabla de símbolos generada:")
            tabla_simbolos.print_table()    
        else:
            print("Error en el análisis léxico.")

if __name__ == "__main__":
    main()


    #12+34*(56)