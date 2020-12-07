import sys
import os
import logging
from os.path import isfile, join, splitext

from ..lexer import Lexer
from ..lexer.token_classes import Token, WrongToken
from ..lexer.dict_token_types import Tokens
from ..lexer._char_checks import is_word, is_whitespace

from ._cases_creation import *


class PHPFormatter:
    formatted_files = []
    all_changes = []
    old_file_names = []
    new_file_names = []

    def __init__(self):
        self.path_to_file = ''
        self.file_name = ''
        self.new_file_name = ''

        self._token = []
        self._invalid_token = []
        self._includes = []
        self._symbol_table = []
        self._lexer_error_list = []

        self._state_pos = 0
        self._all_tokens = []

    def process_php_file(self, path_to_file, file_name):
        file_path = join(path_to_file, file_name)
        self.path_to_file = path_to_file
        self.file_name = file_name
        self.new_file_name = file_name_case(file_name)

        lexer = Lexer()
        lexer.process_php_file(file_path)
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
        if current_token.spec == 'define':
            self._handle_constants()
            return
        if current_token.spec == 'include':
            self._handle_include()
            return

        self._token.append(self._all_tokens[self._state_pos])
        self._state_pos += 1

    def _is_whitespace_token(self, token):
        return token == Tokens.Enter or token == Tokens.Space or token == Tokens.Tab

    def _add_new_token(self, current_token, new_value, error_message, format_type):
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
            message=error_message,
            format_type=format_type,
            new_value=new_value,
            old_value=self._symbol_table[current_token.index]
        ))

    def _handle_variable(self):
        normal_end = True
        next_token = self._next_non_whitespace(self._state_pos + 1)
        while next_token is not None and next_token.spec == '->':
            current_token = self._all_tokens[self._state_pos]
            variable = self._symbol_table[current_token.index]
            if current_token.type == Tokens.Variable:
                new_variable = '$' + snake_case(variable[1:])
            else:
                new_variable = snake_case(variable)

            if new_variable != variable:
                self._add_new_token(current_token, new_variable, "Incorrect snake case in variable name", "var")
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

            next_token = self._next_non_whitespace(self._state_pos + 1)

        if not normal_end or next_token is not None and next_token.spec == '(' and\
                self._all_tokens[self._state_pos].type != Tokens.Variable:
            return
        current_token = self._all_tokens[self._state_pos]
        variable = self._symbol_table[current_token.index]
        if current_token.type == Tokens.Variable:
            new_variable = '$' + snake_case(variable[1:])
        else:
            new_variable = snake_case(variable)

        if new_variable != variable:
            self._add_new_token(current_token, new_variable, "Incorrect snake case in variable name", "var")
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
            self._add_new_token(current_token, new_func_name, "Incorrect snake case in func name", "func")
        else:
            self._token.append(current_token)
        self._state_pos += 1

    def _handle_constants(self):
        next_token = self._next_non_whitespace(self._state_pos + 1)
        self._token.append(self._all_tokens[self._state_pos])
        self._state_pos += 1

        if next_token.spec != '(':
            return

        while self._state_pos < len(self._all_tokens) and \
                self._is_whitespace_token(self._all_tokens[self._state_pos].type):
            self._token.append(self._all_tokens[self._state_pos])
            self._state_pos += 1

        self._token.append(self._all_tokens[self._state_pos])
        self._state_pos += 1

        while self._state_pos < len(self._all_tokens) and \
                self._is_whitespace_token(self._all_tokens[self._state_pos].type):
            self._token.append(self._all_tokens[self._state_pos])
            self._state_pos += 1

        current_token = self._all_tokens[self._state_pos]
        if current_token.type != Tokens.StringLiteral:
            self._token.append(current_token)
            self._state_pos += 1
            return

        const_name = self._symbol_table[current_token.index]
        new_const = screaming_snake_case(const_name)
        if const_name != new_const:
            self._add_new_token(current_token, new_const,
                                "Incorrect screaming snake case in const name", "const")
        else:
            self._token.append(current_token)
        self._state_pos += 1

    def _default_info_of_class_comment(self, s_indent):
        next_token = self._next_non_whitespace(self._state_pos + 1)
        if next_token.type != Tokens.Identifier:
            class_name = '<NoNameClass>'
        else:
            class_name = camel_case(self._symbol_table[next_token.index])
        empty_line = s_indent + ' *'
        comment = '/**\n'
        comment += empty_line + ' ' + class_name + '\n'
        comment += empty_line + '\n'
        comment += empty_line + ' @author Firstname Lastname\n'
        comment += empty_line + ' @global object_type object_name\n'
        comment += empty_line + ' @package package_name\n'
        comment += empty_line + '/'
        return comment

    def _create_class_comment(self):
        pos = self._state_pos - 1
        indent = []
        while pos >= 0 and self._is_whitespace_token(self._all_tokens[pos].type) and \
                self._all_tokens[pos].type != Tokens.Enter:
            indent.append(self._all_tokens[pos])
            pos -= 1
        if pos >= 0 and self._all_tokens[pos].type != Tokens.Enter:
            indent = []
            pos = self._state_pos - 1
            while pos >= 0 and self._is_whitespace_token(self._all_tokens[pos].type):
                self._token.pop()
                pos -= 1
            self._token.append(Token(
                token_type=Tokens.Enter,
                row=self._all_tokens[pos].row,
                column=self._all_tokens[pos].column + 1
            ))
        comment = Token(token_type=Tokens.MultiLineComment,
                        row=self._all_tokens[self._state_pos].row,
                        column=self._all_tokens[self._state_pos].column,
                        index=len(self._symbol_table))

        string_indent = ''
        for token in indent:
            string_indent += token.type.value

        comment_value = self._default_info_of_class_comment(string_indent)
        self._symbol_table.append(comment_value)
        self._token.append(comment)
        self._token.append(Token(
            token_type=Tokens.Enter,
            row=self._all_tokens[pos].row,
            column=self._all_tokens[pos].column + 1
        ))
        self._token.extend(indent)

    def _parse_class_comment(self, comment_value, s_indent):
        new_comment = '/**\n'

        def _parse_next_char(pos, answer, stage):
            while comment_value[pos] == ' ' or comment_value[pos] == '\t':
                pos += 1
            to_add = s_indent + ' *'
            if comment_value[pos] == '*':
                pos += 1

            while comment_value[pos] == ' ' or comment_value[pos] == '\t':
                pos += 1

            if stage == 1:
                to_add += ' '
                next_token = self._next_non_whitespace(self._state_pos + 1)
                if next_token.type != Tokens.Identifier:
                    class_name = '<NoNameClass>'
                else:
                    class_name = self._symbol_table[next_token.index]
                word = ''
                prev_pos = pos
                while not is_whitespace(comment_value[pos]) and pos < len(comment_value) - 2:
                    word += comment_value[pos]
                    pos += 1
                to_add += camel_case(class_name)
                if word == '@author' or word == '@global' or word == '@package' or pos >= len(comment_value) - 2:
                    to_add += '\n'
                    pos -= len(word)
                    pos -= 1
                elif prev_pos == pos:
                    to_add = ''
                    stage -= 1
                else:
                    if word != class_name:
                        pos = prev_pos
                        to_add += ' '
                    while comment_value[pos] != '\n' and pos < len(comment_value) - 2:
                        to_add += comment_value[pos]
                        pos += 1
                    to_add += '\n'
                pos += 1
            elif stage == 2:
                word = ''
                prev_pos = pos
                while not is_whitespace(comment_value[pos]) and pos < len(comment_value) - 2:
                    word += comment_value[pos]
                    pos += 1
                if word == '@author' or word == '@global' or word == '@package' or prev_pos == pos \
                        or pos >= len(comment_value) - 2:
                    to_add += '\n'
                    pos -= len(word)
                    pos -= 1
                else:
                    to_add += ' '

                    pos = prev_pos
                    while comment_value[pos] != '\n' and pos < len(comment_value) - 2:
                        to_add += comment_value[pos]
                        pos += 1

                    stage -= 1
                    to_add += '\n'
                pos += 1
            elif stage == 3:
                word = ''
                prev_pos = pos
                while not is_whitespace(comment_value[pos]) and pos < len(comment_value) - 2:
                    word += comment_value[pos]
                    pos += 1
                if word == '@global' or word == '@package' or pos >= len(comment_value) - 2:
                    to_add += ' @author Firstname Lastname\n'
                    pos -= len(word)
                    pos -= 1
                elif prev_pos == pos:
                    to_add = ''
                    stage -= 1
                else:
                    to_add += ' @author'
                    if word != '@author':
                        pos = prev_pos
                        to_add += ' '
                    while comment_value[pos] != '\n' and pos < len(comment_value) - 2:
                        to_add += comment_value[pos]
                        pos += 1

                    to_add += '\n'

                pos += 1
            elif stage == 4:
                word = ''
                prev_pos = pos
                while not is_whitespace(comment_value[pos]) and pos < len(comment_value) - 2:
                    word += comment_value[pos]
                    pos += 1
                if word == '@package' or pos >= len(comment_value) - 2:
                    to_add += ' @global object_type object_name\n'
                    pos -= len(word)
                    pos -= 1
                elif prev_pos == pos:
                    to_add = ''
                    stage -= 1
                else:
                    to_add += ' @global'
                    if word != '@global':
                        pos = prev_pos
                        to_add += ' '
                    while comment_value[pos] != '\n' and pos < len(comment_value) - 2:
                        to_add += comment_value[pos]
                        pos += 1
                    to_add += '\n'

                pos += 1
            elif stage == 5:
                word = ''
                prev_pos = pos
                while not is_whitespace(comment_value[pos]) and pos < len(comment_value) - 2:
                    word += comment_value[pos]
                    pos += 1
                if pos >= len(comment_value) - 2:
                    to_add += ' @package package_name\n'
                    pos -= 1
                elif prev_pos == pos:
                    to_add = ''
                    stage -= 1
                else:
                    to_add += ' @package'
                    if word != '@package':
                        pos = prev_pos
                        to_add += ' '
                    while comment_value[pos] != '\n' and pos < len(comment_value) - 2:
                        to_add += comment_value[pos]
                        pos += 1

                    to_add += '\n'
                pos += 1
            else:
                to_add += '/'
                pos = len(comment_value)
            stage += 1
            return pos, answer + to_add, stage

        state_pos = 2
        stage_n = 1
        if comment_value[state_pos] == '*' and comment_value[state_pos + 1] == '\n':
            state_pos += 2
        while state_pos < len(comment_value):
            state_pos, new_comment, stage_n = _parse_next_char(state_pos, new_comment, stage_n)

        return new_comment

    def _check_class_comment(self):
        pos = self._state_pos - 1
        indent = []
        while pos >= 0 and self._is_whitespace_token(self._all_tokens[pos].type) and \
                self._all_tokens[pos].type != Tokens.Enter:
            indent.append(self._all_tokens[pos])
            pos -= 1

        if self._all_tokens[pos].type != Tokens.Enter:
            indent = []
        if pos >= 0 and self._is_whitespace_token(self._all_tokens[pos].type):
            pos -= 1

        comment_pos = pos
        pos -= 1
        new_indent = []
        while pos >= 0 and self._is_whitespace_token(self._all_tokens[pos].type) and \
                self._all_tokens[pos].type != Tokens.Enter:
            new_indent.append(self._all_tokens[pos])
            pos -= 1
        if self._all_tokens[pos].type != Tokens.Enter:
            new_indent = []
        was_here = False
        if pos >= 0 and self._is_whitespace_token(self._all_tokens[pos].type):
            pos -= 1
            was_here = True
        if was_here:
            self._token.append(Token(
                token_type=Tokens.Enter,
                row=self._all_tokens[pos].row,
                column=self._all_tokens[pos].column + 1
            ))
        print(new_indent)
        print(indent)
        if len(new_indent) > len(indent):
            indent = new_indent

        for i in range(pos, self._state_pos-1):
            self._token.pop()

        self._token.extend(indent)
        self._token.append(self._all_tokens[comment_pos])

        string_indent = ''
        for token in indent:
            string_indent += token.type.value

        pos = self._state_pos - 1
        while pos >= 0 and self._is_whitespace_token(self._all_tokens[pos].type):
            pos -= 1

        comment = self._all_tokens[pos]
        comment_value = self._symbol_table[comment.index]
        parsed_class_comment = self._parse_class_comment(comment_value, string_indent)
        if parsed_class_comment != comment_value:
            self._symbol_table[comment.index] = parsed_class_comment
            self._invalid_token.append(WrongToken(
                token=comment,
                format_type="comment",
                old_value=comment_value,
                new_value=parsed_class_comment
            ))

        self._token.append(Token(
            token_type=Tokens.Enter,
            row=self._all_tokens[pos].row,
            column=self._all_tokens[pos].column + 1
        ))
        self._token.extend(indent)

    def _handle_class(self):
        prev_token = self._prev_non_whitespace(self._state_pos - 1)
        if prev_token is None or prev_token.type != Tokens.MultiLineComment:
            self._create_class_comment()
        else:
            self._check_class_comment()

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
            self._add_new_token(current_token, new_class_name, "Incorrect snake case in class name", "class")
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
                self._add_new_token(current_token, new_namespace, "Incorrect snake case in namespace name", "namespace")
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
            self._add_new_token(current_token, new_namespace, "Incorrect snake case in namespace name", "namespace")
        else:
            self._token.append(current_token)
        self._state_pos += 1

    def _handle_include(self):
        next_token = self._next_non_whitespace(self._state_pos + 1)
        self._token.append(self._all_tokens[self._state_pos])
        self._state_pos += 1

        if not next_token.type == Tokens.StringLiteral and next_token == Tokens.StartTemplateString:
            return

        while self._state_pos < len(self._all_tokens) and \
                self._is_whitespace_token(self._all_tokens[self._state_pos].type):
            self._token.append(self._all_tokens[self._state_pos])
            self._state_pos += 1

        current_token = self._all_tokens[self._state_pos]
        if current_token.type == Tokens.StringLiteral:
            self._includes.append((current_token, len(self._token)))
            self._token.append(current_token)
            self._state_pos += 1
        else:
            pos = self._state_pos
            while pos < len(self._all_tokens) and self._all_tokens[pos].type != Tokens.EndTemplateString:
                pos += 1
            if pos - self._state_pos != 2:
                self._token.append(self._all_tokens[self._state_pos])
                self._state_pos += 1
                return

            self._includes.append((self._all_tokens[self._state_pos + 1], len(self._token) + 1))
            while self._state_pos < len(self._all_tokens) and \
                    self._all_tokens[self._state_pos].type != Tokens.EndTemplateString:
                self._token.append(self._all_tokens[self._state_pos])
                self._state_pos += 1

            self._token.append(self._all_tokens[self._state_pos])
            self._state_pos += 1

    def _next_non_whitespace(self, pos):
        while pos < len(self._all_tokens) and self._is_whitespace_token(self._all_tokens[pos].type):
            pos += 1
        if pos >= len(self._all_tokens):
            return Token().set_invalid()
        else:
            return self._all_tokens[pos]

    def _prev_non_whitespace(self, pos):
        while pos >= 0 and self._is_whitespace_token(self._all_tokens[pos].type):
            pos -= 1
        if pos < 0:
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

        print('------------------------')
        print(len(self._includes))
        for tok in self._includes:
            if tok[0].index is not None:
                print('|' + self._symbol_table[tok[0].index] + '|')
            else:
                print('')

    def get_tokens_list(self):
        return self._token

    def get_symbol_table(self):
        return self._symbol_table

    def get_includes(self):
        return self._includes

    def get_invalid_tokens_list(self):
        return self._invalid_token

    def save_to_file(self):
        os.remove(join(self.path_to_file, self.file_name))

        with open(join(self.path_to_file, self.new_file_name), 'w') as f:
            original_stdout = sys.stdout
            sys.stdout = f
            for token in self._token:
                if token.type == Tokens.StartTemplateString or token.type == Tokens.EndTemplateString:
                    print('"', end='')
                elif token.index is not None:
                    print(self._symbol_table[token.index], end='')
                elif token.spec is not None:
                    print(token.spec, end='')
                else:
                    print(token.type.value, end='')
            sys.stdout = original_stdout

    def save_ver_log(self):
        if self.file_name != self.new_file_name:
            logging.info('----------- ' + join(self.path_to_file, self.file_name) +
                         ' need to rename to ' + join(self.path_to_file, self.new_file_name) + ' -------------')
        else:
            logging.info('----------- ' + join(self.path_to_file, self.file_name) + ' -------------')
        logging.info('Verification errors:')
        i = 0
        for tok in self._invalid_token:
            if tok.token.index is not None:
                logging.info('Id: ' + str(i) + ') ' + join(self.path_to_file, self.file_name) + ': ' +
                             str(tok.token.row) + '|' + str(tok.token.column) + ' - Error code ( ' +
                             str(tok.old_value) + ' ): ' + str(tok.error_message))
            i += 1
        logging.info('errors end\n')

    def save_fix_log(self):
        if self.file_name != self.new_file_name:
            logging.info('----------- ' + join(self.path_to_file, self.file_name) +
                         ' renamed to ' + join(self.path_to_file, self.new_file_name) + ' -------------')
        else:
            logging.info('----------- ' + join(self.path_to_file, self.file_name) + ' -------------')
        logging.info('Format errors:')
        i = 0
        for tok in self._invalid_token:
            if tok.token.index is not None:
                logging.info('Id: ' + str(i) + ') ' + join(self.path_to_file, self.new_file_name) + ': ' +
                             str(tok.token.row) + '|' + str(tok.token.column) + ' Change from ' +
                             str(tok.old_value) + ' to ' + str(tok.new_value))

            i += 1
        logging.info('errors end\n')

    def setup_all_changes(self):
        for token in self._token:
            if token.type == Tokens.Identifier:
                value = self._symbol_table[token.index]
                for change in PHPFormatter.all_changes:
                    if change.format_type == 'const' and change.old_value[1:-1] == value:
                        self._symbol_table[token.index] = change.new_value[1:-1]
                        self._invalid_token.append(WrongToken(
                            token=token,
                            message=change.error_message,
                            format_type=change.format_type,
                            old_value=change.old_value[1:-1],
                            new_value=change.new_value[1:-1]
                        ))
                        break
                    if change.format_type != 'var' and change.old_value == value:
                        self._symbol_table[token.index] = change.new_value
                        self._invalid_token.append(WrongToken(
                            token=token,
                            message=change.error_message,
                            format_type=change.format_type,
                            old_value=change.old_value,
                            new_value=change.new_value
                        ))
                        break
