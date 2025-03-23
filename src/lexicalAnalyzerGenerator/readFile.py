def read_file(path: str) -> str:
    """
    Lee el contenido de un archivo de texto (como .txt o .py) y lo devuelve como una cadena.
    Si el archivo no existe o no se puede leer, lanza una excepción.
    """
    try:
        with open(path, 'r', encoding='utf-8', newline='') as file:
            return file.read()
    except FileNotFoundError:
        print(f" Error: No se encontró el archivo '{path}'")
        raise
    except Exception as e:
        print(f" Error al leer el archivo: {e}")
        raise