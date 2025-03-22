class SymbolTable:
    def __init__(self):
        self._table = {}  
        self._counter = 1 

    def add(self, nombre: str, linea: int, tipo_lexico: str = "ID"):
        """
        Agrega un nuevo identificador a la tabla o actualiza la línea si ya existe.
        """
        if nombre not in self._table:
            self._table[nombre] = {
                "id": self._counter,
                "nombre": nombre,
                "tipo_lexico": tipo_lexico,
                "lineas": [linea]
            }
            self._counter += 1
        else:
            if linea not in self._table[nombre]["lineas"]:
                self._table[nombre]["lineas"].append(linea)

    def get(self):
        """Devuelve la tabla de símbolos completa."""
        return self._table

    def print_table(self):
        """Imprime la tabla de símbolos como tabla formateada."""
        print("\nTabla de Símbolos:")
        print(f"{'ID':<5} {'Nombre':<15} {'Tipo léxico':<15} {'Líneas'}")
        print("-" * 50)
        for entry in sorted(self._table.values(), key=lambda x: x['id']):
            lineas_str = ', '.join(str(l) for l in sorted(entry['lineas']))
            print(f"{entry['id']:<5} {entry['nombre']:<15} {entry['tipo_lexico']:<15} {lineas_str}")

