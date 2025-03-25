from graphviz import Digraph
import os
import platform
import copy  # Para hacer copias profundas de los nodos

# Definimos los operadores
OPERADORES = {'|', '.', '*', '+'}

class Nodo:
    def __init__(self, valor, token_type=None, izquierdo=None, derecho=None):
        self.valor = valor          # El símbolo (literal, clase o operador)
        self.token_type = token_type  # "LITERAL", "BRACKET", "OPERATOR" o "TOKEN"
        self.token_info = None      # Información adicional para los nodos de tipo "TOKEN"
        self.izquierdo = izquierdo
        self.derecho = derecho
        
        # Atributos para la construcción del DFA
        self.nullable = False       # Indica si el nodo puede generar la cadena vacía
        self.firstpos = set()       # Conjunto de posiciones iniciales
        self.lastpos = set()        # Conjunto de posiciones finales

    def __str__(self):
        if self.izquierdo is None and self.derecho is None:
            return self.valor
        elif self.izquierdo is not None and self.derecho is None:
            # Por ejemplo, para los nodos TOKEN que solo tienen hijo izquierdo.
            return f"({str(self.izquierdo)}{self.valor})"
        elif self.token_type == "OPERATOR" and self.valor in ["*", "+"]:
            return f"({str(self.izquierdo)}{self.valor})"
        else:
            return f"({str(self.izquierdo)}{self.valor}{str(self.derecho)})"


def expand_bracket(bracket_value: str) -> Nodo:
    """
    Expande un token de clase de caracteres (por ejemplo, "[A-Z]") en un árbol de unión.
    Por ejemplo, "[A-C]" se expande a ((A|B)|C).
    Se soportan rangos (con '-') y caracteres aislados.
    """
    # Eliminar los corchetes inicial y final.
    contenido = bracket_value[1:-1]
    symbols = []
    i = 0
    while i < len(contenido):
        if i + 2 < len(contenido) and contenido[i+1] == '-':
            inicio = contenido[i]
            fin = contenido[i+2]
            for code in range(ord(inicio), ord(fin) + 1):
                symbols.append(chr(code))
            i += 3
        else:
            symbols.append(contenido[i])
            i += 1

    if not symbols:
        raise ValueError("Clase de caracteres vacía.")

    # Construir el árbol OR de forma left-associative:
    nodo = Nodo(symbols[0], "LITERAL")
    for sym in symbols[1:]:
        nodo = Nodo('|', "OPERATOR", izquierdo=nodo, derecho=Nodo(sym, "LITERAL"))
    return nodo

