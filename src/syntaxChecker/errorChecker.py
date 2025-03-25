from lexicalAnalyzerGenerator.token import Token
from typing import List, Tuple, Optional

def report_lexical_error(pos: int, input_str: str, start_line: int = 1):
    """
    Imprime un mensaje de error léxico indicando la línea, columna y carácter
    no reconocido en el texto de entrada.

    Parámetros:
        pos (int): Posición en la cadena donde ocurre el error.
        input_str (str): Texto completo que se está escaneando.
        start_line (int): Línea inicial del análisis (por defecto es 1).
    """
    linea_actual = input_str[:pos].count('\n') + start_line
    linea_inicio = input_str.rfind('\n', 0, pos) + 1
    linea_fin = input_str.find('\n', pos)
    if linea_fin == -1:
        linea_fin = len(input_str)
    linea_contenido = input_str[linea_inicio:linea_fin]
    columna = pos - linea_inicio

    print(f"\n[Error léxico] Ha ocurrido un error en la línea {linea_actual}, columna {columna + 1}:")
    print("\n Línea actual:")
    print(f"  {linea_contenido}")
    print(f"  {' ' * columna}^")
    print(f"  Token no reconocido: '{input_str[pos]}'\n")
    print("  El carácter no forma parte de ningún token definido en la gramática.")

