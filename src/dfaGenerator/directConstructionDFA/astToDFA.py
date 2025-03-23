from collections import defaultdict

def compute_functions(node, pos_counter, pos_dict):
    """
    Asigna posiciones y calcula nullable, firstpos y lastpos para cada nodo del AST.
    """
    if node is None:
        return

    if node.izquierdo is None and node.derecho is None:
        # Nodo hoja
        node.nullable = False
        node.pos = pos_counter[0]
        token_info = getattr(node, "token_info", None)
        pos_dict[node.pos] = (node.valor, token_info)
        print(f"[compute_functions] Hoja '{node.valor}' con pos {node.pos} y token_info='{token_info}'")
        node.firstpos = {node.pos}
        node.lastpos = {node.pos}
        pos_counter[0] += 1
        return

    # Recorrido postorden
    compute_functions(node.izquierdo, pos_counter, pos_dict)
    compute_functions(node.derecho, pos_counter, pos_dict)

    if node.token_type == "TOKEN":
        token_info = node.token_info
        print(f"[compute_functions] Nodo TOKEN con info: '{token_info}'")

        # Propaga el token_info a todas las hojas del subárbol izquierdo
        def annotate_leaves(n, token_info):
            if n is None:
                return
            if n.izquierdo is None and n.derecho is None:
                n.token_info = token_info
            else:
                annotate_leaves(n.izquierdo, token_info)
                annotate_leaves(n.derecho, token_info)

        annotate_leaves(node.izquierdo, token_info)

        if (node.izquierdo.token_type == "OPERATOR" and node.izquierdo.valor == '.' and
        node.izquierdo.derecho is not None and node.izquierdo.derecho.valor == '$'):
            node.izquierdo.derecho.token_info = token_info

        # Propaga atributos de posición del hijo izquierdo
        node.nullable = node.izquierdo.nullable
        node.firstpos = node.izquierdo.firstpos
        node.lastpos = node.izquierdo.lastpos
        return

    # Cálculos según tipo de operador
    if node.token_type == "OPERATOR":
        if node.valor == '|':
            node.nullable = node.izquierdo.nullable or node.derecho.nullable
            node.firstpos = node.izquierdo.firstpos | node.derecho.firstpos
            node.lastpos = node.izquierdo.lastpos | node.derecho.lastpos
        elif node.valor == '.':
            node.nullable = node.izquierdo.nullable and node.derecho.nullable
            node.firstpos = node.izquierdo.firstpos if not node.izquierdo.nullable else (node.izquierdo.firstpos | node.derecho.firstpos)
            node.lastpos = node.derecho.lastpos if not node.derecho.nullable else (node.izquierdo.lastpos | node.derecho.lastpos)
        elif node.valor == '*':
            node.nullable = True
            node.firstpos = node.izquierdo.firstpos
            node.lastpos = node.izquierdo.lastpos

def compute_followpos(node, followpos):
    """
    Llenado de la tabla followpos para nodos concatenación y cierre.
    """
    if node is None:
        return
    if node.token_type == "OPERATOR":
        if node.valor == '.':
            for p in node.izquierdo.lastpos:
                followpos[p].update(node.derecho.firstpos)
        elif node.valor == '*':
            for p in node.lastpos:
                followpos[p].update(node.firstpos)
    compute_followpos(node.izquierdo, followpos)
    compute_followpos(node.derecho, followpos)

def build_dfa(root, pos_dict, followpos, token_priority):
    """
    Construcción del AFD directo a partir del AST usando followpos.
    """
    initial = frozenset(root.firstpos)
    unmarked = [initial]
    dfa_states = {initial: 0}
    transitions = {}
    accepting = {}

    while unmarked:
        state = unmarked.pop()
        transitions[state] = {}
        symbols = defaultdict(set)

        for pos in state:
            symbol, token = pos_dict[pos]
            if symbol != '$':  # <-- evitar transiciones por símbolo '$'
                symbols[symbol].update(followpos[pos])


        for symbol, positions in symbols.items():
            next_state = frozenset(positions)
            if next_state not in dfa_states:
                dfa_states[next_state] = len(dfa_states)
                unmarked.append(next_state)
            transitions[state][symbol] = next_state

        # Detectar todos los posibles tokens de aceptación
        accepting_candidates = []
        for pos in state:
            symbol, token = pos_dict[pos]
            if symbol == '$' and token:
                accepting_candidates.append((token_priority[token], token))

        if accepting_candidates:
            _, best_token = min(accepting_candidates)  # menor índice = mayor prioridad
            accepting[dfa_states[state]] = best_token
            print(f"[build_dfa] Estado {dfa_states[state]} es aceptante para '{best_token}'")

    return dfa_states, transitions, accepting

def direct_dfa_from_ast(root, token_priority):
    pos_counter = [1]
    pos_dict = {}
    compute_functions(root, pos_counter, pos_dict)

    followpos = defaultdict(set)
    compute_followpos(root, followpos)

    dfa_states, transitions, accepting_states = build_dfa(root, pos_dict, followpos, token_priority)
    return dfa_states, transitions, accepting_states, pos_dict, followpos
