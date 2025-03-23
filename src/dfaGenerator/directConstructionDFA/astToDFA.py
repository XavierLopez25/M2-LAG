"""
Implementación del algoritmo directo (followpos) para construir un AFD
a partir del AST generado por syToSyntaxTree.py.

Se calculan para cada nodo las funciones:
  - nullable
  - firstpos
  - lastpos
y se construye la tabla followpos para cada posición (hoja).
Luego, a partir de firstpos de la raíz se genera el AFD no minimizado.
"""

from collections import defaultdict

def annotate_leaves(node, token_info, pos_dict):
    """
    Recorre recursivamente el subárbol y asigna a cada hoja la información del token.
    """
    if node is None:
        return
    if node.izquierdo is None and node.derecho is None:
        print(f"[annotate_leaves] Anotando hoja '{node.valor}' con token_info '{token_info}'")
        node.token = token_info
        if hasattr(node, "pos"):
            pos_dict[node.pos] = (node.valor, token_info)
    else:
        annotate_leaves(node.izquierdo, token_info, pos_dict)
        annotate_leaves(node.derecho, token_info, pos_dict)

def compute_functions(node, pos_counter, pos_dict):
    """
    Recorre el AST en postorden asignando números de posición a las hojas
    y calculando las funciones nullable, firstpos y lastpos para cada nodo.
    
    - pos_counter: lista con un entero (contador mutable) que inicia en 1.
    - pos_dict: diccionario que mapea posición -> símbolo.
    
    Se asume que si un nodo es hoja, se le asigna una posición (excepto, por convención,
    si se utilizase una representación de ε; en nuestro caso, usamos '#' como marcador).
    """
    # Caso hoja (sin hijos)
    if node.izquierdo is None and node.derecho is None:
        # Asumimos que toda hoja representa un símbolo que debe aparecer (incluso '#' se numerará)
        node.nullable = False
        node.pos = pos_counter[0]
        # Se guarda en pos_dict una tupla: (carácter, token_info)
        token_info = getattr(node, "token", None)
        pos_dict[node.pos] = (node.valor, token_info)
        print(f"[compute_functions] Nodo TOKEN encontrado. Se asigna token_info '{token_info}' a subárbol izquierdo")
        pos_counter[0] += 1
        node.firstpos = {node.pos}
        node.lastpos = {node.pos}
        return

    # Procesar subárboles (postorden)
    if node.izquierdo:
        compute_functions(node.izquierdo, pos_counter, pos_dict)
    if node.derecho:
        compute_functions(node.derecho, pos_counter, pos_dict)

    if node.token_type == "TOKEN":
        token_info = node.derecho.valor  
        print(f"[compute_functions] Nodo TOKEN encontrado, asignando token_info: {token_info}")
        # Propagar el token en los subárboles y actualizar pos_dict
        annotate_leaves(node.izquierdo, token_info, pos_dict)
        annotate_leaves(node.derecho, token_info, pos_dict)
        # Calcular nullable, firstpos y lastpos...
        node.nullable = node.izquierdo.nullable and node.derecho.nullable
        node.firstpos = node.izquierdo.firstpos.union(node.derecho.firstpos)
        node.lastpos = node.izquierdo.lastpos.union(node.derecho.lastpos)

    # Calcular según el operador del nodo
    if node.token_type == "OPERATOR":
        if node.valor == '|':
            node.nullable = node.izquierdo.nullable or node.derecho.nullable
            node.firstpos = node.izquierdo.firstpos.union(node.derecho.firstpos)
            node.lastpos = node.izquierdo.lastpos.union(node.derecho.lastpos)
        elif node.valor == '.':
            node.nullable = node.izquierdo.nullable and node.derecho.nullable
            if node.izquierdo.nullable:
                node.firstpos = node.izquierdo.firstpos.union(node.derecho.firstpos)
            else:
                node.firstpos = node.izquierdo.firstpos
            if node.derecho.nullable:
                node.lastpos = node.izquierdo.lastpos.union(node.derecho.lastpos)
            else:
                node.lastpos = node.derecho.lastpos
        elif node.valor == '*':
            node.nullable = True
            node.firstpos = node.izquierdo.firstpos
            node.lastpos = node.izquierdo.lastpos
        else:
            raise ValueError(f"Operador desconocido en compute_functions: {node.valor}")

