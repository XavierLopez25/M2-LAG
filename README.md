# Proyecto LAG: Lexical Analyzer Generator

Este proyecto es una completa herramienta para la generación y análisis de analizadores léxicos basados en expresiones regulares y definiciones de tokens. El sistema se encamina desde la definición de reglas mediante archivos YAL hasta la construcción, minimización y simulación de autómatas finitos deterministas (DFA), incluyendo generación de árboles sintácticos (AST) y visualización gráfica.

---

## Índice

1. [Introducción](#introducción)
2. [Arquitectura y estructura de directorios](#arquitectura-y-estructura-de-directorios)
3. [Componentes principales](#componentes-principales)
   - [Lexical Analyzer Generator](#lexical-analyzer-generator)
   - [Parser de YAL](#parser-de-yal)
   - [Conversión de Expresión Regular a Postfix](#conversión-de-expresión-regular-a-postfix)
   - [Construcción de Árbol Sintáctico (AST)](#construcción-de-árbol-sintáctico-ast)
   - [Construcción y Minimización de DFA](#construcción-y-minimización-de-dfa)
   - [Simulación y Visualización](#simulación-y-visualización)
   - [Generación de Tabla de Símbolos y Chequeo de Errores](#generación-de-tabla-de-símbolos-y-chequeo-de-errores)
4. [Definiciones de Tokens y Archivos YAL](#definiciones-de-tokens-y-archivos-yal)
5. [Flujo de operación](#flujo-de-operación)
6. [Instrucciones de uso](#instrucciones-de-uso)
7. [Dependencias](#dependencias)
8. [Licencia](#licencia)

---

## Introducción

El propósito del proyecto LAG es proporcionar una infraestructura completa para la generación automática de analizadores léxicos. Esto se logra tomando como entrada definiciones de tokens mediante archivos en formato YAL, que definen tanto variables (`let`) como reglas (`rule tokens`). A partir de esta información se generan expresiones regulares combinadas, de las cuales se construye un árbol sintáctico. Este árbol se utiliza para derivar un autómata finito determinista (DFA) mediante el método del followpos. Además, se implementa la minimización del DFA preservando la información de tokenización y se proveen herramientas interactivas para simular la ejecución del autómata y generar reportes (p.ej., tabla de símbolos, errores léxicos).

---

## Arquitectura y estructura de directorios

La estructura del proyecto se organiza de la siguiente forma:

- **/src**  
  Contiene todos los módulos fuente del proyecto.

  - **/lexicalAnalyzerGenerator**
    - `yalParser.py`: Parser para archivos YAL. Extrae variables y reglas.
    - `readFile.py`: Función para lectura de archivos de entrada.
    - `lexer.py`: Implementación del analizador léxico basado en el DFA.
    - `__init__.py`: Inicialización del paquete.
    - Otros archivos relacionados (p.ej., `token.py`).
  - **/dfaGenerator**
    - **/toPostfix**:
      - `regexToSY.py`: Conversión de expresiones regulares (infix) a notación postfix; tokenización, inserción de operadores de concatenación, manejo de clases y secuencias escapadas.
    - **/toAST**:
      - `syToSyntaxTree.py`: Construcción y visualización del árbol sintáctico (AST) desde la lista de tokens en postfix.
    - **/directConstructionDFA**:
      - `astToDFA.py`: Construcción del DFA a partir del AST utilizando el método followpos.
    - **/minimizeDFA**:
      - `AFDtoMinimizedAFD.py`: Algoritmo para la minimización del DFA, preservando la información de token asociado a estados aceptantes.
    - **/utils**:  
      Herramientas de visualización y simulación del DFA (por ejemplo, `graphAFD.py`, `graphMinimizedAFD.py`, `simulateDFA.py`, `visualizeLexeme.py`).
    - `__init__.py`: Inicialización del paquete.
  - **/symbolTable**
    - `symbolTableGenerator.py`: Generación y manejo de la tabla de símbolos (identificadores y sus líneas de aparición).
    - `__init__.py`
  - **/syntaxChecker**
    - `errorChecker.py`: Reporte y chequeo de errores léxicos y sintácticos.
    - `__init__.py`
  - **/dfaGenerator/regexParsing**
    - `validateRegex.py`: Validación de la estructura y caracteres permitidos en las expresiones regulares.
  - `main.py`: Archivo principal que integra todo el flujo de procesamiento.

- **Archivos YAL**  
  Se incluyen diferentes archivos YAL (por ejemplo, `hard_lex.yal`, `medium_lex.yal`, `easy_lex.yal`) que definen las reglas de tokens y variables imprescindibles para la generación del analizador léxico.
- **Archivos de prueba y ejemplos**  
  Ejemplos de entradas para pruebas (p.ej., `teste1.txt`, `teste.txt`, `test2.py`) y un archivo de salida generado `lexer.txt` que muestra el análisis léxico con header y trailer.

- **Otros**  
  `LICENSE`, `.gitignore`, `console_output.txt` y otros archivos auxiliares.

---

## Componentes principales

### Lexical Analyzer Generator

Implementa la lectura y generación del analizador léxico utilizando los módulos contenidos en `/lexicalAnalyzerGenerator`.

- **yalParser.py**: Extrae la definición de tokens; procesa variables definidas por `let` y reglas definidas en `rule tokens`.
- **readFile.py**: Provee una función robusta para la lectura de archivos en diferentes formatos (txt, py, etc.).
- **lexer.py y token.py**: Implementan la estructura de Tokens y el analizador basado en el DFA construido a partir de las reglas definidas.

### Parser de YAL

El parser interpreta los archivos YAL, permitiendo definir reglas de tokens y variables. El formato YAL permite:

- Definir variables con la palabra clave `let` (p.ej., `let digit = [0-9]`).
- Definir reglas de tokens con la sección `rule tokens` que asigna un nombre de token a cada expresión regular.

### Conversión de Expresión Regular a Postfix

Dentro de `/dfaGenerator/toPostfix`, el módulo `regexToSY.py` se encarga de:

- Tokenizar la expresión regular.
- Insertar de forma explícita operadores de concatenación ('.') donde sea necesario.
- Convertir la notación infix a postfix usando el algoritmo Shunting-yard, teniendo en cuenta precedencia y asociatividad.

### Construcción de Árbol Sintáctico (AST)

El módulo ubicado en `/dfaGenerator/toAST/syToSyntaxTree.py`:

- Toma la lista de tokens en notación postfix y construye el AST.
- Soporta operadores unarios (como Kleene star `*` y `+`) y binarios (concatenación, unión).
- Proporciona una función para visualizar el árbol utilizando Graphviz.

### Construcción y Minimización de DFA

El módulo `/dfaGenerator/directConstructionDFA/astToDFA.py`:

- Calcula para cada nodo del AST los atributos `nullable`, `firstpos` y `lastpos`.
- Genera la tabla `followpos` y, a partir de ella, construye un DFA no minimizado.
- La minimización se realiza en `/dfaGenerator/minimizeDFA/AFDtoMinimizedAFD.py` mediante un algoritmo que respeta los diferentes tokens en estados de aceptación, evitando fusionar estados con etiquetas incompatibles.

### Simulación y Visualización

- **Simulación**:  
  El módulo `/dfaGenerator/utils/simulateDFA.py` permite al usuario ingresar cadenas de entrada para verificar si son aceptadas por el DFA minimizado, mostrando el proceso paso a paso (derivación).
- **Visualización**:  
  Los módulos `graphAFD.py` y `graphMinimizedAFD.py` generan diagramas (PNG) del DFA, mostrando estados, transiciones y estados de aceptación. Además, `visualizeLexeme.py` ayuda a visualizar lexemas especiales (espacios, tabulaciones).

### Generación de Tabla de Símbolos y Chequeo de Errores

- **Symbol Table**:  
  El módulo `/symbolTable/symbolTableGenerator.py` gestiona la tabla de símbolos que almacena identificadores y sus líneas de aparición.
- **Error Checker**:  
  El módulo `/syntaxChecker/errorChecker.py` reporta errores léxicos en tiempo de ejecución, proporcionando información detallada sobre la ubicación del error.

### Validación de Expresiones Regulares

El módulo `/dfaGenerator/regexParsing/validateRegex.py` se encarga de asegurar que las expresiones regulares estén correctamente formadas, comprobando que todos los caracteres sean válidos y que los paréntesis y corchetes estén balanceados.

---

## Definiciones de Tokens y Archivos YAL

Los archivos YAL definen el léxico para distintos lenguajes o configuraciones. Por ejemplo:

- **hard_lex.yal**: Contiene definiciones completas de tokens para operadores, identificadores, números, espacios en blanco y comentarios, entre otros.
- **medium_lex.yal y easy_lex.yal**: Versiones simplificadas o alternativas para pruebas.
- Cada regla se conforma mediante una expresión regular a la que se asocia un token (p.ej., `("if" $ { return IF })`).

---

## Flujo de operación

1. **Definición y Parsing de Reglas**:  
   Se lee el archivo YAL mediante `yalParser.py`, extrayendo variables (`let`) y reglas (`rule tokens`). Los bloques de header y trailer se procesan para integrarse en la salida final.

2. **Generación de la Expresión Regular Combinada**:  
   Las reglas extraídas se combinan en una única expresión regular. La función `combine_rules` se encarga de procesar literales y aplicar un preprocesamiento adecuado (eliminación de espacios fuera de literales y clases).

3. **Tokenización y Conversión a Postfix**:  
   La expresión combinada se tokeniza y se inserta el operador de concatenación según sea necesario. Posteriormente, se convierte a notación postfix.

4. **Construcción del AST**:  
   A partir de la notación postfix, se construye un árbol sintáctico del regular expression. Se utiliza el AST tanto para la posterior construcción del DFA como para su visualización.

5. **Construcción del DFA Directo**:  
   Utilizando el método followpos, se asignan posiciones y se calcula la función followpos en el AST para construir el DFA no minimizado.

6. **Minimización del DFA**:  
   El DFA se minimiza preservando las etiquetas de token en los estados de aceptación (manejando prioridades de tokens).

7. **Simulación y Análisis**:  
   Se procesa un archivo de entrada (por ejemplo, `teste1.txt`), se realiza el análisis léxico, y se generan reportes visuales y la tabla de símbolos.

8. **Salida y Visualización**:  
   Se generan archivos de salida como `lexer.txt`, se visualizan autómatas y se imprime la derivación y la tabla de símbolos en la consola y en archivos.

---

## Instrucciones de uso

1. **Preparación**:

   - Asegúrese de tener instaladas las dependencias necesarias (ver sección de dependencias).
   - Configure los archivos YAL (por ejemplo, `hard_lex.yal`) con las reglas deseadas.

2. **Ejecución**:

   - Ejecute `main.py` desde la línea de comandos. El script guiará a través de:
     - La lectura de definiciones de tokens.
     - La construcción y visualización del AST y del DFA.
     - La minimización del autómata.
     - La simulación interactiva del analizador léxico mediante la entrada de cadenas.

3. **Salida**:
   - Los resultados del análisis léxico se imprimirán en consola y se escribirán en archivos (p.ej., `lexer.txt`, `console_output.txt`).
   - Las visualizaciones generadas (como `syntax_tree.png`, `graphAFD.png`, `graphMinimizedAFD.png`) se abrirán automáticamente (según el sistema operativo).

---

## Dependencias

- **Python 3.12** (u otra versión compatible)
- **Graphviz**: Biblioteca para la generación de gráficos de autómatas.
- **Módulos estándar**: `re`, `sys`, `codecs`, `collections`, `textwrap`, `os`, `platform`, entre otros.
- Otros módulos instalables mediante pip, si es necesario.

---

## Licencia

El proyecto se distribuye bajo la Licencia MIT. Consulte el archivo `LICENSE` para más detalles.

---

## Notas adicionales

- El proyecto está orientado a ser modular y extensible, permitiendo la integración de nuevos lenguajes o reglas.
- La estructura del código incluye numerosos puntos de extensión, como la función de preprocesamiento de expresiones regulares, análisis de errores y generación de tablas de símbolos.
- Se ha prestado especial atención a la preservación de la información de token (por ejemplo, en la propagación de atributos en el AST), lo que permite que el DFA minimizado no pierda la asociación con los tokens originales.
- El proceso completo desde la definición hasta la simulación se realiza de manera integrada en el archivo `main.py`, proporcionando una interfaz para pruebas y análisis.
