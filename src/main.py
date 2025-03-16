from lexicalAnalyzerGenerator.yalParser import parse_yalex
from dfaGenerator.toPostfix.regexToSY import infix_a_postfix
from dfaGenerator.toAST.syToSyntaxTree import postfix_a_arbol_sintactico
from dfaGenerator.directConstructionDFA.astToDFA import direct_dfa_from_ast
from dfaGenerator.minimizeDFA.AFDtoMinimizedAFD import minimize_dfa

def main():
    yalex_file = "easy_lex.yal"
    rules = parse_yalex(yalex_file)

    print("\n📜 Reglas extraídas:")
    for regex, token in rules.items():
        print(f"  {regex} -> {token}")

    # Aquí se unificarán los DFA individuales
    all_dfa_states = []
    all_transitions = []
    all_accepting_states = {}

    # Procesamos cada regla (regex -> token)
    for regex, token in rules.items():
        print(f"\n⚙️ Procesando regex: {regex} -> {token}")

        # 1. Convertir infix a postfix
        postfix_tokens = infix_a_postfix(regex)
        print(f"🔄 Postfix generado para {regex}: {postfix_tokens}")

        # 2. Generar el AST a partir del postfix
        ast_root = postfix_a_arbol_sintactico(postfix_tokens)
        print("\n🌳 AST generado:")
        print(ast_root)

        # 3. Construir el DFA a partir del AST
        # dfa_states: mapea estados (frozensets) a enteros
        dfa_states, transitions, accepting_states, pos_dict, followpos = direct_dfa_from_ast(ast_root)
        
        # Convertir el estado inicial: tomamos el primer estado (como frozenset) y lo convertimos a entero
        initial_frozenset = next(iter(transitions.keys()))
        initial_state_int = dfa_states[initial_frozenset]
        
        # Convertir las transiciones usando dfa_states
        converted_transitions = {}
        for state, trans in transitions.items():
            int_state = dfa_states[state]
            converted_transitions[int_state] = {}
            for sym, next_state in trans.items():
                converted_transitions[int_state][sym] = dfa_states[next_state]
        
        # Conversión de estados de aceptación:
        # Si un elemento ya es entero, se usa directamente; de lo contrario, se mapea con dfa_states.
        converted_accepting = { s if isinstance(s, int) else dfa_states[s] for s in accepting_states }
        
        print("\n📌 DFA (convertido a enteros) antes de minimizar:")
        print("Estados:", converted_transitions.keys())
        for s, t in converted_transitions.items():
            print(f"Estado {s}: {t}")
        
        # 4. Minimizar el DFA
        minimized_initial, minimized_transitions, minimized_accepting, state_to_block, _ = minimize_dfa(converted_transitions, converted_accepting)
        
        print("\n📌 state_to_block generado:", state_to_block)
        if initial_state_int in state_to_block:
            new_initial = state_to_block[initial_state_int]
            print("✅ Estado inicial encontrado en state_to_block:", new_initial)
        else:
            print("⚠️ Advertencia: El estado inicial original no está en state_to_block. Se usará otro estado válido.")
            new_initial = next(iter(state_to_block.values()))
            print("Nuevo estado inicial asignado:", new_initial)
        
        # 5. Remapear los estados del DFA minimizado para obtener identificadores únicos
        state_offset = len(all_dfa_states)
        remapped_states = { s: s + state_offset for s in minimized_transitions.keys() }
        remapped_transitions = { remapped_states[s]: {sym: remapped_states[d] for sym, d in trans.items()}
                                for s, trans in minimized_transitions.items() }
        remapped_accepting = { remapped_states[s]: token for s in minimized_accepting }
        
        all_dfa_states.extend(remapped_states.values())
        all_transitions.append(remapped_transitions)
        all_accepting_states.update(remapped_accepting)

    # 6. Unir todas las transiciones en un único DFA
    unified_transitions = {}
    for trans in all_transitions:
        unified_transitions.update(trans)

    # 7. Construir el DFA final minimizado
    final_dfa = {
        "initial": new_initial,
        "transitions": unified_transitions,
        "accepting": all_accepting_states
    }

    print("\n✅ DFA minimizado generado:")
    print("Estados:", final_dfa["transitions"].keys())
    print("Estados finales:", final_dfa["accepting"])

if __name__ == "__main__":
    main()