def compute_followpos(node, followpos):
    """
    Recorre el AST y actualiza la tabla followpos (un diccionario: posición -> conjunto de posiciones)
    de acuerdo con las siguientes reglas:
      - Para un nodo de concatenación ('.'):
            Para cada posición p en lastpos(izquierdo), se añade firstpos(derecho) a followpos[p].
      - Para un nodo de Kleene star ('*'):
            Para cada posición p en lastpos(nodo), se añade firstpos(nodo) a followpos[p].
    """

    # Procesamos nodos de operador.
    if node.token_type == "OPERATOR":
        if node.valor == '.':
                for p in node.izquierdo.lastpos:
                    followpos[p] = followpos[p].union(node.derecho.firstpos)
        elif node.valor == '*':
            for p in node.lastpos:
                followpos[p] = followpos[p].union(node.firstpos)

    # Recorrer recursivamente en postorden
    if node.izquierdo:
        compute_followpos(node.izquierdo, followpos)
    if node.derecho:
        compute_followpos(node.derecho, followpos)

def build_dfa(root, pos_dict, followpos):
    """
    Construye el AFD no minimizado a partir del AST.
    
    - El estado inicial es el conjunto firstpos de la raíz.
    - Se consideran como estados del DFA conjuntos (frozenset) de posiciones.
    - Para cada estado y cada símbolo del alfabeto (obtenido de pos_dict, excepto '#'),
      se define una transición.
    - Un estado es final si contiene la posición correspondiente al marcador '#'.
    
    Retorna:
      - dfa_states: mapeo de estados (frozenset) a números (identificador de estado).
      - transitions: diccionario con transiciones (estado, símbolo) -> estado destino.
      - accepting_states: conjunto de identificadores de estados finales.
    """
    # Estado inicial
    initial_state = frozenset(root.firstpos)
    unmarked = [initial_state]
    dfa_states = {initial_state: 0}
    transitions = {}
    accepting_states = {}

    while unmarked:
        state = unmarked.pop()
        print(f"[build_dfa] Procesando estado (id: {dfa_states[state]}): {state}")
        transitions[state] = {}
        # Construir el alfabeto usando el primer elemento de la tupla (símbolo)
        alphabet = set()
        for p in state:
            sym, _ = pos_dict[p]
            alphabet.add(sym)
        print(f"[build_dfa] Alfabeto del estado: {alphabet}")
        for symbol in alphabet:
            new_state = set()
            for p in state:
                sym, _ = pos_dict[p]
                if sym == symbol:
                    new_state = new_state.union(followpos[p])
            new_state = frozenset(new_state)
            if new_state:
                transitions[state][symbol] = new_state
                if new_state not in dfa_states:
                    dfa_states[new_state] = len(dfa_states)
                    unmarked.append(new_state)
                    print(f"[build_dfa] Nuevo estado creado (id: {dfa_states[new_state]}): {new_state}")

        # Marcar estado como aceptante si alguna posición tiene token_info
        for p in state:
            sym, token_info = pos_dict[p]
            print(f"[build_dfa] En estado {dfa_states[state]}, hoja pos {p}: símbolo '{sym}', token_info '{token_info}'")
            if sym == '$' and token_info is not None:
                accepting_states[dfa_states[state]] = token_info
                print(f"[build_dfa] Estado {dfa_states[state]} marcado como aceptante con token: {token_info}")
                break  # Con uno basta para marcar el estado
    return dfa_states, transitions, accepting_states

def direct_dfa_from_ast(root):
    """
    Función principal que, a partir del AST (ya construido en syToSyntaxTree.py),
    calcula las funciones calculadas (nullable, firstpos, lastpos) y followpos,
    y luego construye el AFD directo (no minimizado) utilizando el método followpos.
    
    Retorna:
      - dfa_states: mapeo de estados (frozenset) a números de estado.
      - transitions: diccionario de transiciones (estado, símbolo) -> estado destino.
      - accepting_states: conjunto de identificadores de estados finales.
      - pos_dict: mapeo posición -> símbolo.
      - followpos: tabla followpos (diccionario: posición -> conjunto de posiciones).
    """
    pos_counter = [1]      # Contador mutable para asignar posiciones (comienza en 1)
    pos_dict = {}          # Diccionario: posición -> símbolo
    # Calcular funciones en el AST
    compute_functions(root, pos_counter, pos_dict)
    # Inicializar la tabla followpos
    followpos = defaultdict(set)
    compute_followpos(root, followpos)

    # Construir el DFA a partir del AST y de la tabla followpos
    dfa_states, transitions, accepting_states = build_dfa(root, pos_dict, followpos)
    return dfa_states, transitions, accepting_states, pos_dict, followpos