def postfix_a_arbol_sintactico(postfix_tokens: list) -> Nodo:
    """
    Construye un árbol sintáctico a partir de una lista de tokens en notación postfix.
      - Si el token es de tipo "LITERAL", se crea un nodo hoja.
      - Si el token es de tipo "BRACKET", se expande en un árbol OR mediante expand_bracket.
      - Si el token es de tipo "OPERATOR":
            • Si es un operador unario ('*') se extrae un operando.
            • Si es el operador '+' se reescribe como concatenación de la expresión con su Kleene star,
                es decir, se transforma X+ en X . (X)* (no se incluye el '+' en el árbol).
            • Si es un operador binario ('.' o '|') se extraen dos operandos.
    """
    pila = []
    for token in postfix_tokens:
        token_type, token_value = token
        if token_type == "LITERAL":
            pila.append(Nodo(token_value, token_type))
        elif token_type == "BRACKET":
            nodo_bracket = expand_bracket(token_value)
            pila.append(nodo_bracket)
        elif token_type == "TOKEN":
            if token_value is None:
                raise ValueError("Token de tipo 'TOKEN' con valor None detectado. Revisa el postfix.")
            if not pila:
                raise ValueError(f"Error: `TOKEN` {token_value} sin expresión asociada.")
            
            expr = pila.pop()
            token_label = token_value[1:] if token_value.startswith("~") else token_value
            nodo_token = Nodo("~", "TOKEN", izquierdo=expr)

            def anotar_token_info(nodo, token_info):
                if nodo is None:
                        return
                if nodo.izquierdo is None and nodo.derecho is None:
                    nodo.token_info = token_info  # anotar todas las hojas
                else:
                    # print('TOKEN INFO ANTES DE ASIGNAR: ', token_info)
                    anotar_token_info(nodo.izquierdo, token_info)
                    anotar_token_info(nodo.derecho, token_info)

            anotar_token_info(expr, token_label)
            pila.append(nodo_token)
        
        elif token_type == "OPERATOR":
            if token_value == '*':
                if not pila:
                    raise ValueError("Error: Operador '*' sin operando.")
                nodo = Nodo('*', token_type, izquierdo=pila.pop())
                pila.append(nodo)
            elif token_value == '+':
                if not pila:
                    raise ValueError("Error: Operador '+' sin operando.")
                operand = pila.pop()
                # Reescribir: X+ se transforma en X . (X)*  
                nuevo_nodo = Nodo('.', "OPERATOR", izquierdo=operand, 
                                    derecho=Nodo('*', "OPERATOR", izquierdo=copy.deepcopy(operand)))
                pila.append(nuevo_nodo)
            elif token_value == '?':
                if not pila:
                    raise ValueError("Error: Operador '?' sin operando.")
                operand = pila.pop()
                # Reescribir: X? se transforma en (X | ε), usando '#' para representar la cadena vacía (ε)
                epsilon_node = Nodo('#', "LITERAL")
                nuevo_nodo = Nodo('|', "OPERATOR", izquierdo=operand, derecho=epsilon_node)
                pila.append(nuevo_nodo)
            elif token_value in ['.', '|']:
                if len(pila) < 2:
                    raise ValueError(f"Error: Operador {token_value} sin suficientes operandos.")
                derecho = pila.pop()
                izquierdo = pila.pop()
                nodo = Nodo(token_value, token_type, izquierdo, derecho)
                pila.append(nodo)
            else:
                raise ValueError(f"Operador desconocido: {token_value}")
        else:
            raise ValueError(f"Token desconocido en postfix: {token}")
    if len(pila) != 1:
        raise ValueError("Error en la construcción del árbol sintáctico: elementos sobrantes en la pila.")
    return pila[0]

def visualizar_arbol_sintactico(arbol: Nodo, filename="syntax_tree"):
    """
    Genera y visualiza el árbol sintáctico usando Graphviz.
    Cada nodo muestra dos líneas:
      - Primera línea: el símbolo original.
      - Segunda línea: para hojas se asigna un número secuencial; para nodos internos (operadores),
        se asigna una letra griega. Si se agotan las letras, se reinicia desde el inicio agregando un subíndice.
    Se genera un archivo (por defecto syntax_tree.png) y se intenta abrir automáticamente.
    """
    dot = Digraph()
    leaf_counter = [1]   # Contador mutable para hojas (números)
    branch_counter = [0] # Contador mutable para nodos internos (letras griegas)
    greek_letters = ['α','β','γ','δ','ε','ζ','η','θ','ι','κ','λ','μ','ν','ξ','ο','π','ρ','σ','τ','υ','φ','χ','ψ','ω']

    def add_nodes(node):
        node_id = str(id(node))
        left_id = None
        right_id = None
        # Recorrido postorden: procesamos primero los hijos.
        if node.izquierdo is not None:
            left_id = add_nodes(node.izquierdo)
        if node.derecho is not None:
            right_id = add_nodes(node.derecho)
        
        if node.izquierdo is None and node.derecho is None:
            # Nodo hoja: asignar un número secuencial.
            label_sub = str(leaf_counter[0])
            leaf_counter[0] += 1
        else:
            # Nodo interno: asignar una letra griega.
            index = branch_counter[0]
            if index < len(greek_letters):
                label_sub = greek_letters[index]
            else:
                sub_index = index // len(greek_letters)
                letter_index = index % len(greek_letters)
                label_sub = f"{greek_letters[letter_index]}_{sub_index}"
            branch_counter[0] += 1

        label = f"{node.valor}\n{label_sub}"
        dot.node(node_id, label)
        if left_id is not None:
            dot.edge(node_id, left_id)
        if right_id is not None:
            dot.edge(node_id, right_id)
        return node_id

    add_nodes(arbol)
    output_path = dot.render(filename, format='png', cleanup=True)

    # Abrir la imagen automáticamente según el sistema operativo.
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
