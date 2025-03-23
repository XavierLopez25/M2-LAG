from collections import defaultdict

def improve_minimize_dfa(transitions, accepting_states, accepting_state_to_token):
    """
    Versión mejorada de minimizar AFD que respeta los distintos tokens asociados a los estados
    de aceptación y evita fusionar estados de aceptación con etiquetas distintas.
    """
    Q = set(transitions.keys())
    for s, trans in transitions.items():
        for dest in trans.values():
            Q.add(dest)

    # Agrupar estados aceptantes por token
    token_to_states = defaultdict(set)
    for state in accepting_states:
        token = accepting_state_to_token[state]
        token_to_states[token].add(state)

    # Estados no aceptantes
    nonF = Q - accepting_states

    # Inicializar partición con grupos separados por token
    P = list(token_to_states.values())
    if nonF:
        P.append(nonF)

    W = list(P)

    # Calcular el alfabeto
    alphabet = set()
    for s in Q:
        if s in transitions:
            for sym in transitions[s]:
                alphabet.add(sym)

    while W:
        A = W.pop()
        for c in alphabet:
            X = set()
            for s in Q:
                if s in transitions and c in transitions[s]:
                    if transitions[s][c] in A:
                        X.add(s)
            new_P = []
            for Y in P:
                intersection = Y.intersection(X)
                difference = Y - X
                if intersection and difference:
                    new_P.append(intersection)
                    new_P.append(difference)
                    if Y in W:
                        W.remove(Y)
                        W.append(intersection)
                        W.append(difference)
                    else:
                        if len(intersection) <= len(difference):
                            W.append(intersection)
                        else:
                            W.append(difference)
                else:
                    new_P.append(Y)
            P = new_P

    state_to_block = {}
    for i, block in enumerate(P):
        for s in block:
            state_to_block[s] = i

    new_transitions = {}
    for block in P:
        rep = next(iter(block))
        block_id = state_to_block[rep]
        new_transitions[block_id] = {}
        if rep in transitions:
            for sym, dest in transitions[rep].items():
                new_transitions[block_id][sym] = state_to_block[dest]

    new_initial = state_to_block[0]

    new_accepting = set()
    for block in P:
        if block.intersection(accepting_states):
            new_accepting.add(state_to_block[next(iter(block))])

    return new_initial, new_transitions, new_accepting, state_to_block, P
