from graphviz import Digraph
import os
import platform

def graph_dfa(dfa_states, transitions, accepting_states):
    """
    Genera y visualiza el DFA (no minimizado) usando Graphviz.

    Parámetros:
      - dfa_states: diccionario que mapea (frozenset de posiciones) a un número de estado.
      - transitions: diccionario de transiciones, con formato:
            { estado (frozenset): { símbolo: estado_destino (frozenset), ... }, ... }
      - accepting_states: conjunto de identificadores de estados finales.

    Se asume que el estado inicial es el que tiene id 0.
    """
    dot = Digraph(comment="DFA")
    
    # Determinar el estado inicial: buscamos el estado cuya asignación sea 0.
    initial_state = None
    for state, state_id in dfa_states.items():
        if state_id == 0:
            initial_state = state
            break
    if initial_state is None:
        raise ValueError("No se encontró el estado inicial (id 0) en dfa_states.")
    
    # Crear un nodo invisible para la flecha de inicio
    dot.node("start", label="", shape="none")
    dot.edge("start", str(dfa_states[initial_state]), label="start")
    
    # Crear los nodos para cada estado
    # Se muestra la etiqueta con el número de estado y el conjunto de posiciones (ordenado para mayor legibilidad)
    for state, state_id in dfa_states.items():
        label = f"q{state_id}\n{sorted(list(state))}"
        if state_id in accepting_states:
            dot.node(str(state_id), label=label, shape="doublecircle")
        else:
            dot.node(str(state_id), label=label, shape="circle")
    
    # Crear las aristas (transiciones)
    for state, trans in transitions.items():
        from_state_id = dfa_states[state]
        for symbol, dest_state in trans.items():
            to_state_id = dfa_states[dest_state]
            dot.edge(str(from_state_id), str(to_state_id), label=symbol)
    
    # Renderizar y guardar la imagen (por defecto graphAFD.png) y abrirla automáticamente
    output_path = dot.render("graphAFD", format="png", cleanup=True)
    try:
        if platform.system() == "Darwin":       # macOS
            os.system(f"open {output_path}")
        elif platform.system() == "Windows":    # Windows
            os.startfile(output_path)
        else:                                   # Linux y otros
            os.system(f"xdg-open {output_path}")
    except Exception as e:
        print("No se pudo abrir la imagen automáticamente:", e)
    
    return dot

