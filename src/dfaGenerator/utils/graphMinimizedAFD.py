# graphMinimizedAFD.py
"""
Módulo para graficar el DFA minimizado usando Graphviz.
Se espera que se le suministren:
  - new_transitions: diccionario con la forma { state_id: { símbolo: state_id_destino, ... }, ... }
  - new_accepting: conjunto de estados finales (números)
  - new_initial: estado inicial (número)
El diagrama se guardará (por ejemplo, como "graphMinimizedAFD.png") y se abrirá automáticamente.
"""

from graphviz import Digraph
import os
import platform

def graph_minimized_dfa(new_initial, new_transitions, new_accepting):
    dot = Digraph(comment="DFA Minimizado")
    
    # Crear un nodo invisible para la flecha de inicio.
    dot.node("start", label="", shape="none")
    dot.edge("start", str(new_initial), label="start")
    
    # Crear los nodos para cada estado.
    for state in new_transitions.keys():
        label = f"q{state}"
        shape = "doublecircle" if state in new_accepting else "circle"
        dot.node(str(state), label=label, shape=shape)
        
    # Crear las aristas (transiciones).
    for state, trans in new_transitions.items():
        for symbol, dest in trans.items():
            dot.edge(str(state), str(dest), label=symbol)
    
    # Renderizar y guardar la imagen (por defecto graphMinimizedAFD.png)
    output_path = dot.render("graphMinimizedAFD", format="png", cleanup=True)
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

