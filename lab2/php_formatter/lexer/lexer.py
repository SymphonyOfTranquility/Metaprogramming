import errno

from ._dict_token_types import Tokens
from ._char_checks import *
from ._token_classes import Token, WrongToken


class _CurrentLineState:
    all_lines = []

    def __init__(self):
        self.column = 0
        self.row = 0
        self.line = ""
        self.token = Token(token_type=Tokens.Invalid)
        self.multi_line_mode = False

    def copy(self, instance):
        self.row = instance.row
        self.column = instance.column
        self.line = instance.line


class Lexer:

    def __init__(self):
        self._symbol_table = []
        self._token = []
        self._invalid_token = []

    def process_php_file(self, path_to_file):
        try:
            f = open(path_to_file, "r")
            state = _CurrentLineState()
            all_lines = [line for line in f]
            _CurrentLineState.all_lines = all_lines

            while state.row < len(all_lines):
                state.line = all_lines[state.row]
                state.column = 0
                while state.column < len(state.line):
                    self._get_next_token(state)
                state.row += 1
            state.row -= 1
            state.column -= 1
            self._check_multi_line_mode(state)

        except IOError as x:
            if x.errno == errno.ENOENT:
                print(path_to_file, '- does not exist')
            elif x.errno == errno.EACCES:
                print(path_to_file, '- cannot be read')
            else:
                print(path_to_file, '- some other error')

    def get_tokens_list(self):
        return self._token

    def get_error_tokens_list(self):
        return self._invalid_token

    def get_symbol_table(self):
        return self._symbol_table

    def _check_multi_line_mode(self, state):
        if state.multi_line_mode:
            if state.token.type == Tokens.MultiLineComment:
                self._invalid_token.append(WrongToken(message="Multi line comment requires end",
                                                      token=state.token))
            if state.token.type == Tokens.StringLiteral and state.token.spec != '`':
                self._invalid_token.append(WrongToken(message="String literal requires the end",
                                                      token=state.token))
            if state.token.type == Tokens.StringLiteral and state.token.spec == '`':
                self._token.append(Token(token_type=Tokens.EndTemplateString,
                                         row=state.row,
                                         column=state.column))
                self._invalid_token.append(WrongToken(message="String literal requires the end",
                                                      token=self._token[-1]))

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

    def _get_next_token(self, state):
        if state.multi_line_mode:
            self._handle_multi_line_mode(state)
            return

        if len(state.line) <= state.column:
            return

        current_symbol = state.line[state.column]

        if is_whitespace(current_symbol):
            self._handle_whitespaces(state)
            return

        if is_string(current_symbol):
            self._handle_strings(state)
            return

        if state.column + 1 < len(state.line) and is_comment(current_symbol, state.line[state.column + 1]):
            self._handle_comment(state)
            return

        if is_number(current_symbol) or is_dot(current_symbol):
            self._handle_number(state)
            return

        if is_symbol(current_symbol):
            self._handle_word(state)
            return

        if is_dollar(current_symbol):
            self._handle_variable(state)
            return

        if is_operation(current_symbol):
            self._handle_operation(state)
            return

        if is_punctuation(current_symbol):
            self._handle_punctuation(state)
            return

        self._add_wrong_token(token_type=Tokens.Invalid,
                              row=state.row,
                              column=state.column,
                              lit_value=current_symbol,
                              error_message="Invalid symbol")
        state.column += 1

    def _handle_whitespaces(self, state):
        while state.column < len(state.line):
            current_symbol = state.line[state.column]
            if current_symbol == ' ':
                self._token.append(Token(token_type=Tokens.Space,
                                         row=state.row,
                                         column=state.column))
            elif current_symbol == '\t':
                self._token.append(Token(token_type=Tokens.Tab,
                                         row=state.row,
                                         column=state.column))
            elif current_symbol == '\n':
                self._token.append(Token(token_type=Tokens.Enter,
                                         row=state.row,
                                         column=state.column))
            else:
                break
            state.column += 1

    def _handle_punctuation(self, state):
        current_symbol = state.line[state.column]
        self._token.append(Token(token_type=Tokens.Punctuation,
                                 row=state.row,
                                 column=state.column,
                                 spec=current_symbol))
        state.column += 1

    def _add_wrong_token(self, token_type, row, column, lit_value, error_message):
        self._token.append(Token(token_type=token_type,
                                 row=row,
                                 column=column,
                                 index=len(self._symbol_table)))
        self._symbol_table.append(lit_value)
        self._invalid_token.append(WrongToken(message=error_message,
                                              token=self._token[-1]))

    def _add_correct_token(self, token_type, row, column, lit_value, token_spec=None):
        self._token.append(Token(token_type=token_type,
                                 row=row,
                                 column=column,
                                 index=len(self._symbol_table),
                                 spec=token_spec))
        self._symbol_table.append(lit_value)

    def _handle_nonnormal_number(self, state, check_func, type_number):
        start_pos = state.column
        new_number = state.line[state.column:state.column+2]
        state.column += 2
        last_bad = False
        while state.column < len(state.line):
            current_symbol = state.line[state.column]
            if check_func(current_symbol):
                new_number += current_symbol
                last_bad = False
            elif is_down_dash(current_symbol):
                last_bad = True
                new_number += current_symbol
            else:
                break

            state.column += 1

        if last_bad:
            self._add_wrong_token(token_type=Tokens.NumberLiteral,
                                  row=state.row,
                                  column=start_pos,
                                  lit_value=new_number,
                                  error_message="Incorrect number ending")
            return

        if state.column >= len(state.line) or is_correct_after_number(state.line[state.column]):
            self._add_correct_token(token_type=Tokens.NumberLiteral,
                                    row=state.row,
                                    column=start_pos,
                                    lit_value=new_number,
                                    token_spec=Tokens.NumberLiteral.value[type_number])
            return

        if state.line[state.column] == 'n':
            # octal
            state.column += 1
            new_number += 'n'

            if type_number == 3 and new_number[1] == '0':
                self._add_wrong_token(token_type=Tokens.NumberLiteral,
                                      row=state.row,
                                      column=start_pos,
                                      lit_value=new_number,
                                      error_message="Incorrect writing for big octal numbers")
                return

            elif state.column >= len(state.line) or is_correct_after_number(state.line[state.column]):
                self._add_correct_token(token_type=Tokens.NumberLiteral,
                                        row=state.row,
                                        column=start_pos,
                                        lit_value=new_number,
                                        token_spec=Tokens.NumberLiteral.value[type_number + 4])
                return

        self._add_wrong_token(token_type=Tokens.NumberLiteral,
                              row=state.row,
                              column=start_pos,
                              lit_value=new_number + state.line[state.column],
                              error_message="Incorrect number ending")
        state.column += 1

    def _check_nonnormal_numbers(self, state):
        hex_val = is_nonnormal_start(state, is_hex, 'Xx')
        oct_val = is_nonnormal_start(state, is_octal, '0oO')
        bin_val = is_nonnormal_start(state, is_binary, 'Bb')

        if hex_val == 1:
            self._handle_nonnormal_number(state, is_hex, 4)
            return True
        if oct_val == 1:
            self._handle_nonnormal_number(state, is_octal, 3)
            return True
        if bin_val == 1:
            self._handle_nonnormal_number(state, is_binary, 2)
            return True

        if hex_val*oct_val*bin_val == 0:
            ans = 'hex'
            if oct_val == 0:
                ans = 'oct'
            if bin_val == 0:
                ans = 'bin'
            self._add_wrong_token(token_type=Tokens.NumberLiteral,
                                  row=state.row,
                                  column=state.column,
                                  lit_value=state.line[state.column:state.column+2],
                                  error_message="Invalid" + ans + "token")
            state.column += 2
            return True

        return False

    def _handle_number(self, state):
        if self._check_nonnormal_numbers(state):
            return

        current_symbol = state.line[state.column]

        if is_dot(current_symbol):
            if state.column + 1 >= len(state.line) or not is_number(state.line[state.column + 1]):
                if is_dot(state.line[state.column + 1]) and \
                          state.column + 2 < len(state.line) and is_dot(state.line[state.column + 2]):
                    self._token.append(Token(token_type=Tokens.Operators,
                                             spec='...',
                                             row=state.row,
                                             column=state.column))
                    state.column += 3
                else:
                    self._token.append(Token(token_type=Tokens.Punctuation,
                                             row=state.row,
                                             column=state.column,
                                             spec=current_symbol))
                    state.column += 1
                return

        if current_symbol == '0' and state.column + 1 < len(state.line) and \
                not is_correct_after_number(state.line[state.column + 1]) and \
                not is_dot(state.line[state.column + 1]):
            state.column += 1
            self._add_wrong_token(token_type=Tokens.NumberLiteral,
                                  row=state.row,
                                  column=state.column-1,
                                  lit_value=current_symbol+state.line[state.column],
                                  error_message="Not allowed start from zero")
            state.column += 1
            return

        new_number = ""
        was_dot, was_e, was_sign, was_dash, last_dash = False, False, False, False, False
        start_pos = state.column
        unknown = False

        while state.column < len(state.line):
            current_symbol = state.line[state.column]
            if is_number(current_symbol):
                new_number += current_symbol
                last_dash = False

            elif is_dot(current_symbol):
                new_number += current_symbol
                if last_dash:
                    self._add_wrong_token(token_type=Tokens.NumberLiteral,
                                          row=state.row,
                                          column=start_pos,
                                          lit_value=new_number,
                                          error_message="Unexpected symbol in the number end")
                    state.column += 1
                    return
                was_dot = True
                break

            elif is_e(current_symbol):
                new_number += current_symbol
                if last_dash:
                    self._add_wrong_token(token_type=Tokens.NumberLiteral,
                                          row=state.row,
                                          column=start_pos,
                                          lit_value=new_number,
                                          error_message="Unexpected symbol in the number end")
                    state.column += 1
                    return
                was_e = True
                break

            elif is_down_dash(current_symbol):
                last_dash = True
                new_number += current_symbol

            else:
                unknown = True
                break

            state.column += 1

        if was_dot:
            state.column += 1
            if state.column < len(state.line) and \
                    (is_number(state.line[state.column]) or is_e(state.line[state.column])):
                while state.column < len(state.line):
                    current_symbol = state.line[state.column]
                    if is_number(current_symbol):
                        new_number += current_symbol
                        last_dash = False

                    elif is_e(current_symbol):
                        new_number += current_symbol
                        if last_dash:
                            self._add_wrong_token(token_type=Tokens.NumberLiteral,
                                                  row=state.row,
                                                  column=start_pos,
                                                  lit_value=new_number,
                                                  error_message="Unexpected symbol in the number end")
                            state.column += 1
                            return

                        was_e = True
                        break
                    elif is_down_dash(current_symbol):
                        last_dash = True
                        new_number += current_symbol

                    else:
                        unknown = True
                        break
                    state.column += 1

        if was_e:
            state.column += 1
            if state.column < len(state.line) and \
                    (is_number(state.line[state.column]) or state.line[state.column] in '+-'):
                if state.line[state.column] in '+-':
                    new_number += state.line[state.column]
                    state.column += 1
                    if state.column >= len(state.line) or not is_number(state.line[state.column]):
                        new_number = new_number[:-1]
                        self._add_wrong_token(token_type=Tokens.NumberLiteral,
                                              row=state.row,
                                              column=start_pos,
                                              lit_value=new_number,
                                              error_message="Unexpected symbol in the number end")

                        state.column -= 1
                        return

                while state.column < len(state.line):
                    current_symbol = state.line[state.column]
                    if is_number(current_symbol):
                        new_number += current_symbol
                        last_dash = False

                    elif is_down_dash(current_symbol):
                        last_dash = True
                        new_number += current_symbol

                    else:
                        unknown = True
                        break

                    state.column += 1

            else:
                self._add_wrong_token(token_type=Tokens.NumberLiteral,
                                      row=state.row,
                                      column=start_pos,
                                      lit_value=new_number,
                                      error_message="Unexpected symbol in the number end")
                return

        if last_dash:
            self._add_wrong_token(token_type=Tokens.NumberLiteral,
                                  row=state.row,
                                  column=start_pos,
                                  lit_value=new_number,
                                  error_message="Unexpected symbol in the number end")
            state.column += 1
            return

        if unknown:
            if is_correct_after_number(state.line[state.column]):
                cur_spec = Tokens.NumberLiteral.value[1]
                if was_dot or was_e:
                    cur_spec = Tokens.NumberLiteral.value[0]

                self._add_correct_token(token_type=Tokens.NumberLiteral,
                                        row=state.row,
                                        column=start_pos,
                                        lit_value=new_number,
                                        token_spec=cur_spec)

            elif state.line[state.column] == 'n':
                new_number += 'n'
                if was_dot or was_e:
                    self._add_wrong_token(token_type=Tokens.NumberLiteral,
                                          row=state.row,
                                          column=start_pos,
                                          lit_value=new_number,
                                          error_message="Invalid biginteger literal")
                else:
                    self._add_correct_token(token_type=Tokens.NumberLiteral,
                                            row=state.row,
                                            column=start_pos,
                                            lit_value=new_number,
                                            token_spec=Tokens.NumberLiteral.value[5])
                state.column += 1
            else:
                self._add_wrong_token(token_type=Tokens.NumberLiteral,
                                      row=state.row,
                                      column=start_pos,
                                      lit_value=new_number+state.line[state.column],
                                      error_message="Unexpected symbol in the number end")
                state.column += 1
        else:
            cur_spec = Tokens.NumberLiteral.value[1]
            if was_dot or was_e:
                cur_spec = Tokens.NumberLiteral.value[0]

            self._add_correct_token(token_type=Tokens.NumberLiteral,
                                    row=state.row,
                                    column=start_pos,
                                    lit_value=new_number,
                                    token_spec=cur_spec)

    def _handle_word(self, state):
        word = ""
        start_pos = state.column
        while state.column < len(state.line):
            current_symbol = state.line[state.column]
            if not is_word(current_symbol):
                break
            word += current_symbol
            state.column += 1
        if word in Tokens.Keyword.value:
            self._token.append(Token(token_type=Tokens.Keyword,
                                     row=state.row,
                                     column=start_pos,
                                     spec=word))
            return
        if word in Tokens.ConstLiteral.value:
            self._token.append(Token(token_type=Tokens.ConstLiteral,
                                     row=state.row,
                                     column=start_pos,
                                     spec=word))
            return
        self._add_correct_token(token_type=Tokens.Identifier,
                                row=state.row,
                                column=start_pos,
                                lit_value=word)

    def _handle_variable(self, state):
        if state.column + 1 >= len(state.line) or not is_symbol(state.line[state.column + 1]):
            self._add_wrong_token(token_type=Tokens.Variable,
                                  row=state.row,
                                  column=state.column,
                                  lit_value='$',
                                  error_message="Not completed variable")
        word = "$"
        state.column += 1
        start_pos = state.column
        while state.column < len(state.line):
            current_symbol = state.line[state.column]
            if not is_word(current_symbol):
                break
            word += current_symbol
            state.column += 1
        if word in Tokens.Keyword.value:
            self._token.append(Token(token_type=Tokens.Keyword,
                                     row=state.row,
                                     column=start_pos,
                                     spec=word))
            return
        if word in Tokens.ConstLiteral.value:
            self._token.append(Token(token_type=Tokens.ConstLiteral,
                                     row=state.row,
                                     column=start_pos,
                                     spec=word))
            return
        self._add_correct_token(token_type=Tokens.Variable,
                                row=state.row,
                                column=start_pos,
                                lit_value=word)

    def _handle_operation(self, state):
        op = ""
        start_pos = state.column
        while state.column < len(state.line):
            temp_op = op + state.line[state.column]
            if temp_op in Tokens.Operators.value:
                op = temp_op
            else:
                break
            state.column += 1

        self._token.append(Token(token_type=Tokens.Operators,
                                 row=state.row,
                                 column=start_pos,
                                 spec=op))

    def _handle_single_line_comment(self, state):
        if state.line[-1] != '\n':
            comment = state.line[state.column:]
        else:
            comment = state.line[state.column:-1]
        self._add_correct_token(token_type=Tokens.SingleLineComment,
                                row=state.row,
                                column=state.column,
                                lit_value=comment)

        if state.line[-1] == '\n':
            state.column = len(state.line)-1
        else:
            state.column = len(state.line)

    def _handle_multi_line_comment(self, state):
        pos = state.line[state.column:].find("*/")
        if pos == -1:
            comment = state.line[state.column:]
            self._symbol_table[state.token.index] += comment
            state.column = len(state.line)
            state.multi_line_mode = True
        else:
            comment = state.line[state.column:state.column + pos + 2]
            self._symbol_table[state.token.index] += comment
            state.column += pos + 2
            state.multi_line_mode = False
            state.token = None

    def _init_multi_line_comment(self, state):
        self._add_correct_token(token_type=Tokens.MultiLineComment,
                                row=state.row,
                                column=state.column,
                                lit_value=state.line[state.column:state.column + 2])
        state.token = self._token[-1]
        state.multi_line_mode = True
        state.column += 2

    def _handle_comment(self, state):
        if state.line[state.column:state.column+2] == Tokens.SingleLineComment.value:
            self._handle_single_line_comment(state)
        else:
            self._init_multi_line_comment(state)

    def _handle_multi_line_mode(self, state):
        if state.token.type == Tokens.MultiLineComment:
            self._handle_multi_line_comment(state)
        elif state.token.type == Tokens.StringLiteral and state.token.spec == "'":
            self._handle_common_string(state)
        elif state.token.type == Tokens.StringLiteral and state.token.spec == '"':
            self._handle_template_string(state)
        else:
            state.multi_line_mode = False

    def _init_common_string(self, state):
        self._add_correct_token(token_type=Tokens.StringLiteral,
                                row=state.row,
                                column=state.column,
                                lit_value=state.line[state.column],
                                token_spec=state.line[state.column])
        state.token = self._token[-1]
        state.multi_line_mode = True
        state.column += 1

    def _handle_common_string(self, state):
        st = state.column
        ending = state.token.spec
        while st < len(state.line):
            temp_s = state.line[st:]
            pos = temp_s.find(ending)
            if pos == -1:
                string_lit = state.line[state.column:]
                self._symbol_table[state.token.index] += string_lit
                state.column = len(state.line)
                return
            else:
                st += pos
                if state.line[st - 1] == '\\':
                    slash_pos = st - 1
                    while slash_pos >= state.column and state.line[slash_pos] == '\\':
                        slash_pos -= 1
                    if (st - 1 - slash_pos) % 2 == 1:
                        st += 1
                        continue

                string_lit = state.line[state.column:st+1]
                self._symbol_table[state.token.index] += string_lit
                state.column = st + 1
                state.token = None
                state.multi_line_mode = False
                return

    def _init_template_string(self, state):
        self._token.append(Token(token_type=Tokens.StartTemplateString,
                                 row=state.row,
                                 column=state.column))
        self._add_correct_token(token_type=Tokens.StringLiteral,
                                row=state.row,
                                column=state.column,
                                lit_value="",
                                token_spec=state.line[state.column])
        state.token = self._token[-1]
        state.multi_line_mode = True
        state.column += 1

    def _get_next_token_interpolate(self, state):
        current_symbol = state.line[state.column]
        if not state.multi_line_mode and current_symbol == Tokens.InterpolationEnd.value:
            self._token.append(Token(token_type=Tokens.InterpolationEnd,
                                     row=state.row,
                                     column=state.column))
            return True
        else:
            self._get_next_token(state)
            return False

    def _interpolate(self, state):

        self._token.append(Token(token_type=Tokens.InterpolationStart,
                                 row=state.row,
                                 column=state.column))
        state.column += 2

        while state.row < len(state.all_lines):
            state.line = state.all_lines[state.row]
            while state.column < len(state.line):
                if self._get_next_token_interpolate(state):
                    return
            state.column = 0
            state.row += 1
        state.row -= 1
        state.column = len(state.all_lines[-1])-1
        self._check_multi_line_mode(state)

        self._token.append(Token(token_type=Tokens.InterpolationEnd,
                                 row=state.row,
                                 column=state.column))
        self._invalid_token.append(WrongToken(message="There was no end for interpolation",
                                              token=self._token[-1]))

    def _check_interpolation(self, state, start, end):
        line_slice = state.line[start:end]
        symbols = "${"
        pos = line_slice.find(symbols)
        if pos == -1:
            return False
        string_literal = state.line[state.column:state.column + pos]
        state.column += pos
        self._symbol_table[state.token.index] += string_literal
        new_state = _CurrentLineState()
        new_state.copy(state)
        self._interpolate(new_state)
        state.copy(new_state)

        self._add_correct_token(token_type=Tokens.StringLiteral,
                                row=state.row,
                                column=state.column,
                                lit_value='',
                                token_spec='"')
        state.token = self._token[-1]
        state.column += 1
        return True

    def _handle_template_string(self, state):
        st = state.column
        ending = state.token.spec
        while st < len(state.line):
            temp_s = state.line[st:]
            pos = temp_s.find(ending)
            if pos == -1:
                if self._check_interpolation(state, state.column, len(state.line)):
                    return

                string_lit = state.line[state.column:]
                self._symbol_table[state.token.index] += string_lit
                state.column = len(state.line)
                return
            else:
                st += pos
                if self._check_interpolation(state, state.column, st):
                    return
                if st-1 >= state.column and state.line[st - 1] == '\\':
                    slash_pos = st - 1
                    while slash_pos >= state.column and state.line[slash_pos] == '\\':
                        slash_pos -= 1
                    if (st - 1 - slash_pos) % 2 == 1:
                        st += 1
                        continue

                string_lit = state.line[state.column:st]
                self._symbol_table[state.token.index] += string_lit
                self._token.append(Token(token_type=Tokens.EndTemplateString,
                                         row=state.row,
                                         column=st))
                state.column = st + 1
                state.token = None
                state.multi_line_mode = False
                return

    def _handle_strings(self, state):
        if state.line[state.column] == "'":
            self._init_common_string(state)
        else:
            self._init_template_string(state)
