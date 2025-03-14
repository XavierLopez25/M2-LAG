from lexicalAnalyzerGenerator.yalParser import parse_yalex

def main(): 

    yalex_file = "lexer.yal"

    rules = parse_yalex(yalex_file)

    print("\nReglas extraídas:")
    for regex, token in rules.items():
        print(f"  {regex} -> {token}")


if __name__ == "__main__":
    main()