from lexicalAnalyzerGenerator.yalParser import parse_yalex
from dfaGenerator.toPostfix.regexToSY import infix_a_postfix
from dfaGenerator.toAST.syToSyntaxTree import postfix_a_arbol_sintactico
from dfaGenerator.directConstructionDFA.astToDFA import direct_dfa_from_ast
from dfaGenerator.minimizeDFA.AFDtoMinimizedAFD import minimize_dfa

def combine_rules(rules):
    """
    Combina todas las reglas en una única expresión regular usando el operador '|'.
    Para cada regla, se encapsula la regex (quitándole el '$' final, si existe) y se le
    añade un marcador (por ejemplo, '#TOKEN') que luego se usará para etiquetar el estado
    de aceptación correspondiente. Finalmente, se añade un único '$' al final.
    """
    combined = []
    for regex, token in rules.items():
        # Quitar el '$' final si está presente
        if regex.endswith('$'):
            regex = regex[:-1].strip()
        # Encapsular la regex y agregar el marcador de token.
        combined.append(f"{regex}~{token}")
    # Unir todas las alternativas con '|' y agregar '$' al final
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

    # Construir el DFA a partir del AST
    dfa_states, transitions, accepting_states, pos_dict, followpos = direct_dfa_from_ast(ast_root)
    
    # Convertir estados y transiciones a enteros
    initial_frozenset = next(iter(transitions.keys()))
    initial_state_int = dfa_states[initial_frozenset]
    
    converted_transitions = {}
    for state, trans in transitions.items():
        int_state = dfa_states[state]
        converted_transitions[int_state] = {}
        for sym, next_state in trans.items():
            converted_transitions[int_state][sym] = dfa_states[next_state]

    print("\n✅ DFA (antes de minimizar):")
    print("Estados:", converted_transitions.keys())
    for state, trans in converted_transitions.items():
        print(f"Estado {state}: {trans}")
    
    converted_accepting = { s if isinstance(s, int) else dfa_states[s] for s in accepting_states }
    
    print("\n📌 Estados de aceptación antes de minimizar:", accepting_states)

    # Minimizar el DFA
    minimized_initial, minimized_transitions, minimized_accepting, state_to_block, _ = minimize_dfa(converted_transitions, converted_accepting)
    
    if initial_state_int in state_to_block:
        new_initial = state_to_block[initial_state_int]
    else:
        new_initial = next(iter(state_to_block.values()))
    
    final_dfa = {
        "initial": new_initial,
        "transitions": minimized_transitions,
        "accepting": {s: accepting_states.get(s, "UNKNOWN") for s in minimized_accepting}   
    }
    
    print("\n📌 Estados de aceptación después de minimizar:", minimized_accepting)

    print("\n📌 state_to_block generado:", state_to_block)

    print("\nDFA minimizado generado:")
    print("Estados:", final_dfa["transitions"].keys())
    print("Estados finales:", final_dfa["accepting"])

if __name__ == "__main__":
    main()
