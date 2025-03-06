from lexicalAnalyzerGenerator.token import Token

class Lexer:
    def __init__(self, dfa, accepting_states):
        self.dfa = dfa
        self.accepting_states = accepting_states

    def analyze(self, text: str):
        tokens = []
        state = self.dfa['initial']
        lexeme = ""
        line_number = 1

        for char in text:
            if char == '\n':
                line_number += 1

            next_state = self.dfa['transitions'].get((state, char))
            if next_state is None:
                if state in self.accepting_states:
                    token_type = self.accepting_states[state]
                    tokens.append(Token(token_type, lexeme, line_number))
                    lexeme = ""
                    state = self.dfa['initial']
                    if char.strip():  # Reprocesar char
                        next_state = self.dfa['transitions'].get((state, char))
                        if next_state is None:
                            raise ValueError(f"Error léxico: '{char}' en línea {line_number}")
                        lexeme += char
                        state = next_state
                else:
                    raise ValueError(f"Error léxico: '{char}' en línea {line_number}")
            else:
                lexeme += char
                state = next_state

        if lexeme and state in self.accepting_states:
            tokens.append(Token(self.accepting_states[state], lexeme, line_number))
        elif lexeme:
            raise ValueError(f"Error léxico al final: '{lexeme}'")

        return tokens
