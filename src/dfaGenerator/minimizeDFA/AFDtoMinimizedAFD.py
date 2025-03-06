"""
Módulo para minimizar un AFD (DFA) no minimizado usando el algoritmo de particiones (Hopcroft).
Se espera que se le suministre:
  - transitions: diccionario con la forma { state_id: { símbolo: state_id_destino, ... }, ... }
  - accepting_states: conjunto de estados (números) que son de aceptación.
  - Se asume que el estado inicial es el 0.
El módulo retorna:
  - new_initial: número del estado inicial del DFA minimizado.
  - new_transitions: diccionario con las transiciones del DFA minimizado.
  - new_accepting: conjunto de estados finales (nuevos).
  - state_to_block: mapeo original de cada estado a su bloque (número de bloque).
  - P: la lista de bloques (cada bloque es un conjunto de estados equivalentes).
"""

def minimize_dfa(transitions, accepting_states):
    # Q es el conjunto de todos los estados (asumidos como las llaves de transitions)
    Q = set(transitions.keys())
    # En caso de que existan estados destino que no sean llave en transitions, agrégalos:
    for s, trans in transitions.items():
        for dest in trans.values():
            Q.add(dest)
            
    # F = estados de aceptación y noF = Q \ F
    F = set(accepting_states)
    nonF = Q - F

    # Inicializar la partición: solo se incluyen bloques no vacíos.
    P = []
    if F:
        P.append(F)
    if nonF:
        P.append(nonF)
        
    # Inicializar W (lista de bloques a procesar)
    W = list(P)
    
    # Calcular el alfabeto: unión de símbolos de todas las transiciones
    alphabet = set()
    for s in Q:
        if s in transitions:
            for sym in transitions[s]:
                alphabet.add(sym)
    
    # Algoritmo de Hopcroft:
    while W:
        A = W.pop()
        for c in alphabet:
            # X es el conjunto de estados que tienen, con el símbolo c, una transición a algún estado en A.
            X = set()
            for s in Q:
                if s in transitions and c in transitions[s]:
                    if transitions[s][c] in A:
                        X.add(s)
            # Dividir cada bloque Y de P en dos (Y∩X y Y\X) si corresponde
            new_P = []
            for Y in P:
                intersection = Y.intersection(X)
                difference = Y - X
                if intersection and difference:
                    new_P.append(intersection)
                    new_P.append(difference)
                    # Actualizar W: si Y estaba en W, se reemplaza por ambos bloques; si no, se añade el de menor tamaño.
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

    # Ahora cada bloque en P es un conjunto de estados equivalentes.
    # Creamos un mapeo de cada estado a su bloque (identificado con un número).
    state_to_block = {}
    for i, block in enumerate(P):
        for s in block:
            state_to_block[s] = i

    # Construir las transiciones del DFA minimizado
    new_transitions = {}
    for block in P:
        rep = next(iter(block))  # elegimos un representante
        block_id = state_to_block[rep]
        new_transitions[block_id] = {}
        # Para cada símbolo, la transición se define a partir del representante.
        if rep in transitions:
            for sym, dest in transitions[rep].items():
                new_transitions[block_id][sym] = state_to_block[dest]

    # Estado inicial minimizado: el bloque que contiene al estado 0.
    new_initial = state_to_block[0]
    # Estados de aceptación minimizados: bloques que contienen al menos un estado de aceptación.
    new_accepting = set()
    for block in P:
        if block.intersection(accepting_states):
            new_accepting.add(state_to_block[next(iter(block))])
            
    return new_initial, new_transitions, new_accepting, state_to_block, P

