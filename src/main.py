from lexicalAnalyzerGenerator.yalParser import parse_yalex
from dfaGenerator.toPostfix.regexToSY import infix_a_postfix
from dfaGenerator.toAST.syToSyntaxTree import postfix_a_arbol_sintactico
from dfaGenerator.directConstructionDFA.astToDFA import direct_dfa_from_ast
from dfaGenerator.minimizeDFA.AFDtoMinimizedAFD import minimize_dfa
import re

def remove_spaces_outside_literals(s):
    """
    Elimina espacios (y otros espacios en blanco, como tabulaciones y saltos de línea)
    de la cadena s, pero preserva los espacios que se encuentren dentro de literales 
    delimitados por comillas dobles.
    
    Ejemplo:
      Entrada: 'let string = "\"" (letter | digit)* "\""'  
      Salida: 'letstring="\"" (letter|digit)* "\""'  
      
    Nota: Este ejemplo asume que las comillas dobles aparecen de forma balanceada.
    """
    result = []
    in_literal = False
    for char in s:
        if char == '"':
            # Al encontrar una comilla doble, se agrega y se cambia el estado.
            result.append(char)
            in_literal = not in_literal
        else:
            # Si estamos dentro de un literal, se agrega tal cual.
            if in_literal:
                result.append(char)
            else:
                # Fuera de un literal, se ignoran espacios, tabulaciones y saltos de línea.
                if char in [' ', '\t', '\n']:
                    continue
                else:
                    result.append(char)
    return "".join(result)

def scan_input(transitions, initial, accepting, input_str):
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
    # Se añade '$' para el análisis interno, pero luego se ignora.
    if not input_str.endswith('$'):
        input_str += '$'
    
    tokens = []
    pos = 0
    n = len(input_str)
    
    # La última posición (con '$') no se procesa como parte del lexema.
    while pos < n - 1:
        current_state = initial
        last_accept_pos = -1  # posición del último carácter aceptado
        current_pos = pos
        
        while current_pos < n:
            char = input_str[current_pos]
            # Si llegamos al final (símbolo terminal) y ya hemos reconocido token, salimos.
            if char == '$' and current_pos == n - 1:
                break

            if char in transitions.get(current_state, {}):
                current_state = transitions[current_state][char]
                current_pos += 1
                if current_state in accepting:
                    last_accept_pos = current_pos
            else:
                break
        
        if last_accept_pos == -1:
            print(f"Error: No se reconoce token a partir de la posición {pos} ('{input_str[pos:]}').")
            return None
        
        token_lexeme = input_str[pos:last_accept_pos]
        tokens.append(token_lexeme)
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
        
        # Si la regla es un literal puro (empieza y termina con comillas), no se le quitan espacios
        if regex.startswith('"') and regex.endswith('"'):
            # Removemos las comillas y escapamos el literal
            literal = regex[1:-1]
            regex = re.escape(literal)
        else:
            # En reglas compuestas, eliminamos espacios solo fuera de literales
            regex = remove_spaces_outside_literals(regex)
        
        combined.append(f"({regex})~{token}")
    
    return "(" + "|".join(combined) + ")$"

def main():
    yalex_file = "easy_lex.yal"
    rules = parse_yalex(yalex_file)

    print("\nReglas extraídas:")
    for regex, token in rules.items():
        print(f"  {regex} -> {token}")

     # Combinar todas las reglas en una sola expresión regular
    combined_regex = combine_rules(rules)
    print("\nRegex combinada:", combined_regex)

    # Ahora, en lugar de iterar por cada regla, se procesa una sola regex combinada:
    postfix_tokens = infix_a_postfix(combined_regex)
    print(f"\nPostfix generado para la regex combinada: {postfix_tokens}")

    ast_root = postfix_a_arbol_sintactico(postfix_tokens)
    print("\nAST generado:")
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

    # print("\n✅ DFA (antes de minimizar):")
    # print("Estados:", converted_transitions.keys())
    # for state, trans in converted_transitions.items():
    #     print(f"Estado {state}: {trans}")
    
    converted_accepting = { s if isinstance(s, int) else dfa_states[s] for s in accepting_states }
    
    # print("\n📌 Estados de aceptación antes de minimizar:", accepting_states)

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
    
    # print("\n📌 Estados de aceptación después de minimizar:", minimized_accepting)

    # print("\n📌 state_to_block generado:", state_to_block)

    # print("\nDFA minimizado generado:")
    # print("Estados:", final_dfa["transitions"].keys())
    # print("Estados finales:", final_dfa["accepting"])

    # Simulación: se pide la cadena completa y se escanean los tokens
    input_str = input("\nIngrese la cadena completa a simular (sin dividir en tokens): ")
    tokens = scan_input(final_dfa["transitions"], final_dfa["initial"], final_dfa["accepting"], input_str)
    
    if tokens is not None:
        print("\nTokens reconocidos:")
        for t in tokens:
            print(f"  {t}")
    else:
        print("Error en el análisis léxico.")





if __name__ == "__main__":
    main()


    #12+34*(56)