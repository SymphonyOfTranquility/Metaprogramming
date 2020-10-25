import json
import sys

from Lexer import Lexer
from DictTokenTypes import Tokens
from TokenClasses import Token, WrongToken
from CharChecks import *


class _CurrentState:
    all_tokens = []

    def __init__(self):
        self.pos = 0
        self.row_offset = 0
        self.column_offset = 0
        self.indent = 0
        self.continuous_indent = 0
        self.empty_line_counter = 0


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
                    print('|' + self._symbol_table[tok.index] + '|')
                else:
                    print('')
            if tok.type == Tokens.Enter:
                print('')
        print('------------------------error syntax------------------------')
        for tok in self._invalid_token:
            print(tok, end=' ')
            if tok.token.index is not None:
                print('|' + self._symbol_table[tok.token.index] + '|')
            else:
                print('')

        print('------------------------lexer error------------------------')
        for tok in self._lexer_error_list:
            print(tok, end=' ')
            if tok.token.index is not None:
                print('|' + self._symbol_table[tok.token.index] + '|')
            else:
                print('')

        print('------------------------symbol table------------------------')
        for i in range(len(self._symbol_table)):
            print(str(i) + ') ', '|' + self._symbol_table[i] + '|')

    def _parse_next_token(self, state):
        current_token = state.all_tokens[state.pos]
        if current_token.type == Tokens.Space or current_token.type == Tokens.Tab or current_token.type == Tokens.Enter:
            self._handle_first_whitespaces(state)
            return

        while state.pos < len(state.all_tokens) and state.all_tokens[state.pos].type != Tokens.Enter:
            current_token = state.all_tokens[state.pos]
            self._token.append(current_token)
            state.pos += 1

        if state.pos < len(state.all_tokens):
            self._token.append(state.all_tokens[state.pos])
        state.pos += 1

    def _handle_first_whitespaces(self, state):
        need_tabs = self._config['Tabs and Indents']['Use tab character']

        start_pos = state.pos
        while state.pos < len(state.all_tokens) and is_whitespace(state.all_tokens[state.pos].type.value):
            if state.all_tokens[state.pos].type == Tokens.Enter:
                break
            state.pos += 1

        current_token = state.all_tokens[state.pos]
        if state.pos < len(state.all_tokens) and current_token.type == Tokens.Enter and \
                self._config['Tabs and Indents']['Keep indents on empty lines']:
            if state.pos != start_pos:
                self._invalid_token.append(WrongToken(message="Redundant spaces in empty line",
                                                      token=current_token))
            if True:
                # self._check_blank_lines(state): TO DO
                self._token.append(Token(token_type=Tokens.Enter,
                                         row=state.row_offset + current_token.row,
                                         column=0))
        else:
            tab_size = self._config['Tabs and Indents']['Tab size']
            indent_size = self._config['Tabs and Indents']['Indent']
            cont_indent_size = self._config['Tabs and Indents']['Continuation indent']

            counter_space_len = 0

            ind = start_pos
            while ind < state.pos:
                current_token = state.all_tokens[ind]
                if current_token.type == Tokens.Space:
                    counter_space_len += 1
                elif current_token.type == Tokens.Tab:
                    counter_space_len += tab_size
                else:
                    break
                ind += 1

            was_wrong = False
            # TO DO create check for secondary indent

            real_space_len = indent_size * state.indent + cont_indent_size * state.continuous_indent
            if real_space_len != counter_space_len:
                if state.pos < len(state.all_tokens):
                    self._invalid_token.append(WrongToken(message="Wrong number of whitespaces before",
                                                          token=state.all_tokens[state.pos]))
                else:
                    self._invalid_token.append(WrongToken(message="Wrong number of whitespaces in the end",
                                                          token=state.all_tokens[start_pos]))
                was_wrong = True
            if need_tabs:
                self._check_with_tabs(state, start_pos, real_space_len, was_wrong)
            else:
                self._check_without_tabs(state, start_pos, real_space_len, was_wrong)

            if state.pos < len(state.all_tokens) and state.all_tokens[state.pos].type == Tokens.Enter:
                self._token.append(Token(token_type=Tokens.Enter,
                                         row=state.row_offset + current_token.row,
                                         column=real_space_len))
                state.pos += 1

    def _check_with_tabs(self, state, start_pos, real_space_len, was_wrong):
        tab_size = self._config['Tabs and Indents']['Tab size']
        current_token = state.all_tokens[start_pos]

        tab_counter = 0
        space_counter = 0
        while real_space_len > 0:
            if real_space_len > tab_size:
                self._token.append(Token(token_type=Tokens.Tab,
                                         row=state.row_offset + current_token.row,
                                         column=tab_counter*tab_size))
                tab_counter += 1
                real_space_len -= tab_size
            else:
                self._token.append(Token(token_type=Tokens.Space,
                                         row=state.row_offset + current_token.row,
                                         column=tab_counter*tab_size + space_counter))
                space_counter += 1
                real_space_len -= 1

        if not was_wrong:
            ind = start_pos
            while ind < state.pos:
                current_token = state.all_tokens[ind]
                if current_token.type == Tokens.Space and tab_counter > 0:
                    self._invalid_token.append(WrongToken(message="Wrong token space here",
                                                          token=current_token))
                elif current_token.type == Tokens.Tab:
                    tab_counter -= 1
                else:
                    break

                ind += 1

    def _check_without_tabs(self, state, start_pos, real_space_len, was_wrong):
        current_token = state.all_tokens[start_pos]

        for i in range(real_space_len):
            self._token.append(Token(token_type=Tokens.Space,
                                     row=state.row_offset + current_token.row,
                                     column=i))

        if not was_wrong:
            ind = start_pos
            while ind < state.pos:
                current_token = state.all_tokens[ind]
                if current_token.type == Tokens.Tab:
                    self._invalid_token.append(WrongToken(message="Wrong token tab here",
                                                          token=current_token))
                else:
                    break

                ind += 1

