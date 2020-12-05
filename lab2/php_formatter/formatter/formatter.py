from ..lexer import Lexer
from ..lexer.token_classes import Token, WrongToken
from ..lexer.dict_token_types import Tokens


class PHPFormatter:

    def __init__(self):
        self._token = []
        self._invalid_token = []
        self._symbol_table = []
        self._lexer_error_list = []

        self._state_pos = 0
        self._all_tokens = []

    def process_php_file(self, path_to_file):
        lexer = Lexer()
        lexer.process_php_file(path_to_file)
        self._all_tokens = lexer.get_tokens_list()
        self._symbol_table = lexer.get_symbol_table()
        self._lexer_error_list = lexer.get_error_tokens_list()

        while self._state_pos < len(self._all_tokens):
            self._parse_next_token()

    def _parse_next_token(self):
        current_token = self._all_tokens[self._state_pos]

        if current_token.type == Tokens.Variable:
            self._handle_variable()
            return

        self._token.append(self._all_tokens[self._state_pos])
        self._state_pos += 1

    def _handle_variable(self):
        current_token = self._all_tokens[self._state_pos]
        variable = self._symbol_table[current_token.index]
        new_variable = '$'
        for i in range(1, len(variable)):
            if (variable[i]).isupper() and i != 1:
                new_variable += '_'
            new_variable += (variable[i]).lower()

        new_token = Token(
            token_type=Tokens.Variable,
            row=current_token.row,
            column=current_token.column,
            index=len(self._symbol_table)
        )

        self._token.append(new_token)
        self._symbol_table.append(new_variable)
        self._invalid_token.append(WrongToken(
            token=new_token,
            message="Not snake_case"
        ))
        self._state_pos += 1

    def print_all(self):
        for tok in self._token:
            if tok.type != Tokens.Space and tok.type != Tokens.Tab:
                print(tok, end=' ')
                if tok.index is not None:
                    print('|' + self._symbol_table[tok.index] + '|')
                else:
                    print('')
            if tok.type == Tokens.Enter:
                print('')
        print('------------------------')
        for tok in self._invalid_token:
            print(tok, end=' ')
            if tok.token.index is not None:
                print('|' + self._symbol_table[tok.token.index] + '|')
            else:
                print('')

        print('------------------------')
        for i in range(len(self._symbol_table)):
            print(str(i) + ') ', '|' + self._symbol_table[i] + '|')

    def get_tokens_list(self):
        return self._token

    def get_symbol_table(self):
        return self._symbol_table
