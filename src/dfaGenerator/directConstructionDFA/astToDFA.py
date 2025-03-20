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
        pos_dict[node.pos] = node.valor
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
        # Propagar los atributos del hijo izquierdo (que contiene la expresión)
        node.nullable = node.izquierdo.nullable
        node.firstpos = node.izquierdo.firstpos
        node.lastpos = node.izquierdo.lastpos

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
    accepting_states = set()

    # Determinar la posición del marcador '$' (marcador de fin de cadena)
    marker_pos = None
    for pos, symbol in pos_dict.items():
        if symbol == '$':
            marker_pos = pos
            break

    while unmarked:
        state = unmarked.pop()
        transitions[state] = {}
        # Para cada símbolo (excluyendo '$')
        alphabet = set()
        for p in state:
            if pos_dict[p] != '$':
                alphabet.add(pos_dict[p])
        for symbol in alphabet:
            new_state = set()
            for p in state:
                if pos_dict[p] == symbol:
                    new_state = new_state.union(followpos[p])
            new_state = frozenset(new_state)
            if new_state:
                transitions[state][symbol] = new_state
                if new_state not in dfa_states:
                    dfa_states[new_state] = len(dfa_states)
                    unmarked.append(new_state)
        # Si el estado contiene la posición del marcador, es un estado final.
        if marker_pos is not None and marker_pos in state:
            accepting_states.add(dfa_states[state])
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
