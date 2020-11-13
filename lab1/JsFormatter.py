import json
import sys
from enum import Enum

from Lexer import Lexer
from DictTokenTypes import Tokens
from TokenClasses import Token, WrongToken
from CharChecks import *
from TokenChecks import *


class ActionType(Enum):
    If = 1
    While = 2,
    For = 3
    Func = 4


ERROR_SIZE = "Wrong number of whitespaces"
ERROR_WRONG_WHITESPACE = "Wrong whitespace"
ERROR_ORDER = "Wrong order of whitespaces"
RULE_BLANK_MAX = ". Rule: Blank Lines Keep Maximum Blank Lines"


class _CurrentState:
    all_tokens = []

    def __init__(self):
        self.pos = 0
        self.row_offset = 0
        self.column_offset = 0
        self.indent = 0
        self.continuous_indent = 0
        self.empty_line_counter = 0
        self.is_start = True


class JsFormatter:

    def __init__(self):
        self._token = []
        self._symbol_table = []
        self._invalid_token = []
        self._lexer_error_list = []
        self._config = []

    def set_up_config(self, path_to_config):
        with open(path_to_config) as f:
            self._config = json.load(f)

    def process_js_file(self, path_to_file):
        lexer = Lexer()
        lexer.process_js_file(path_to_file)
        _CurrentState.all_tokens = lexer.get_tokens_list()
        self._lexer_error_list = lexer.get_error_tokens_list()
        self._symbol_table = lexer.get_symbol_table()
        state = _CurrentState()

        while state.pos < len(state.all_tokens):
            self._parse_next_token(state)

    def print_all_tokens(self):
        with open('new_file.js', 'w') as f:
            original_stdout = sys.stdout
            sys.stdout = f
            for token in self._token:
                if token.type == Tokens.StartTemplateString or token.type == Tokens.EndTemplateString:
                    print('`', end='')
                elif token.index is not None:
                    print(self._symbol_table[token.index], end='')
                elif token.spec is not None:
                    print(token.spec, end='')
                else:
                    print(token.type.value, end='')
            sys.stdout = original_stdout

    def print_all(self):
        print('------------------------all tokens------------------------')
        for tok in self._token:
            if tok.type != Tokens.Space and tok.type != Tokens.Tab:
                print(tok, end=' ')
                if tok.index is not None:
                    print(str(tok.index) + ') |' + self._symbol_table[tok.index] + '|')
                else:
                    print('')
            if tok.type == Tokens.Enter:
                print('')
        print('------------------------error syntax------------------------')
        for tok in self._invalid_token:
            print(tok, end=' ')
            if tok.token.index is not None:
                print('|| Token value: ' + str(tok.token.index) + ') |' + self._symbol_table[tok.token.index] + '|')
            else:
                print('')

        print('------------------------lexer error------------------------')
        for tok in self._lexer_error_list:
            print(tok, end=' ')
            if tok.token.index is not None:
                print('|| Token value: ' + str(tok.token.index) + ') |' + self._symbol_table[tok.token.index] + '|')
            else:
                print('')

        print('------------------------symbol table------------------------')
        for i in range(len(self._symbol_table)):
            print(str(i) + ') ', '|' + self._symbol_table[i] + '|')

    def _parse_next_token(self, state):
        current_token = state.all_tokens[state.pos]
        '''
        if current_token.type == Tokens.Space or current_token.type == Tokens.Tab or current_token.type == Tokens.Enter:
            self._handle_first_whitespaces(state)
            return
        
        if current_token.type == Tokens.Identifier:
            self._handle_identifiers(state)
            return
        

        if state.is_start:
            state.is_start = False
        '''

        state.is_start = False
        if current_token.type == Tokens.Keyword:
            self._handle_keywords(state)
            return

        if current_token.type == Tokens.Enter:
            state.is_start = True

        self._token.append(state.all_tokens[state.pos])
        state.pos += 1

    '''
    def _handle_identifiers(self, state):
        start_pos = state.pos
        next_pos = start_pos + 1
        while next_pos < len(state.all_tokens):
            if is_whitespace(state.all_tokens[next_pos].type.value):
                next_pos += 1
        if next_pos < len(state.all_tokens):
            current_token = state.all_tokens
    '''

    def _handle_keywords(self, state):
        current_token = state.all_tokens[state.pos]

        if current_token.spec == 'function':
            self._handle_function_creation(state)
        else:
            current_token = state.all_tokens[state.pos]
            self._token.append(current_token)
            state.pos += 1

    def _get_next_non_whitespace(self, state):
        counter = {Tokens.Space: 0, Tokens.Enter: 0, Tokens.Tab: 0}
        while state.pos < len(state.all_tokens):
            if is_whitespace_token(state.all_tokens[state.pos].type):
                counter[state.all_tokens[state.pos].type] += 1
            else:
                break
            state.pos += 1
        return counter

    def _handle_indents(self, state, start, end, is_empty, no_errors):
        if is_empty and not self._config['Tabs and Indents']['Keep indents on empty lines']:
            if start != end:
                if not no_errors:
                    self._invalid_token.append(WrongToken(ERROR_SIZE + " in the end of line",
                                                          token=state.all_tokens[start]))
                    return True
            return False

        tab_size = self._config['Tabs and Indents']['Tab size']
        indent_size = self._config['Tabs and Indents']['Indent']
        cont_indent_size = self._config['Tabs and Indents']['Continuation indent']
        total_size_indent = indent_size * state.indent + cont_indent_size * state.continuous_indent
        number_of_tabs = total_size_indent // tab_size
        number_of_spaces = total_size_indent - number_of_tabs * tab_size

        if self._config['Tabs and Indents']['Use tab character']:
            index = start
            was_error = False
            while index <= end:
                if state.all_tokens[index].type == Tokens.Space:
                    if number_of_tabs > 0:
                        if not no_errors:
                            self._invalid_token.append(WrongToken(ERROR_ORDER + " in the indent",
                                                                  token=state.all_tokens[start]))
                        was_error = True
                        break
                    elif number_of_spaces == 0:
                        if not no_errors:
                            self._invalid_token.append(WrongToken(ERROR_SIZE + " of the indent",
                                                                  token=state.all_tokens[start]))
                        was_error = True
                        break
                    number_of_spaces -= 1
                else:
                    if number_of_tabs == 0:
                        if not no_errors:
                            self._invalid_token.append(WrongToken(ERROR_SIZE + " of the indent",
                                                                  token=state.all_tokens[start]))
                        was_error = True
                        break
                    number_of_tabs -= 1
                index += 1

            if not was_error and (number_of_tabs > 0 or number_of_spaces > 0 or index != end + 1):
                if not no_errors:
                    self._invalid_token.append(WrongToken(ERROR_SIZE + " of the indent",
                                                          token=state.all_tokens[start]))
                was_error = True
            number_of_tabs = total_size_indent // tab_size
            number_of_spaces = total_size_indent - number_of_tabs * tab_size
            for i in range(0, number_of_tabs):
                self._token.append(Token(token_type=Tokens.Tab,
                                         row=state.row_offset + state.all_tokens[start].row,
                                         column=tab_size * i))
            for i in range(0, number_of_spaces):
                self._token.append(Token(token_type=Tokens.Space,
                                         row=state.row_offset + state.all_tokens[start].row,
                                         column=i))
        else:
            index = start + 1
            was_error = False
            number_of_spaces = total_size_indent
            while index <= end:
                if state.all_tokens[index].type == Tokens.Space:
                    if number_of_spaces == 0:
                        if not no_errors:
                            self._invalid_token.append(WrongToken(ERROR_SIZE + " of the indent",
                                                                  token=state.all_tokens[start]))
                        was_error = True
                        break
                    number_of_spaces -= 1
                else:
                    if not no_errors:
                        self._invalid_token.append(WrongToken(ERROR_WRONG_WHITESPACE + " in the indent (no tabs rule)",
                                                              token=state.all_tokens[start]))
                    was_error = True
                    break
                index += 1

            if not was_error and (number_of_spaces > 0 or index != end + 1):
                if not no_errors:
                    self._invalid_token.append(WrongToken(ERROR_SIZE + " in the indent",
                                                          token=state.all_tokens[start]))
                was_error = True

            number_of_spaces = total_size_indent

            for i in range(0, number_of_spaces):
                self._token.append(Token(token_type=Tokens.Space,
                                         row=state.row_offset + state.all_tokens[start].row,
                                         column=i))
        return was_error

    def _next_pos_of_token(self):
        prev_token = self._token[-1]
        prev_start = prev_token.column
        prev_size = 1

        if prev_token.spec is not None and not (prev_token == Tokens.NumberLiteral or
                                                prev_token == Tokens.StartTemplateString or
                                                prev_token == Tokens.EndTemplateString or
                                                prev_token == Tokens.Identifier):
            prev_size = len(prev_token.spec)
        elif prev_token.spec is not None:
            prev_size = len(self._symbol_table[prev_token.index])
        elif prev_token.type == Tokens.InterpolationStart:
            prev_size = 2
        elif prev_token.type == Tokens.Tab:
            prev_size = self._config['Tabs and Indents']['Tab size']
        elif prev_token.type == Tokens.Enter:
            prev_size = 0
            prev_start = 0

        return prev_start + prev_size

    def _handle_whitespace_bitween_tokens(self, state, whitespace_rule):
        was_error = False
        declaration_start = state.pos
        counter = self._get_next_non_whitespace(state)
        index = declaration_start
        was_good_space = False
        was_bad_space = False
        if state.all_tokens[index].type == Tokens.Space:
            if whitespace_rule[Tokens.Space] >= 1:
                was_good_space = True
                self._token.append(state.all_tokens[index])
            else:
                was_bad_space = True
            index += 1

        while index < state.pos and state.all_tokens[index].type != Tokens.Enter:
            was_bad_space = True
            index += 1

        if state.all_tokens[index].type == Tokens.Enter and whitespace_rule[Tokens.Enter][1] != -1:
            if was_good_space or was_bad_space:
                self._invalid_token.append(WrongToken(message=ERROR_SIZE + " in the end of line",
                                                      token=state.all_tokens[declaration_start - 1]))
                was_error = True

            if was_good_space:
                self._token.pop()
            self._token.append(state.all_tokens[index])
            index += 1
            if index == len(state.all_tokens):
                return was_error
            counter[Tokens.Enter] -= 1
            no_errors = False
            if counter[Tokens.Enter] > max(whitespace_rule[Tokens.Enter][1], whitespace_rule[Tokens.Enter][0]) or \
                    counter[Tokens.Enter] < whitespace_rule[Tokens.Enter][0]:
                self._invalid_token.append(WrongToken(message=whitespace_rule['error_blank'],
                                                      token=state.all_tokens[declaration_start - 1]))
                no_errors = True
                if counter[Tokens.Enter] < whitespace_rule[Tokens.Enter][0]:
                    enter_number = whitespace_rule[Tokens.Enter][0]
                else:
                    enter_number = max(whitespace_rule[Tokens.Enter][1], whitespace_rule[Tokens.Enter][0])

                while enter_number > 0 and counter[Tokens.Enter] > 0:
                    cur_pos = index
                    while state.all_tokens[cur_pos].type == Tokens.Tab or \
                            state.all_tokens[cur_pos].type == Tokens.Space:
                        cur_pos += 1
                    was_error = self._handle_indents(state, index, cur_pos, counter[Tokens.Enter] > 0, no_errors)
                    if state.all_tokens[cur_pos].type == Tokens.Enter:
                        self._token.append(Token(token_type=Tokens.Enter,
                                                 row=state.all_tokens[cur_pos].row + state.row_offset,
                                                 column=self._next_pos_of_token()))
                        index = cur_pos + 1

                    counter[Tokens.Enter] -= 1
                    enter_number -= 1
                if enter_number == 0:
                    while counter[Tokens.Enter] > 0:
                        while state.all_tokens[index].type == Tokens.Tab or \
                                state.all_tokens[index].type == Tokens.Space:
                            index += 1
                        counter[Tokens.Enter] -= 1
                        state.row_offset -= 1
                        index += 1
                else:
                    row_list = [self._token[-1]]
                    prev_pos = -2
                    while self._token[prev_pos].type != Tokens.Enter:
                        row_list.append(self._token[prev_pos])
                        prev_pos -= 1
                    row_list.reverse()
                    while enter_number > 0:
                        self._token.extend(row_list)
                        enter_number -= 1
                        state.row_offset += 1

                cur_pos = index
                if index == len(state.all_tokens):
                    return was_error
                while state.all_tokens[cur_pos].type == Tokens.Tab or \
                        state.all_tokens[cur_pos].type == Tokens.Space:
                    cur_pos += 1
                was_error = self._handle_indents(state, index, cur_pos, counter[Tokens.Enter] > 0, False)
                if state.all_tokens[cur_pos].type == Tokens.Enter:
                    self._token.append(Token(token_type=Tokens.Enter,
                                             row=state.all_tokens[cur_pos].row + state.row_offset,
                                             column=self._next_pos_of_token()))
                    index = cur_pos + 1

            else:
                while counter[Tokens.Enter] >= 0:
                    cur_pos = index
                    while state.all_tokens[cur_pos].type == Tokens.Tab or state.all_tokens[cur_pos].type == Tokens.Space:
                        cur_pos += 1
                    was_error = self._handle_indents(state, index, cur_pos, counter[Tokens.Enter] > 0, no_errors)
                    if state.all_tokens[cur_pos].type == Tokens.Enter:
                        self._token.append(Token(token_type=Tokens.Enter,
                                                 row=state.all_tokens[cur_pos].row + state.row_offset,
                                                 column=self._next_pos_of_token()))
                        index = cur_pos + 1

                    counter[Tokens.Enter] -= 1
        else:
            if whitespace_rule[Tokens.Enter][0] == -1 or state.all_tokens[index].type == Tokens.Enter:
                if not was_error:
                    self._invalid_token.append(WrongToken(message=whitespace_rule['error_message'],
                                                          token=state.all_tokens[declaration_start - 1]))
                state.row_offset -= counter[Tokens.Enter]
                was_error = True

            if was_bad_space:
                if not was_error:
                    self._invalid_token.append(WrongToken(message=whitespace_rule['error_message'],
                                                          token=state.all_tokens[declaration_start - 1]))
                was_error = True

            if whitespace_rule[Tokens.Space] == 1:
                if not was_good_space:
                    self._token.append(Token(token_type=Tokens.Space,
                                             row=state.all_tokens[index].row + state.row_offset,
                                             column=self._next_pos_of_token()))
                if not was_error and not was_good_space:
                    self._invalid_token.append(WrongToken(message=whitespace_rule['error_message'],
                                                          token=state.all_tokens[declaration_start - 1]))
                    was_error = True

        return was_error

    def _rule_whitespace(self, space_number, enter_number, error_message, error_blank):
        return {Tokens.Space: space_number,
                Tokens.Enter: enter_number,
                "error_message": error_message,
                "error_blank": error_blank}

    def _handle_function_creation(self, state):
        declaration_start = state.pos
        self._token.append(state.all_tokens[state.pos])
        state.pos += 1

        max_blank_lines = self._config['Blank Lines']['Keep Maximum Blank Lines']

        whitespace_counter = self._get_next_non_whitespace(state)
        if state.pos >= len(state.all_tokens):
            state.pos = declaration_start + 1
            self._handle_whitespace_bitween_tokens(state,
                                                   self._rule_whitespace(space_number=0,
                                                                         enter_number=(0, max_blank_lines),
                                                                         error_message=ERROR_SIZE + " after token",
                                                                         error_blank=ERROR_SIZE + RULE_BLANK_MAX))
            return

        current_token = state.all_tokens[state.pos]
        state.pos = declaration_start + 1
        if current_token.type == Tokens.Punctuation and current_token.spec == '(':
            rule_error_text = ERROR_SIZE + ". Rule: Spaces before parentheses in function expression"
            space_number = int(self._config['Spaces']['Before Parentheses']['In function expression'])
            was_error = self._handle_whitespace_bitween_tokens(
                state,
                self._rule_whitespace(space_number=space_number,
                                      enter_number=(0, max_blank_lines),
                                      error_message=rule_error_text,
                                      error_blank=ERROR_SIZE + RULE_BLANK_MAX))

        else:
            rule_error = ERROR_SIZE + " after token"
            was_error = self._handle_whitespace_bitween_tokens(
                state,
                self._rule_whitespace(space_number=0,
                                      enter_number=(0, max_blank_lines),
                                      error_message=rule_error,
                                      error_blank=ERROR_SIZE + RULE_BLANK_MAX))

        '''
        was_error = self._handle_whitespace_bitween_tokens(state)
        if state.pos >= len(state.all_tokens):
            return

            start_parentheses = state.pos
            state.pos += 1
            white_space_counter = self._get_next_non_whitespace(state)
            if state.pos > len(state.all_tokens):

        '''
