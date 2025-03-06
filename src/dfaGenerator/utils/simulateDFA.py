"""
Módulo para simular la ejecución de un DFA.
Se espera que se le suministre:
  - transitions: un diccionario que mapea cada estado (número) a otro diccionario de transiciones,
      con el formato: { símbolo: estado_destino, ... }
  - initial_state: el estado inicial del DFA (número)
  - accepting_states: conjunto de estados (números) que son de aceptación.
  
El módulo incluye:
  - simulate_dfa_with_derivation: función que, dada una cadena de entrada, simula el DFA, 
      imprime la derivación y devuelve True si es aceptada, False en caso contrario.
  - process_input: función que permite ingresar cadenas de forma interactiva y muestra el resultado de la simulación.
"""

def simulate_dfa_with_derivation(transitions, initial_state, accepting_states, input_string):
    """
    Simula el DFA sobre la cadena de entrada, mostrando la derivación paso a paso.
    
    Parámetros:
      - transitions: diccionario de transiciones. Ejemplo:
            { 0: {'a': 1, 'b': 0}, 1: {'a': 1, 'b': 2}, ... }
      - initial_state: estado inicial (número).
      - accepting_states: conjunto de estados finales (números).
      - input_string: cadena de entrada a procesar.
      
    El proceso imprime cada transición realizada, por ejemplo:
         Estado 0 -- a --> Estado 1
         Estado 1 -- b --> Estado 2
    Finalmente, se indica si la cadena es aceptada o no.
    
    Retorna:
      - True si, tras procesar la cadena, el estado actual es de aceptación.
      - False en caso contrario.
    """
    derivation = []  # Lista para almacenar los pasos de la derivación
    current_state = initial_state
    derivation.append(f"Estado inicial: {current_state}")
    
    for symbol in input_string:
        # Si no existe una transición para el símbolo en el estado actual, se indica error en la derivación.
        if symbol not in transitions.get(current_state, {}):
            derivation.append(f"No existe transición para el símbolo '{symbol}' en el estado {current_state}.")
            print("Derivación:")
            for line in derivation:
                print(line)
            return False
        next_state = transitions[current_state][symbol]
        derivation.append(f"Estado {current_state} -- {symbol} --> Estado {next_state}")
        current_state = next_state
    
    # Imprime la derivación completa
    print("Derivación:")
    for line in derivation:
        print(line)
        
    # Retorna True si el estado final es de aceptación
    return current_state in accepting_states

def process_input(transitions, initial_state, accepting_states):
    """
    Permite al usuario ingresar cadenas para ser procesadas por el DFA.
    Para cada cadena, muestra la derivación y el resultado de la simulación.
    
    La función finaliza cuando el usuario ingresa una cadena vacía.
    """
    print("Ingrese cadenas para procesarlas (presione Enter sin escribir nada para salir):")
    while True:
        s = input("Cadena: ")
        if s == "":
            break
        result = simulate_dfa_with_derivation(transitions, initial_state, accepting_states, s)
        if result:
            print("  Cadena aceptada\n")
        else:
            print("  Cadena rechazada\n")