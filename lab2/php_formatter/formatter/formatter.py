from ..lexer import Lexer
from ..lexer.token_classes import Token, WrongToken
from ..lexer.dict_token_types import Tokens

from ._cases_creation import *


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
        if current_token.spec == 'function':
            self._handle_function()
            return
        if current_token.spec == 'class':
            self._handle_class()
            return
        if current_token.spec == 'namespace':
            self._handle_namespace()
            return

        self._token.append(self._all_tokens[self._state_pos])
        self._state_pos += 1

    def _is_whitespace_token(self, token):
        return token == Tokens.Enter or token == Tokens.Space or token == Tokens.Tab

    def _add_new_token(self, current_token, new_value, error_message):
        new_token = Token(
            token_type=current_token.type,
            row=current_token.row,
            column=current_token.column,
            index=len(self._symbol_table)
        )

        self._token.append(new_token)
        self._symbol_table.append(new_value)
        self._invalid_token.append(WrongToken(
            token=current_token,
            message=error_message
        ))

    def _handle_variable(self):
        normal_end = True
        while self._next_non_whitespace(self._state_pos + 1).spec == '->':
            current_token = self._all_tokens[self._state_pos]
            variable = self._symbol_table[current_token.index]
            if current_token.type == Tokens.Variable:
                new_variable_lower = '$' + snake_case(variable[1:])
                new_variable_upper = '$' + screaming_snake_case(variable[1:])
            else:
                new_variable_lower = snake_case(variable)
                new_variable_upper = screaming_snake_case(variable)
            if new_variable_upper == variable:
                self._token.append(current_token)
            elif new_variable_lower != variable:
                self._add_new_token(current_token, new_variable_lower, "Incorrect snake case in variable name")
            else:
                self._token.append(current_token)
            self._state_pos += 1
            while self._state_pos < len(self._all_tokens) and\
                    self._is_whitespace_token(self._all_tokens[self._state_pos].type):
                self._token.append(self._all_tokens[self._state_pos])
                self._state_pos += 1

            if self._state_pos >= len(self._all_tokens):
                return

            self._token.append(self._all_tokens[self._state_pos])
            self._state_pos += 1
            next_token = self._next_non_whitespace(self._state_pos)
            if next_token.type != Tokens.Identifier:
                normal_end = False
                break
            while self._state_pos < len(self._all_tokens) and\
                    self._is_whitespace_token(self._all_tokens[self._state_pos].type):
                self._token.append(self._all_tokens[self._state_pos])
                self._state_pos += 1

        if not normal_end or self._next_non_whitespace(self._state_pos + 1).spec == '(' and\
                self._all_tokens[self._state_pos].type != Tokens.Variable:
            return
        current_token = self._all_tokens[self._state_pos]
        variable = self._symbol_table[current_token.index]
        if current_token.type == Tokens.Variable:
            new_variable_lower = '$' + snake_case(variable[1:])
            new_variable_upper = '$' + screaming_snake_case(variable[1:])
        else:
            new_variable_lower = snake_case(variable)
            new_variable_upper = screaming_snake_case(variable)
        if new_variable_upper == variable:
            self._token.append(current_token)
        elif new_variable_lower != variable:
            self._add_new_token(current_token, new_variable_lower, "Incorrect snake case in variable name")
        else:
            self._token.append(current_token)
        self._state_pos += 1

    def _handle_function(self):
        next_token = self._next_non_whitespace(self._state_pos + 1)
        self._token.append(self._all_tokens[self._state_pos])
        self._state_pos += 1

        if next_token.type != Tokens.Identifier:
            return

        while self._state_pos < len(self._all_tokens) and \
                self._is_whitespace_token(self._all_tokens[self._state_pos].type):
            self._token.append(self._all_tokens[self._state_pos])
            self._state_pos += 1

        current_token = self._all_tokens[self._state_pos]
        func_name = self._symbol_table[current_token.index]
        new_func_name = snake_case(func_name)
        if func_name != new_func_name:
            self._add_new_token(current_token, new_func_name, "Incorrect snake case in func name")
        else:
            self._token.append(current_token)
        self._state_pos += 1

    def _handle_class(self):
        next_token = self._next_non_whitespace(self._state_pos + 1)
        self._token.append(self._all_tokens[self._state_pos])
        self._state_pos += 1

        if next_token.type != Tokens.Identifier:
            return

        while self._state_pos < len(self._all_tokens) and \
                self._is_whitespace_token(self._all_tokens[self._state_pos].type):
            self._token.append(self._all_tokens[self._state_pos])
            self._state_pos += 1

        current_token = self._all_tokens[self._state_pos]
        class_name = self._symbol_table[current_token.index]
        new_class_name = camel_case(class_name)
        if class_name != new_class_name:
            self._add_new_token(current_token, new_class_name, "Incorrect snake case in class name")
        else:
            self._token.append(current_token)
        self._state_pos += 1

    def _handle_namespace(self):
        next_token = self._next_non_whitespace(self._state_pos + 1)
        self._token.append(self._all_tokens[self._state_pos])
        self._state_pos += 1

        if next_token.type != Tokens.Identifier:
            return
        while self._state_pos < len(self._all_tokens) and \
                self._is_whitespace_token(self._all_tokens[self._state_pos].type):
            self._token.append(self._all_tokens[self._state_pos])
            self._state_pos += 1

        normal_end = True

        while self._next_non_whitespace(self._state_pos + 1).spec == '\\':
            current_token = self._all_tokens[self._state_pos]
            namespace = self._symbol_table[current_token.index]
            new_namespace = camel_case(namespace)
            if new_namespace == namespace:
                self._token.append(current_token)
            elif new_namespace != namespace:
                self._add_new_token(current_token, new_namespace, "Incorrect snake case in namespace name")
            else:
                self._token.append(current_token)
            self._state_pos += 1
            while self._state_pos < len(self._all_tokens) and \
                    self._is_whitespace_token(self._all_tokens[self._state_pos].type):
                self._token.append(self._all_tokens[self._state_pos])
                self._state_pos += 1

            if self._state_pos >= len(self._all_tokens):
                return

            self._token.append(self._all_tokens[self._state_pos])
            self._state_pos += 1
            next_token = self._next_non_whitespace(self._state_pos)
            if next_token.type != Tokens.Identifier:
                normal_end = False
                break
            while self._state_pos < len(self._all_tokens) and \
                    self._is_whitespace_token(self._all_tokens[self._state_pos].type):
                self._token.append(self._all_tokens[self._state_pos])
                self._state_pos += 1

        if not normal_end or self._state_pos >= len(self._all_tokens):
            return
        current_token = self._all_tokens[self._state_pos]
        namespace = self._symbol_table[current_token.index]
        new_namespace = camel_case(namespace)
        if new_namespace != namespace:
            self._add_new_token(current_token, new_namespace, "Incorrect snake case in namespace name")
        else:
            self._token.append(current_token)
        self._state_pos += 1

    def _next_non_whitespace(self, pos):
        while pos < len(self._all_tokens) and self._is_whitespace_token(self._all_tokens[pos].type):
            pos += 1
        if pos >= len(self._all_tokens):
            return Token().set_invalid()
        else:
            return self._all_tokens[pos]

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
