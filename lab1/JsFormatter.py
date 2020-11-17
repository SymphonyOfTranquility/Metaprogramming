import sys
import os
from os import listdir
from os.path import isfile, join, splitext
import json
from enum import Enum

from Lexer import Lexer
from DictTokenTypes import Tokens, Scope
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
RULE_BLANK_MAX = ". Rule: Blank Lines -> Keep Maximum Blank Lines"
_MAX_BLANK_LINES = 2


class _CurrentState:
    all_tokens = []

    def __init__(self):
        self.pos = 0
        self.row_offset = 0
        self.column_offset = 0
        self.indent = 0
        self.continuous_indent = 0
        self.empty_line_counter = 0
        self.outer_scope = Scope.GeneralScope


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

        global _MAX_BLANK_LINES
        _MAX_BLANK_LINES = self._config['Blank Lines']['Keep Maximum Blank Lines']

    def process_js_file(self, path_to_file):
        lexer = Lexer()
        lexer.process_js_file(path_to_file)
        _CurrentState.all_tokens = lexer.get_tokens_list()
        self._lexer_error_list = lexer.get_error_tokens_list()
        self._symbol_table = lexer.get_symbol_table()
        state = _CurrentState()

        while state.pos < len(state.all_tokens) and is_whitespace_token(state.all_tokens[state.pos].type):
            state.pos += 1

        if state.pos != 0:
            self._invalid_token.append(WrongToken(message="Whitespaces iat the beginning of the file",
                                                  token=state.all_tokens[state.pos]))

        while state.pos < len(state.all_tokens):
            self._parse_next_token(state, Scope.GeneralScope)

    def _parse_next_token(self, state, where, handle_indent=False):
        current_token = state.all_tokens[state.pos]
        prev_token = self._get_prev_token(state)
        was_comma = False
        if (prev_token.type == Tokens.Punctuation and prev_token.spec == ',' or
                current_token.type == Tokens.Punctuation and current_token.spec == ',') and \
                (where is not None and where.value > Scope.Do.value and state.outer_scope != Scope.ArrayBrackets and
                 state.outer_scope != Scope.IndexAccessBrackets and state.outer_scope != Scope.PropertyNameValue and
                 state.outer_scope != Scope.ObjectLiteralBrace):
            was_comma = True
            state.continuous_indent += 1

        if current_token.type == Tokens.Keyword:
            self._handle_keywords(state, where)
        elif current_token.type == Tokens.Identifier:
            self._handle_identifier_cases(state, where)
        elif current_token.type == Tokens.Operators:
            self._handle_operators(state)
        elif current_token.type == Tokens.Punctuation:
            self._handle_punctuation(state, where)
        else:
            self._token.append(current_token)

        if state.pos < len(state.all_tokens) and not handle_indent:
            if where == Scope.Switch and current_token.spec == ':':
                self._check_space_to_next_token(state, where, (0, _MAX_BLANK_LINES))
            else:
                self._check_space_to_next_token(state, where)

        if was_comma:
            state.continuous_indent = max(state.continuous_indent - 1, 0)

    def _get_next_non_whitespace(self, state):
        counter = {Tokens.Space: 0, Tokens.Enter: 0, Tokens.Tab: 0}
        while state.pos < len(state.all_tokens):
            if is_whitespace_token(state.all_tokens[state.pos].type):
                counter[state.all_tokens[state.pos].type] += 1
            else:
                break
            state.pos += 1
        # if counter[Tokens.Space] == counter[Tokens.Enter] == counter[Tokens.Tab]:
        #     state.pos += 1
        return counter

    def _get_prev_non_whitespace(self, state):
        counter = {Tokens.Space: 0, Tokens.Enter: 0, Tokens.Tab: 0}
        start_pos = state.pos
        while start_pos >= 0:
            if is_whitespace_token(state.all_tokens[start_pos].type):
                counter[state.all_tokens[start_pos].type] += 1
            else:
                break
            start_pos -= 1
        return counter

    def _check_space_to_next_token(self, state, where, enter_number=(-1, _MAX_BLANK_LINES)):

        error_blank = ERROR_SIZE + RULE_BLANK_MAX

        prev_token = state.all_tokens[state.pos]

        next_token = self._get_next_token(state)

        if next_token.is_fake():
            return

        space_number, error_message = self._get_check_tokens_result(state, prev_token, next_token, where)

        state.pos += 1
        self._handle_whitespace_between_tokens(
            state,
            self._rule_whitespace(space_number=space_number,
                                  enter_number=enter_number,
                                  error_message=error_message,
                                  error_blank=error_blank))

    def _error_rule_text_creation(self, main_rule, sub_rule, rule_name):
        return ". Rule: " + main_rule + " -> " + sub_rule + " -> " + rule_name + "."

    # 5 next funcs - checks for next and prev token
    def _check_token_operators(self, state, token, where):
        error_text = ERROR_SIZE

        # Spaces -> Around operators
        if token.spec in Scope.AssignmentOperators.value:
            error_text += self._error_rule_text_creation("Spaces", "Around operators", "Assignment")
            return int(self._config["Spaces"]["Around operators"]["Assignment"]), error_text

        if token.spec in Scope.LogicOperators.value:
            error_text += self._error_rule_text_creation("Spaces", "Around operators", "Logical")
            return int(self._config["Spaces"]["Around operators"]["Logical"]), error_text

        if token.spec in Scope.EqualityOperators.value:
            error_text += self._error_rule_text_creation("Spaces", "Around operators", "Equality")
            return int(self._config["Spaces"]["Around operators"]["Equality"]), error_text

        if token.spec in Scope.RelationalOperators.value:
            error_text += self._error_rule_text_creation("Spaces", "Around operators", "Relational")
            return int(self._config["Spaces"]["Around operators"]["Relational"]), error_text

        if token.spec in Scope.BitwiseOperators.value:
            error_text += self._error_rule_text_creation("Spaces", "Around operators", "Bitwise")
            return int(self._config["Spaces"]["Around operators"]["Bitwise"]), error_text

        if token.spec in Scope.AdditiveOperators.value:
            error_text += self._error_rule_text_creation("Spaces", "Around operators", "Additive")
            return int(self._config["Spaces"]["Around operators"]["Additive"]), error_text

        if token.spec in Scope.MultiplicativeOperators.value:
            if where == Scope.FuncDeclaration and token.spec == '*':
                return -1, ""
            error_text += self._error_rule_text_creation("Spaces", "Around operators", "Multiplicative")
            return int(self._config["Spaces"]["Around operators"]["Multiplicative"]), error_text

        if token.spec in Scope.ShiftOperators.value:
            error_text += self._error_rule_text_creation("Spaces", "Around operators", "Shift")
            return int(self._config["Spaces"]["Around operators"]["Shift"]), error_text

        if token.spec in Scope.UnaryAdditiveOperators.value:
            error_text += self._error_rule_text_creation("Spaces", "Around operators", "Unary additive")
            return int(self._config["Spaces"]["Around operators"]["Unary additive"]), error_text

        if token.spec in Scope.ArrowFunction.value:
            error_text += self._error_rule_text_creation("Spaces", "Around operators", "Arrow function")
            return int(self._config["Spaces"]["Around operators"]["Arrow function"]), error_text

        return -1, error_text + " after token"

    def _check_general_space_for_prev_next_token(self, state, prev_token, next_token, where):
        error_text = ERROR_SIZE

        if prev_token.type == Tokens.Punctuation and prev_token.spec is not None and \
                next_token.type == Tokens.Punctuation and next_token.spec is not None and \
                (next_token.spec in '{[(' and prev_token.spec in '{[(' or
                 next_token.spec in '}])' and prev_token.spec in '{[(' or
                 next_token.spec in '}])' and prev_token.spec in '}])'):
            error_text += " between bkts"
            if prev_token.spec in '{[':
                state.indent += 1
            if next_token.spec in '}]':
                state.indent = max(state.indent - 1, 0)

            if prev_token.spec in '(':
                state.continuous_indent += 1
            if next_token.spec in ')':
                state.continuous_indent = max(state.continuous_indent - 1, 0)
            return 0, error_text

        if prev_token.type == Tokens.Punctuation and prev_token.spec == '.' or \
                next_token.type == Tokens.Punctuation and next_token.spec == '.':
            error_text += " after token"
            return 0, error_text

        # Spaces -> Within
        if prev_token.type == Tokens.Punctuation and prev_token.spec == '(' or \
                next_token.type == Tokens.Punctuation and next_token.spec == ')':
            if prev_token.spec == '(' and not next_token.is_fake():
                state.continuous_indent += 1
            elif next_token.spec == ')' and not prev_token.is_fake():
                state.continuous_indent = max(state.continuous_indent - 1, 0)

            if where == Scope.FuncDeclaration:
                error_text += self._error_rule_text_creation("Spaces", "Within", "Function declaration parentheses")
                return int(self._config['Spaces']['Within']['Function declaration parentheses']), error_text

            elif where == Scope.FuncCall:
                error_text += self._error_rule_text_creation("Spaces", "Within", "Function call parentheses")
                return int(self._config['Spaces']['Within']['Function call parentheses']), error_text

            elif where == Scope.Grouping:
                error_text += self._error_rule_text_creation("Spaces", "Within", "Grouping parentheses")
                return int(self._config['Spaces']['Within']['Grouping parentheses']), error_text

            elif where == Scope.If:
                error_text += self._error_rule_text_creation("Spaces", "Within", "'if' parentheses")
                return int(self._config['Spaces']['Within']["'if' parentheses"]), error_text

            elif where == Scope.For:
                error_text += self._error_rule_text_creation("Spaces", "Within", "'for' parentheses")
                return int(self._config['Spaces']['Within']["'for' parentheses"]), error_text

            elif where == Scope.While:
                error_text += self._error_rule_text_creation("Spaces", "Within", "'while' parentheses")
                return int(self._config['Spaces']['Within']["'while' parentheses"]), error_text

            elif where == Scope.Switch:
                error_text += self._error_rule_text_creation("Spaces", "Within", "'switch' parentheses")
                return int(self._config['Spaces']['Within']["'switch' parentheses"]), error_text

            elif where == Scope.Catch:
                error_text += self._error_rule_text_creation("Spaces", "Within", "'catch' parentheses")
                return int(self._config['Spaces']['Within']["'catch' parentheses"]), error_text

        if prev_token.type == Tokens.Punctuation and prev_token.spec == '{' or \
                next_token.type == Tokens.Punctuation and next_token.spec == '}':

            if prev_token.spec == '{' and not next_token.is_fake():
                state.indent += 1
            elif next_token.spec == '}' and not prev_token.is_fake():
                state.indent = max(state.indent - 1, 0)

            if where == Scope.ObjectLiteralBrace:
                error_text += self._error_rule_text_creation("Spaces", "Within", "Object literal braces")
                return int(self._config['Spaces']['Within']["Object literal braces"]), error_text
            elif where == Scope.ES6ImportBrace:
                error_text += self._error_rule_text_creation("Spaces", "Within", "ES6 import/export braces")
                return int(self._config['Spaces']['Within']["ES6 import/export braces"]), error_text

        if prev_token.type == Tokens.InterpolationStart or next_token.type == Tokens.InterpolationEnd:
            if prev_token.type == Tokens.InterpolationStart and not next_token.is_fake():
                state.continuous_indent += 1
            elif next_token.type == Tokens.InterpolationEnd and not prev_token.is_fake():
                state.continuous_indent = max(state.continuous_indent - 1, 0)

            if where == Scope.Interpolation:
                error_text += self._error_rule_text_creation("Spaces", "Within", "Interpolation expressions")
                return int(self._config['Spaces']['Within']["Interpolation expressions"]), error_text

        if prev_token.type == Tokens.Punctuation and prev_token.spec == '[' or \
                next_token.type == Tokens.Punctuation and next_token.spec == ']':
            if prev_token.spec == '[' and not next_token.is_fake():
                if where == Scope.IndexAccessBrackets:
                    state.continuous_indent += 1
                else:
                    state.indent += 1
            elif next_token.spec == ']' and not prev_token.is_fake():
                if where == Scope.IndexAccessBrackets:
                    state.continuous_indent = max(state.continuous_indent - 1, 0)
                else:
                    state.indent = max(state.indent - 1, 0)

            if where == Scope.IndexAccessBrackets:
                error_text += self._error_rule_text_creation("Spaces", "Within", "Index access brackets")
                return int(self._config['Spaces']['Within']["Index access brackets"]), error_text
            elif where == Scope.ArrayBrackets:
                error_text += self._error_rule_text_creation("Spaces", "Within", "Array brackets")
                return int(self._config['Spaces']['Within']["Array brackets"]), error_text

        # General Rule Between operators at least 1 space
        if prev_token.type == Tokens.Operators and next_token.type == Tokens.Operators:
            error_text += " between operators"
            return 1, error_text

        # Spaces -> Other
        if prev_token.type == Tokens.Operators and prev_token.spec == '...' and next_token.type == Tokens.Identifier \
                and self._symbol_table[next_token.index] in ('rest', 'spread'):
            error_text += self._error_rule_text_creation("Spaces", "Other", "After '...' in rest/spread")
            return int(self._config["Spaces"]["Other"]["After '...' in rest/spread"]), error_text
        elif prev_token.type == Tokens.Operators and prev_token.spec == '...':
            error_text += " after token"
            return 0, error_text

        # Spaces -> Before Keywords [ requires '}' of prev_token) ]
        if prev_token.type == Tokens.Punctuation and prev_token.spec == '}':
            if next_token.type == Tokens.Keyword and next_token.spec == 'else':
                error_text += self._error_rule_text_creation("Spaces", "Before Keywords", "else")
                return int(self._config["Spaces"]["Before Keywords"]["else"]), error_text

            if next_token.type == Tokens.Keyword and next_token.spec == 'while' and where == Scope.Do:
                error_text += self._error_rule_text_creation("Spaces", "Before Keywords", "while")
                return int(self._config["Spaces"]["Before Keywords"]["while"]), error_text

            if next_token.type == Tokens.Keyword and next_token.spec == 'catch':
                error_text += self._error_rule_text_creation("Spaces", "Before Keywords", "catch")
                return int(self._config["Spaces"]["Before Keywords"]["catch"]), error_text

            if next_token.type == Tokens.Keyword and next_token.spec == 'finally':
                error_text += self._error_rule_text_creation("Spaces", "Before Keywords", "finally")
                return int(self._config["Spaces"]["Before Keywords"]["finally"]), error_text

        return -1, error_text + " after token"

    def _check_prev_token_space_need(self, state, prev_token, where):
        error_text = ERROR_SIZE

        # Spaces -> Around operators -> for unary not
        if prev_token.type == Tokens.Operators and prev_token.spec in Scope.AfterUnaryNot.value:
            error_text += self._error_rule_text_creation("Spaces", "Around operators", "After unary 'not' (!) and '!!'")
            return int(self._config["Spaces"]["Around operators"]["After unary 'not' (!) and '!!'"]), error_text

        # Spaces -> Ternary If
        if prev_token.type == Tokens.Operators and prev_token.spec in Scope.AfterQuestMark.value:
            error_text += self._error_rule_text_creation("Spaces", "In Ternary Operator (?:)", "After '?'")
            return int(self._config["Spaces"]["In Ternary Operator (?:)"]["After '?'"]), error_text

        if where == Scope.TernaryIf and prev_token.type == Tokens.Operators and prev_token.spec in Scope.AfterColon.value:
            error_text += self._error_rule_text_creation("Spaces", "In Ternary Operator (?:)", "After ':'")
            return int(self._config["Spaces"]["In Ternary Operator (?:)"]["After ':'"]), error_text

        # Spaces -> Other
        if prev_token.type == Tokens.Punctuation and prev_token.spec in Scope.AfterComma.value:
            error_text += self._error_rule_text_creation("Spaces", "Other", "After comma")
            return int(self._config["Spaces"]["Other"]["After comma"]), error_text

        if where == Scope.PropertyNameValue and prev_token.type == Tokens.Operators and prev_token.spec == ':':
            error_text += self._error_rule_text_creation("Spaces", "Other", "After property name-value operator ':'")
            return int(self._config["Spaces"]["Other"]["After property name-value operator ':'"]), error_text

        if (where == Scope.FuncDeclaration or where == Scope.FuncExpression) \
                and prev_token.type == Tokens.Operators and prev_token.spec == '*':
            error_text += self._error_rule_text_creation("Spaces", "Other", "After '*' in generator")
            return int(self._config["Spaces"]["Other"]["After '*' in generator"]), error_text

        if prev_token.type == Tokens.StartTemplateString or prev_token.type == Tokens.InterpolationEnd:
            error_text = "LEXER ERROR"
            return 0, error_text

        fake_next = Token()
        return self._check_general_space_for_prev_next_token(state, prev_token, fake_next, where)

    def _check_next_token_space_need(self, state, next_token, where):
        error_text = ERROR_SIZE

        # Spaces -> Around operators -> for unary not
        if next_token.type == Tokens.Operators and next_token.spec in Scope.BeforeUnaryNot.value:
            error_text += self._error_rule_text_creation("Spaces", "Around operators", "Before unary 'not' (!) and '!!'")
            return int(self._config["Spaces"]["Around operators"]["Before unary 'not' (!) and '!!'"]), error_text

        # Spaces -> Ternary If
        if next_token.type == Tokens.Operators and next_token.spec in Scope.BeforeQuestMark.value:
            error_text += self._error_rule_text_creation("Spaces", "In Ternary Operator (?:)", "Before '?'")
            return int(self._config["Spaces"]["In Ternary Operator (?:)"]["Before '?'"]), error_text

        if where == Scope.TernaryIf and next_token.type == Tokens.Operators and next_token.spec in Scope.BeforeColon.value:
            error_text += self._error_rule_text_creation("Spaces", "In Ternary Operator (?:)", "Before ':'")
            return int(self._config["Spaces"]["In Ternary Operator (?:)"]["Before ':'"]), error_text

        # Spaces -> Other
        if next_token.type == Tokens.Punctuation and next_token.spec in Scope.BeforeComma.value:
            error_text += self._error_rule_text_creation("Spaces", "Other", "Before comma")
            return int(self._config["Spaces"]["Other"]["Before comma"]), error_text

        if where == Scope.For and next_token.type == Tokens.Punctuation and next_token.spec == ';':
            error_text += self._error_rule_text_creation("Spaces", "Other", "Before 'for' semicolon")
            return int(self._config["Spaces"]["Other"]["Before 'for' semicolon"]), error_text
        elif next_token.type == Tokens.Punctuation and next_token.spec == ';':
            error_text += " after token"
            return 0, error_text
        if where == Scope.PropertyNameValue and next_token.type == Tokens.Operators and next_token.spec == ':':
            error_text += self._error_rule_text_creation("Spaces", "Other", "Before property name-value operator ':'")
            return int(self._config["Spaces"]["Other"]["Before property name-value operator ':'"]), error_text

        if (where == Scope.FuncDeclaration or where == Scope.FuncExpression) \
                and next_token.type == Tokens.Operators and next_token.spec == '*':
            error_text += self._error_rule_text_creation("Spaces", "Other", "Before '*' in generator")
            return int(self._config["Spaces"]["Other"]["Before '*' in generator"]), error_text

        # Spaces -> Before Parenthesis
        if next_token.type == Tokens.Punctuation and next_token.spec == '(':
            if where == Scope.FuncDeclaration:
                error_text += self._error_rule_text_creation("Spaces", "Before Parentheses", "Function declaration")
                return int(self._config["Spaces"]["Before Parentheses"]["Function declaration"]), error_text

            elif where == Scope.FuncCall:
                error_text += self._error_rule_text_creation("Spaces", "Before Parentheses", "Function call")
                return int(self._config["Spaces"]["Before Parentheses"]["Function call"]), error_text

            elif where == Scope.If:
                error_text += self._error_rule_text_creation("Spaces", "Before Parentheses", "if")
                return int(self._config["Spaces"]["Before Parentheses"]["if"]), error_text

            elif where == Scope.For:
                error_text += self._error_rule_text_creation("Spaces", "Before Parentheses", "for")
                return int(self._config["Spaces"]["Before Parentheses"]["for"]), error_text

            elif where == Scope.While:
                error_text += self._error_rule_text_creation("Spaces", "Before Parentheses", "while")
                return int(self._config["Spaces"]["Before Parentheses"]["while"]), error_text

            elif where == Scope.Switch:
                error_text += self._error_rule_text_creation("Spaces", "Before Parentheses", "switch")
                return int(self._config["Spaces"]["Before Parentheses"]["switch"]), error_text

            elif where == Scope.Catch:
                error_text += self._error_rule_text_creation("Spaces", "Before Parentheses", "catch")
                return int(self._config["Spaces"]["Before Parentheses"]["catch"]), error_text

            elif where == Scope.FuncExpression:
                error_text += self._error_rule_text_creation("Spaces", "Before Parentheses", "In function expression")
                return int(self._config["Spaces"]["Before Parentheses"]["In function expression"]), error_text

            elif where == Scope.AsyncFunc:
                error_text += self._error_rule_text_creation("Spaces", "Before Parentheses", "In async arrow function")
                return int(self._config["Spaces"]["Before Parentheses"]["In async arrow function"]), error_text

        # Spaces -> Before Left Brace
        if next_token.type == Tokens.Punctuation and next_token.spec == '{':
            if where == Scope.FuncDeclaration:
                error_text += self._error_rule_text_creation("Spaces", "Before Left Brace", "Function")
                return int(self._config["Spaces"]["Before Left Brace"]["Function"]), error_text

            elif where == Scope.If:
                error_text += self._error_rule_text_creation("Spaces", "Before Left Brace", "if")
                return int(self._config["Spaces"]["Before Left Brace"]["if"]), error_text

            elif where == Scope.Else:
                error_text += self._error_rule_text_creation("Spaces", "Before Left Brace", "else")
                return int(self._config["Spaces"]["Before Left Brace"]["else"]), error_text

            elif where == Scope.For:
                error_text += self._error_rule_text_creation("Spaces", "Before Left Brace", "for")
                return int(self._config["Spaces"]["Before Left Brace"]["for"]), error_text

            elif where == Scope.While:
                error_text += self._error_rule_text_creation("Spaces", "Before Left Brace", "while")
                return int(self._config["Spaces"]["Before Left Brace"]["while"]), error_text

            elif where == Scope.Do:
                error_text += self._error_rule_text_creation("Spaces", "Before Left Brace", "do")
                return int(self._config["Spaces"]["Before Left Brace"]["do"]), error_text

            elif where == Scope.Switch:
                error_text += self._error_rule_text_creation("Spaces", "Before Left Brace", "switch")
                return int(self._config["Spaces"]["Before Left Brace"]["switch"]), error_text

            elif where == Scope.Try:
                error_text += self._error_rule_text_creation("Spaces", "Before Left Brace", "try")
                return int(self._config["Spaces"]["Before Left Brace"]["try"]), error_text

            elif where == Scope.Catch:
                error_text += self._error_rule_text_creation("Spaces", "Before Left Brace", "catch")
                return int(self._config["Spaces"]["Before Left Brace"]["catch"]), error_text

            elif where == Scope.Finally:
                error_text += self._error_rule_text_creation("Spaces", "Before Left Brace", "finally")
                return int(self._config["Spaces"]["Before Left Brace"]["finally"]), error_text

            elif where == Scope.Class:
                error_text += self._error_rule_text_creation("Spaces", "Before Left Brace", "Class")
                return int(self._config["Spaces"]["Before Left Brace"]["Class"]), error_text

        if next_token.spec == ':' and where == Scope.Switch:
            error_text += " after token"
            return 0, error_text

        if next_token.type == Tokens.EndTemplateString or next_token.type == Tokens.InterpolationStart:
            error_text = "LEXER ERROR"
            return 0, error_text

        fake_prev = Token()
        return self._check_general_space_for_prev_next_token(state, fake_prev, next_token, where)

    def _get_check_tokens_result(self, state, prev_token, next_token, where):
        space_number, error_message = self._check_general_space_for_prev_next_token(state, prev_token, next_token, where)
        save_space, save_error = -1, ERROR_SIZE + " after token"
        if space_number == 1:
            return space_number, error_message
        elif space_number == 0:
            save_space, save_error = space_number, error_message
        space_number, error_message = self._check_prev_token_space_need(state, prev_token, where)

        if space_number == 1:
            return space_number, error_message
        elif space_number == 0:
            save_space, save_error = space_number, error_message

        space_number, error_message = self._check_next_token_space_need(state, next_token, where)
        if space_number == 1:
            return space_number, error_message
        elif space_number == 0:
            save_space, save_error = space_number, error_message

        if prev_token.type == Tokens.Operators:
            space_number, error_message = self._check_token_operators(state, prev_token, where)
            if space_number == 1:
                return space_number, error_message
            elif space_number == 0:
                save_space, save_error = space_number, error_message

        if next_token.type == Tokens.Operators:
            space_number, error_message = self._check_token_operators(state, next_token, where)
            if space_number == 1:
                return space_number, error_message
            elif space_number == 0:
                save_space, save_error = space_number, error_message

        if save_space == 0:
            return save_space, save_error

        return 1, save_error

    def _rule_whitespace(self, space_number, enter_number, error_message, error_blank):
        return {Tokens.Space: space_number,
                Tokens.Enter: enter_number,
                "error_message": error_message,
                "error_blank": error_blank}

    def _end_of_file(self, state, pos):
        state.pos = pos + 1
        self._handle_whitespace_between_tokens(state,
                                               self._rule_whitespace(space_number=0,
                                                                     enter_number=(-1, _MAX_BLANK_LINES),
                                                                     error_message=ERROR_SIZE + " after token",
                                                                     error_blank=ERROR_SIZE + RULE_BLANK_MAX))

    def _handle_whitespace_between_tokens2(self, state, whitespace_rule):
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

                while enter_number > 0 and counter[Tokens.Enter] >= 0:
                    cur_pos = index
                    while state.all_tokens[cur_pos].type == Tokens.Tab or \
                            state.all_tokens[cur_pos].type == Tokens.Space:
                        cur_pos += 1
                    was_error = self._handle_indents(state, index, cur_pos, counter[Tokens.Enter] > 0, no_errors)

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
                while counter[Tokens.Enter] >= 0 and index < len(state.all_tokens):
                    cur_pos = index
                    while state.all_tokens[cur_pos].type == Tokens.Tab or state.all_tokens[
                        cur_pos].type == Tokens.Space:
                        cur_pos += 1
                    was_error = self._handle_indents(state, index, cur_pos, counter[Tokens.Enter] > 0, no_errors)
                    if state.all_tokens[cur_pos].type == Tokens.Enter:
                        self._token.append(Token(token_type=Tokens.Enter,
                                                 row=state.all_tokens[cur_pos].row + state.row_offset,
                                                 column=self._next_pos_of_token()))
                        index = cur_pos + 1

                    counter[Tokens.Enter] -= 1
        else:
            if whitespace_rule[Tokens.Enter][0] == -1 and state.all_tokens[index].type == Tokens.Enter:
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

    def _handle_whitespace_between_tokens(self, state, whitespace_rule):
        declaration_start = state.pos
        counter = self._get_next_non_whitespace(state)
        index = declaration_start
        was_good_space = False
        was_bad_space = False
        if state.pos >= len(state.all_tokens):
            return
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

        whitespace_rule[Tokens.Enter] = [whitespace_rule[Tokens.Enter][0] + 1, whitespace_rule[Tokens.Enter][1] + 1]

        if whitespace_rule[Tokens.Enter][0] <= counter[Tokens.Enter] <= whitespace_rule[Tokens.Enter][1] or \
                whitespace_rule[Tokens.Enter][1] < whitespace_rule[Tokens.Enter][0] == counter[Tokens.Enter]:

            if (was_good_space or was_bad_space) and counter[Tokens.Enter] != 0:
                self._invalid_token.append(WrongToken(message=ERROR_SIZE + " in the end of line",
                                                      token=state.all_tokens[declaration_start - 1]))
                if was_good_space:
                    self._token.pop()

            elif counter[Tokens.Enter] == 0:
                if whitespace_rule[Tokens.Space] >= 1 and not was_good_space:
                    self._token.append(Token(token_type=Tokens.Space,
                                             row=state.row_offset + state.all_tokens[declaration_start].row,
                                             column=state.all_tokens[declaration_start].column))
                    self._invalid_token.append(WrongToken(message=whitespace_rule['error_message'],
                                                          token=state.all_tokens[declaration_start - 1]))
                return

            self._token.append(Token(token_type=Tokens.Enter,
                                     row=state.all_tokens[declaration_start].row + state.row_offset,
                                     column=self._next_pos_of_token()))
            index += 1
            counter[Tokens.Enter] -= 1
            if index == len(state.all_tokens):
                return
            while counter[Tokens.Enter] >= 0 and index < len(state.all_tokens):
                cur_pos = index
                while state.all_tokens[cur_pos].type == Tokens.Tab or state.all_tokens[cur_pos].type == Tokens.Space:
                    cur_pos += 1
                was_error = self._handle_indents(state, index, cur_pos, counter[Tokens.Enter] > 0, False)
                if state.all_tokens[cur_pos].type == Tokens.Enter:
                    self._token.append(Token(token_type=Tokens.Enter,
                                             row=state.all_tokens[cur_pos].row + state.row_offset,
                                             column=self._next_pos_of_token()))
                    index = cur_pos + 1

                counter[Tokens.Enter] -= 1
        elif whitespace_rule[Tokens.Enter][0] <= whitespace_rule[Tokens.Enter][1] < counter[Tokens.Enter] or\
                whitespace_rule[Tokens.Enter][1] < whitespace_rule[Tokens.Enter][0] < counter[Tokens.Enter]:

            self._invalid_token.append(WrongToken(message=whitespace_rule['error_blank'],
                                                  token=state.all_tokens[declaration_start - 1]))

            if (was_good_space or was_bad_space) and max(whitespace_rule[Tokens.Enter]) > 0:
                self._invalid_token.append(WrongToken(message=ERROR_SIZE + " in the end of line",
                                                      token=state.all_tokens[declaration_start - 1]))
                if was_good_space:
                    self._token.pop()
            elif max(whitespace_rule[Tokens.Enter]) == 0:
                if whitespace_rule[Tokens.Space] >= 1 and not was_good_space:
                    self._token.append(Token(token_type=Tokens.Space,
                                             row=state.row_offset + state.all_tokens[declaration_start].row,
                                             column=state.all_tokens[declaration_start].column))
                return
                # self._invalid_token.append(WrongToken(message=whitespace_rule['error_message'],
                #                                       token=state.all_tokens[declaration_start - 1]))

            self._token.append(Token(token_type=Tokens.Enter,
                                     row=state.all_tokens[declaration_start].row + state.row_offset,
                                     column=self._next_pos_of_token()))
            index += 1
            if index == len(state.all_tokens):
                return
            counter[Tokens.Enter] -= 1

            max_enter_number = max(whitespace_rule[Tokens.Enter]) - 1
            while max_enter_number >= 0 and index < len(state.all_tokens):
                cur_pos = index
                while state.all_tokens[cur_pos].type == Tokens.Tab or state.all_tokens[cur_pos].type == Tokens.Space:
                    cur_pos += 1
                was_error = self._handle_indents(state, index, cur_pos, counter[Tokens.Enter] > 0, True)
                if state.all_tokens[cur_pos].type == Tokens.Enter and max_enter_number > 0:
                    self._token.append(Token(token_type=Tokens.Enter,
                                             row=state.all_tokens[cur_pos].row + state.row_offset,
                                             column=self._next_pos_of_token()))
                    index = cur_pos + 1
                max_enter_number -= 1
                counter[Tokens.Enter] -= 1

            while counter[Tokens.Enter] >= 0 and index < len(state.all_tokens):
                while state.all_tokens[index].type == Tokens.Tab or state.all_tokens[index].type == Tokens.Space:
                    index += 1
                counter[Tokens.Enter] -= 1
                state.row_offset -= 1
        elif counter[Tokens.Enter] < whitespace_rule[Tokens.Enter][0]:
            if was_good_space or was_bad_space:
                self._invalid_token.append(WrongToken(message=ERROR_SIZE + " in the end of line",
                                                      token=state.all_tokens[declaration_start - 1]))
                if was_good_space:
                    self._token.pop()

                if counter[Tokens.Enter] != 0:
                    index += 1
                    if index == len(state.all_tokens):
                        return

            self._invalid_token.append(WrongToken(message=whitespace_rule['error_blank'],
                                                  token=state.all_tokens[declaration_start - 1]))

            spaces_row = [Token(token_type=Tokens.Enter,
                                row=state.all_tokens[declaration_start].row + state.row_offset,
                                column=self._next_pos_of_token())]
            if self._config['Tabs and Indents']['Keep indents on empty lines']:
                tab_size = self._config['Tabs and Indents']['Tab size']
                indent_size = self._config['Tabs and Indents']['Indent']
                cont_indent_size = self._config['Tabs and Indents']['Continuation indent']
                total_size_indent = indent_size * state.indent + cont_indent_size * state.continuous_indent
                number_of_tabs = total_size_indent // tab_size
                number_of_spaces = total_size_indent - number_of_tabs * tab_size

                if self._config['Tabs and Indents']['Use tab character']:
                    for i in range(0, number_of_tabs):
                        spaces_row.append(Token(token_type=Tokens.Tab,
                                                row=state.row_offset + state.all_tokens[declaration_start - 1].row,
                                                column=tab_size * i))
                    for i in range(0, number_of_spaces):
                        spaces_row.append(Token(token_type=Tokens.Space,
                                                row=state.row_offset + state.all_tokens[declaration_start - 1].row,
                                                column=i))
                else:
                    number_of_spaces = total_size_indent
                    for i in range(0, number_of_spaces):
                        spaces_row.append(Token(token_type=Tokens.Space,
                                                row=state.row_offset + state.all_tokens[declaration_start - 1].row,
                                                column=i))
            while whitespace_rule[Tokens.Enter][0] > 0:
                whitespace_rule[Tokens.Enter][0] -= 1
                self._token.extend(spaces_row)

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
            while index < end:
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

            if not was_error and (number_of_tabs > 0 or number_of_spaces > 0 or index != end):
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
            index = start
            was_error = False
            number_of_spaces = total_size_indent
            while index < end:
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

            if not was_error and (number_of_spaces > 0 or index != end):
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

    def _get_next_token(self, state, check_end=True):
        start_pos = state.pos
        state.pos += 1

        whitespace_counter = self._get_next_non_whitespace(state)
        if state.pos >= len(state.all_tokens):
            state.pos = start_pos
            if check_end:
                self._end_of_file(state, start_pos)
            return Token()

        ans = state.all_tokens[state.pos]
        state.pos = start_pos
        return ans

    def _get_prev_token(self, state):
        start_pos = state.pos
        state.pos -= 1

        while state.pos >= 0 and is_whitespace_token(state.all_tokens[state.pos].type):
            state.pos -= 1

        if state.pos < 0:
            state.pos = start_pos
            return Token()

        ans = state.all_tokens[state.pos]
        state.pos = start_pos
        return ans

    def _handle_keywords(self, state, where):
        current_token = state.all_tokens[state.pos]

        if current_token.spec == 'function':
            self._handle_function_creation(state)
        elif current_token.spec == 'yield':
            self._handle_yield(state)
        elif current_token.spec == 'async':
            self._handle_async(state)
        elif current_token.spec == 'if':
            self._handle_if(state)
        elif current_token.spec == 'for':
            self._handle_for_while(state, Scope.For)
        elif current_token.spec == 'while':
            self._handle_for_while(state, Scope.While)
        elif current_token.spec == 'do':
            self._handle_do_while(state)
        elif current_token.spec == 'try':
            self._handle_try_catch(state)
        elif current_token.spec == 'switch':
            self._handle_switch(state)
        else:
            self._token.append(state.all_tokens[state.pos])

    def _handle_identifier_cases(self, state, where):

        self._token.append(state.all_tokens[state.pos])
        prev_token = state.all_tokens[state.pos]

        declaration_start = state.pos
        current_token = self._get_next_token(state)
        if current_token.is_fake():
            return

        # func call
        if current_token.type == Tokens.Punctuation and current_token.spec == '(':
            where = Scope.FuncCall

            space_number, error_text = self._get_check_tokens_result(state, prev_token, current_token, where)
            self._handle_bkt(state, space_number, error_text, declaration_start, current_token,
                             _MAX_BLANK_LINES, where, ')')
        elif current_token.type == Tokens.Punctuation and current_token.spec == '[':
            where = Scope.IndexAccessBrackets
            space_number, error_text = self._get_check_tokens_result(state, prev_token, current_token, where)

            state.pos += 1

            self._handle_whitespace_between_tokens(
                state,
                self._rule_whitespace(space_number=0,
                                      enter_number=(-1, _MAX_BLANK_LINES),
                                      error_message=error_text,
                                      error_blank=ERROR_SIZE + RULE_BLANK_MAX))

            self._token.append(state.all_tokens[state.pos])
            prev_token = state.all_tokens[state.pos]
            current_token = self._get_next_token(state)
            if current_token.is_fake():
                return


            space_number, error_text = self._get_check_tokens_result(state, prev_token, current_token, where)
            state.pos += 1
            self._handle_whitespace_between_tokens(
                state,
                self._rule_whitespace(space_number=space_number,
                                      enter_number=(-1, _MAX_BLANK_LINES),
                                      error_message=error_text,
                                      error_blank=ERROR_SIZE + RULE_BLANK_MAX))

            prev_outer_scope = state.outer_scope
            state.outer_scope = where

            current_token = self._get_next_token(state)
            if current_token.is_fake():
                return

            first_open = False
            while state.pos < len(state.all_tokens):
                current_token = state.all_tokens[state.pos]
                if current_token.spec == ']':
                    self._token.append(state.all_tokens[state.pos])
                    break
                else:
                    if current_token.spec == '[' and not first_open or self._get_next_token(state, False).spec == ']':
                        self._parse_next_token(state, where)
                        first_open = True
                    else:
                        self._parse_next_token(state, Scope.GeneralScope)
            state.outer_scope = prev_outer_scope

    def _handle_punctuation(self, state, where):
        current_token = state.all_tokens[state.pos]
        if current_token.spec == '[' and where != Scope.IndexAccessBrackets and where != Scope.ArrayBrackets:
            where = Scope.ArrayBrackets
            prev_outer_scope = state.outer_scope
            state.outer_scope = where
            current_token = self._get_next_token(state)
            if current_token.is_fake():
                return

            first_open = False
            while state.pos < len(state.all_tokens):
                current_token = state.all_tokens[state.pos]
                if current_token.spec == ']':
                    self._token.append(state.all_tokens[state.pos])
                    break
                else:
                    if current_token.spec == '[' and not first_open or self._get_next_token(state, False).spec == ']':
                        self._parse_next_token(state, where)
                        first_open = True
                    else:
                        self._parse_next_token(state, Scope.GeneralScope)
            state.outer_scope = prev_outer_scope
            '''
            elif current_token.spec == '{' and state.outer_scope == Scope.GeneralScope:
                where = Scope.ObjectLiteralBrace
                prev_outer_scope = state.outer_scope
                state.outer_scope = where
                current_token = self._get_next_token(state)
                if current_token.is_fake():
                    return
    
                first_open = False
                while state.pos < len(state.all_tokens):
                    current_token = state.all_tokens[state.pos]
                    if current_token.spec == '}':
                        self._token.append(state.all_tokens[state.pos])
                        break
                    else:
                        if current_token.spec == '{' and not first_open or self._get_next_token(state, False).spec == '}':
                            self._parse_next_token(state, where)
                            first_open = True
                        else:
                            self._parse_next_token(state, Scope.PropertyNameValue)
                state.outer_scope = prev_outer_scope
            '''
        else:
            self._token.append(state.all_tokens[state.pos])

    def _handle_operators(self, state):
        current_token = state.all_tokens[state.pos]
        if current_token.spec == '?':
            where = Scope.TernaryIf

            self._token.append(current_token)

            self._check_space_to_next_token(state, where)

            was_colon = False
            while state.pos < len(state.all_tokens):
                current_token = state.all_tokens[state.pos]
                if current_token.spec == ';':
                    self._token.append(current_token)
                    break
                if current_token.spec == ':':
                    was_colon += 1
                self._parse_next_token(state, where)
        else:
            self._token.append(current_token)

    def _handle_function_creation(self, state):
        where = Scope.FuncDeclaration

        self._token.append(state.all_tokens[state.pos])
        prev_token = state.all_tokens[state.pos]

        declaration_start = state.pos
        current_token = self._get_next_token(state)
        if current_token.is_fake():
            return

        was_star = False
        if current_token.type == Tokens.Operators and current_token.spec == '*':
            was_star = True

            space_number, error_text = self._get_check_tokens_result(state, prev_token, current_token, where)

            state.pos += 1
            self._handle_whitespace_between_tokens(
                state,
                self._rule_whitespace(space_number=space_number,
                                      enter_number=(-1, -1),
                                      error_message=error_text,
                                      error_blank=ERROR_SIZE + " after token"))
            declaration_start = state.pos
            self._token.append(state.all_tokens[state.pos])
            prev_token = state.all_tokens[state.pos]

            current_token = self._get_next_token(state)
            if current_token.is_fake():
                return

        was_identifier = False
        if current_token.type == Tokens.Identifier:
            was_identifier = True
            space_number, error_text = self._get_check_tokens_result(state, prev_token, current_token, where)
            if was_star:
                enter_number = (-1, -1)
            else:
                enter_number = (-1, _MAX_BLANK_LINES)

            state.pos += 1
            self._handle_whitespace_between_tokens(
                state,
                self._rule_whitespace(space_number=space_number,
                                      enter_number=enter_number,
                                      error_message=error_text,
                                      error_blank=ERROR_SIZE + " after token"))
            declaration_start = state.pos
            self._token.append(state.all_tokens[state.pos])
            prev_token = state.all_tokens[state.pos]

            current_token = self._get_next_token(state)
            if current_token.is_fake():
                return

        if current_token.type == Tokens.Punctuation and current_token.spec == '(':
            if not was_identifier:
                where = Scope.FuncExpression

            space_number, error_text = self._get_check_tokens_result(state, prev_token, current_token, where)
            self._handle_bkt(state, space_number, error_text, declaration_start, current_token,
                             _MAX_BLANK_LINES, where, ')')
        else:
            return

        if state.pos >= len(state.all_tokens):
            return

        finish_parentheses = state.pos
        prev_token = state.all_tokens[finish_parentheses]
        current_token = self._get_next_token(state)
        if current_token.is_fake():
            return

        if current_token.type == Tokens.Punctuation and current_token.spec == '{':
            space_number, error_text = self._get_check_tokens_result(state, prev_token, current_token, where)
            self._handle_bkt(state, space_number, error_text, finish_parentheses, current_token,
                             _MAX_BLANK_LINES, Scope.GeneralScope, '}')
        else:
            return

    def _handle_yield(self, state):

        where = Scope.FuncDeclaration

        self._token.append(state.all_tokens[state.pos])
        prev_token = state.all_tokens[state.pos]

        declaration_start = state.pos
        current_token = self._get_next_token(state)
        if current_token.is_fake():
            return

        was_star = False
        if current_token.type == Tokens.Operators and current_token.spec == '*':
            was_star = True

            space_number, error_text = self._get_check_tokens_result(state, prev_token, current_token, where)

            state.pos += 1
            self._handle_whitespace_between_tokens(
                state,
                self._rule_whitespace(space_number=space_number,
                                      enter_number=(-1, -1),
                                      error_message=error_text,
                                      error_blank=ERROR_SIZE + " after token"))
            declaration_start = state.pos
            self._token.append(state.all_tokens[state.pos])
            prev_token = state.all_tokens[state.pos]

            current_token = self._get_next_token(state)
            if current_token.is_fake():
                return

        was_identifier = False
        if current_token.type == Tokens.Identifier:
            was_identifier = True
            space_number, error_text = self._get_check_tokens_result(state, prev_token, current_token, where)
            if was_star:
                enter_number = (-1, -1)
            else:
                enter_number = (-1, _MAX_BLANK_LINES)

            state.pos += 1
            self._handle_whitespace_between_tokens(
                state,
                self._rule_whitespace(space_number=space_number,
                                      enter_number=enter_number,
                                      error_message=error_text,
                                      error_blank=ERROR_SIZE + " after token"))
            declaration_start = state.pos
            self._token.append(state.all_tokens[state.pos])
            prev_token = state.all_tokens[state.pos]

            current_token = self._get_next_token(state)
            if current_token.is_fake():
                return

        if current_token.type == Tokens.Punctuation and current_token.spec == '(':
            if not was_identifier:
                where = Scope.FuncExpression

            space_number, error_text = self._get_check_tokens_result(state, prev_token, current_token, where)
            self._handle_bkt(state, space_number, error_text, declaration_start, current_token,
                             _MAX_BLANK_LINES, where, ')')
        else:
            return

        if state.pos >= len(state.all_tokens):
            return

    def _handle_async(self, state):
        where = Scope.AsyncFunc

        self._token.append(state.all_tokens[state.pos])
        prev_token = state.all_tokens[state.pos]

        declaration_start = state.pos
        current_token = self._get_next_token(state)
        if current_token.is_fake():
            return

        if current_token.type == Tokens.Punctuation and current_token.spec == '(':
            space_number, error_text = self._get_check_tokens_result(state, prev_token, current_token, where)
            self._handle_bkt(state, space_number, error_text, declaration_start, current_token,
                             _MAX_BLANK_LINES, Scope.FuncDeclaration, ')')
        else:
            return

        finish_parentheses = state.pos
        prev_token = state.all_tokens[finish_parentheses]
        current_token = self._get_next_token(state)
        if current_token.is_fake():
            return

        if current_token.type == Tokens.Operators and current_token.spec == '=>':

            space_number, error_text = self._get_check_tokens_result(state, prev_token, current_token, where)

            state.continuous_indent += 1
            state.pos += 1
            self._handle_whitespace_between_tokens(
                state,
                self._rule_whitespace(space_number=space_number,
                                      enter_number=(-1, _MAX_BLANK_LINES),
                                      error_message=error_text,
                                      error_blank=ERROR_SIZE + " after token"))

            state.continuous_indent -= 1
            declaration_start = state.pos
            self._token.append(state.all_tokens[state.pos])
            prev_token = state.all_tokens[state.pos]

            current_token = self._get_next_token(state)
            if current_token.is_fake():
                return
        else:
            return
        if state.pos >= len(state.all_tokens):
            return

        finish_parentheses = state.pos
        prev_token = state.all_tokens[finish_parentheses]
        current_token = self._get_next_token(state)
        if current_token.is_fake():
            return

        if current_token.type == Tokens.Punctuation and current_token.spec == '{':
            space_number, error_text = self._get_check_tokens_result(state, prev_token, current_token, where)
            self._handle_bkt(state, space_number, error_text, finish_parentheses, current_token,
                             _MAX_BLANK_LINES, Scope.GeneralScope, '}')
        else:
            return

    def _handle_try_catch(self, state):
        where = Scope.Try

        self._token.append(state.all_tokens[state.pos])
        prev_token = state.all_tokens[state.pos]

        declaration_start = state.pos
        next_token = self._get_next_token(state)
        if next_token.is_fake():
            return

        if next_token.type == Tokens.Punctuation and next_token.spec == '{':
            space_number, error_text = self._get_check_tokens_result(state, prev_token, next_token, where)
            self._handle_bkt(state, space_number, error_text, declaration_start, next_token,
                             _MAX_BLANK_LINES, Scope.GeneralScope, '}')
        else:
            return

        if state.pos >= len(state.all_tokens):
            return

        finish_brace = state.pos
        prev_token = state.all_tokens[finish_brace]
        next_token = self._get_next_token(state)
        if next_token.is_fake():
            return

        if not (next_token.type == Tokens.Keyword and next_token.spec == 'catch'):
            return

        where = Scope.Catch

        self._check_space_to_next_token(state, where, (-1, -1))
        self._token.append(next_token)

        next_token = self._get_next_token(state)
        if next_token.is_fake():
            return

        if next_token.type == Tokens.Punctuation and next_token.spec == '(':
            space_number, error_text = self._get_check_tokens_result(state, prev_token, next_token, where)
            self._handle_bkt(state, space_number, error_text, declaration_start, next_token,
                             _MAX_BLANK_LINES, where, ')')
        else:
            return

        if state.pos >= len(state.all_tokens):
            return

        finish_parentheses = state.pos
        prev_token = state.all_tokens[finish_parentheses]
        next_token = self._get_next_token(state)
        if next_token.is_fake():
            return

        if next_token.type == Tokens.Punctuation and next_token.spec == '{':
            space_number, error_text = self._get_check_tokens_result(state, prev_token, next_token, where)
            self._handle_bkt(state, space_number, error_text, finish_parentheses, next_token,
                             _MAX_BLANK_LINES, Scope.GeneralScope, '}')
        else:
            return

        if state.pos >= len(state.all_tokens):
            return
        finish_brace = state.pos
        prev_token = state.all_tokens[finish_brace]
        next_token = self._get_next_token(state)
        if next_token.is_fake():
            return

        if next_token.type == Tokens.Keyword and next_token.spec == 'finally':
            where = Scope.Finally
            self._check_space_to_next_token(state, where, (-1, -1))

            self._token.append(next_token)

            next_token = self._get_next_token(state)
            if next_token.is_fake():
                return
            if next_token.type == Tokens.Punctuation and next_token.spec == '{':
                space_number, error_text = self._get_check_tokens_result(state, prev_token, next_token, where)
                self._handle_bkt(state, space_number, error_text, finish_parentheses, next_token,
                                 _MAX_BLANK_LINES, Scope.GeneralScope, '}')
            else:
                return

    def _handle_bkt(self, state, space_number, rule_error_text, declaration_start, current_token,
                    max_blank_lines, where, bkt_type):

        state.pos += 1
        if bkt_type == '}':
            enter_number = (-1, -1)
        else:
            enter_number = (-1, max_blank_lines)

        self._handle_whitespace_between_tokens(
            state,
            self._rule_whitespace(space_number=space_number,
                                  enter_number=enter_number,
                                  error_message=rule_error_text,
                                  error_blank=ERROR_SIZE + RULE_BLANK_MAX))

        current_token = self._get_next_token(state)
        if current_token.is_fake():
            return

        while state.pos < len(state.all_tokens):
            current_token = state.all_tokens[state.pos]
            if current_token.spec == bkt_type:
                self._token.append(state.all_tokens[state.pos])
                break
            else:
                self._parse_next_token(state, where)

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

    def _handle_if(self, state):
        where = Scope.If

        self._token.append(state.all_tokens[state.pos])
        prev_token = state.all_tokens[state.pos]

        declaration_start = state.pos
        next_token = self._get_next_token(state)
        if next_token.is_fake():
            return

        if next_token.type == Tokens.Punctuation and next_token.spec == '(':
            space_number, error_text = self._get_check_tokens_result(state, prev_token, next_token, where)
            self._handle_bkt(state, space_number, error_text, declaration_start, next_token,
                             _MAX_BLANK_LINES, where, ')')
        else:
            return

        if state.pos >= len(state.all_tokens):
            return

        finish_parentheses = state.pos
        prev_token = state.all_tokens[finish_parentheses]
        next_token = self._get_next_token(state)
        if next_token.is_fake():
            return

        if next_token.type == Tokens.Punctuation and next_token.spec == '{':
            space_number, error_text = self._get_check_tokens_result(state, prev_token, next_token, where)
            self._handle_bkt(state, space_number, error_text, finish_parentheses, next_token,
                             _MAX_BLANK_LINES, Scope.GeneralScope, '}')
        elif next_token.type == Tokens.Keyword and not next_token.spec == 'else' \
                or next_token.type == Tokens.Identifier:
            space_number, error_text = self._get_check_tokens_result(state, prev_token, next_token, where)
            self._handle_one_liner(state, space_number, error_text, finish_parentheses, next_token,
                                   _MAX_BLANK_LINES, Scope.GeneralScope)
        else:
            return

        if state.pos >= len(state.all_tokens):
            return
        finish_brace = state.pos
        prev_token = state.all_tokens[finish_brace]
        next_token = self._get_next_token(state)
        if next_token.is_fake():
            return

        if next_token.type == Tokens.Keyword and next_token.spec == 'else':
            where = Scope.Else
            if prev_token.spec == '}':
                self._check_space_to_next_token(state, where, (-1, -1))
            else:
                self._check_space_to_next_token(state, where, (0, 1))

            self._token.append(next_token)

            next_token = self._get_next_token(state)
            if next_token.is_fake():
                return
            if next_token.type == Tokens.Punctuation and next_token.spec == '{':
                space_number, error_text = self._get_check_tokens_result(state, prev_token, next_token, where)
                self._handle_bkt(state, space_number, error_text, finish_parentheses, next_token,
                                 _MAX_BLANK_LINES, Scope.GeneralScope, '}')
            elif next_token.type == Tokens.Keyword and not next_token.spec == 'else' \
                    or next_token.type == Tokens.Identifier:
                space_number, error_text = self._get_check_tokens_result(state, prev_token, next_token, where)
                self._handle_one_liner(state, space_number, error_text, finish_parentheses, next_token,
                                       _MAX_BLANK_LINES, Scope.GeneralScope)
            else:
                return

    def _handle_one_liner(self, state, space_number, rule_error_text, declaration_start, current_token,
                          max_blank_lines, where):

        state.pos += 1
        state.indent += 1
        self._handle_whitespace_between_tokens(
            state,
            self._rule_whitespace(space_number=space_number,
                                  enter_number=(-1, _MAX_BLANK_LINES),
                                  error_message=rule_error_text,
                                  error_blank=ERROR_SIZE + RULE_BLANK_MAX))

        was_comma = False
        while state.pos < len(state.all_tokens):
            current_token = state.all_tokens[state.pos]
            next_token = self._get_next_token(state, False)
            if (next_token.type == Tokens.Punctuation and next_token.spec == ',' or
                    current_token.type == Tokens.Punctuation and current_token.spec == ',') and \
                    where != Scope.FuncCall and where != Scope.FuncDeclaration and where != Scope.AsyncFunc and \
                    where.value > Scope.Do.value:
                was_comma = True
            prev_pos = state.pos
            state.pos += 1
            counter = self._get_next_non_whitespace(state)
            state.pos = prev_pos
            if not was_comma and next_token != current_token and counter[Tokens.Enter] > 0 or next_token.is_fake() \
                    or next_token.type == Tokens.Keyword and next_token.spec == 'else' and where != Scope.Else \
                    or current_token.spec == ';':
                self._token.append(state.all_tokens[state.pos])
                break
            elif current_token.type == Tokens.Keyword and current_token.spec is not None \
                    and current_token.spec in ('function', 'for', 'do', 'while', 'if', 'class'):
                self._parse_next_token(state, Scope.GeneralScope, True)
                break
            else:
                self._parse_next_token(state, Scope.GeneralScope)
                was_comma = False

        state.indent = max(state.indent - 1, 0)

    def _handle_for_while(self, state, scope):
        where = scope

        self._token.append(state.all_tokens[state.pos])
        prev_token = state.all_tokens[state.pos]

        declaration_start = state.pos
        next_token = self._get_next_token(state)
        if next_token.is_fake():
            return

        if next_token.type == Tokens.Punctuation and next_token.spec == '(':
            space_number, error_text = self._get_check_tokens_result(state, prev_token, next_token, where)
            self._handle_bkt(state, space_number, error_text, declaration_start, next_token,
                             _MAX_BLANK_LINES, where, ')')
        else:
            return

        if state.pos >= len(state.all_tokens):
            return

        finish_parentheses = state.pos
        prev_token = state.all_tokens[finish_parentheses]
        next_token = self._get_next_token(state)
        if next_token.is_fake():
            return

        if next_token.type == Tokens.Punctuation and next_token.spec == '{':
            space_number, error_text = self._get_check_tokens_result(state, prev_token, next_token, where)
            self._handle_bkt(state, space_number, error_text, finish_parentheses, next_token,
                             _MAX_BLANK_LINES, Scope.GeneralScope, '}')
        elif next_token.type == Tokens.Keyword and not next_token.spec == 'else' \
                or next_token.type == Tokens.Identifier:
            space_number, error_text = self._get_check_tokens_result(state, prev_token, next_token, where)
            self._handle_one_liner(state, space_number, error_text, finish_parentheses, next_token,
                                   _MAX_BLANK_LINES, Scope.GeneralScope)
        else:
            return

    def _handle_do_while(self, state):
        where = Scope.Do

        self._token.append(state.all_tokens[state.pos])
        prev_token = state.all_tokens[state.pos]

        declaration_start = state.pos
        next_token = self._get_next_token(state)
        if next_token.is_fake():
            return

        if next_token.type == Tokens.Punctuation and next_token.spec == '{':
            space_number, error_text = self._get_check_tokens_result(state, prev_token, next_token, where)
            self._handle_bkt(state, space_number, error_text, declaration_start, next_token,
                             _MAX_BLANK_LINES, Scope.GeneralScope, '}')
        else:
            return

        if state.pos >= len(state.all_tokens):
            return

        finish_brace = state.pos
        prev_token = state.all_tokens[finish_brace]
        next_token = self._get_next_token(state)
        if next_token.is_fake():
            return

        if not (next_token.type == Tokens.Keyword and next_token.spec == 'while'):
            return

        where = Scope.While

        self._check_space_to_next_token(state, where, (-1, -1))
        self._token.append(next_token)

        next_token = self._get_next_token(state)
        if next_token.is_fake():
            return

        if next_token.type == Tokens.Punctuation and next_token.spec == '(':
            space_number, error_text = self._get_check_tokens_result(state, prev_token, next_token, where)
            self._handle_bkt(state, space_number, error_text, declaration_start, next_token,
                             _MAX_BLANK_LINES, where, ')')
        else:
            return

    def _handle_switch(self, state):
        where = Scope.Switch

        self._token.append(state.all_tokens[state.pos])
        prev_token = state.all_tokens[state.pos]

        declaration_start = state.pos
        next_token = self._get_next_token(state)
        if next_token.is_fake():
            return

        if next_token.type == Tokens.Punctuation and next_token.spec == '(':
            space_number, error_text = self._get_check_tokens_result(state, prev_token, next_token, where)
            self._handle_bkt(state, space_number, error_text, declaration_start, next_token,
                             _MAX_BLANK_LINES, where, ')')
        else:
            return

        if state.pos >= len(state.all_tokens):
            return

        finish_parentheses = state.pos
        prev_token = state.all_tokens[finish_parentheses]
        next_token = self._get_next_token(state)
        if next_token.is_fake():
            return

        if next_token.type == Tokens.Punctuation and next_token.spec == '{':
            space_number, error_text = self._get_check_tokens_result(state, prev_token, next_token, where)
            self._handle_switch_bkt(state, space_number, error_text, finish_parentheses, next_token,
                                    _MAX_BLANK_LINES, where, '}')
        else:
            return

    def _handle_switch_bkt(self, state, space_number, rule_error_text, declaration_start, current_token,
                           max_blank_lines, where, bkt_type):

        state.pos += 1
        enter_number = (-1, -1)
        self._handle_whitespace_between_tokens(
            state,
            self._rule_whitespace(space_number=space_number,
                                  enter_number=enter_number,
                                  error_message=rule_error_text,
                                  error_blank=ERROR_SIZE + RULE_BLANK_MAX))

        current_token = self._get_next_token(state)
        if current_token.is_fake():
            return
        first_case = True
        last = None
        while state.pos < len(state.all_tokens):
            current_token = state.all_tokens[state.pos]
            next_token = self._get_next_token(state, False)
            if current_token.spec == ':':
                state.indent += 1
                last = ':'
            if next_token.spec == 'case':
                if not first_case:
                    state.indent -= 1
                else:
                    first_case = False
                last = 'case'
            if next_token.spec == bkt_type:
                if last == ':':
                    state.indent -= 1
                self._parse_next_token(state, where)
                self._token.append(state.all_tokens[state.pos])
                break
            else:
                self._parse_next_token(state, where)

    def print_all_tokens(self, file_name):
        with open(file_name, 'w') as f:
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

    def print_log(self, file_name):
        with open("log.txt", "a") as f:
            original_stdout = sys.stdout
            sys.stdout = f
            print('##########-----------' + file_name + '-----------##########')

            print('------------------------error format------------------------')
            for tok in self._invalid_token:
                print(tok, end=' ')
                if tok.token.index is not None:
                    print('|| Token value: ' + str(tok.token.index) + ') |' + self._symbol_table[tok.token.index] + '|')
                else:
                    print('')
            if len(self._invalid_token) == 0:
                print("No format errors")

            print('------------------------lexer error------------------------')
            for tok in self._lexer_error_list:
                print(tok, end=' ')
                if tok.token.index is not None:
                    print('|| Token value: ' + str(tok.token.index) + ') |' + self._symbol_table[tok.token.index] + '|')
                else:
                    print('')

            if len(self._lexer_error_list) == 0:
                print("No lexer errors")
            print('\n\n\n')
            sys.stdout = original_stdout


def _get_dirs_from_path(my_path):
    return [f for f in listdir(my_path) if not isfile(join(my_path, f))]


def _get_js_files_from_path(my_path):
    all_files = [f for f in listdir(my_path) if isfile(join(my_path, f))]
    js_files = []
    for f in all_files:
        f_name, f_ext = splitext(f)
        if f_ext == '.js':
            js_files.append(f)
    return js_files


def _get_result(file_name, conf_name, action_type):
    formatter = JsFormatter()
    formatter.set_up_config(conf_name)
    formatter.process_js_file(file_name)
    if action_type == '-v' or action_type == '--verify':
        formatter.print_log(file_name)
        print("Done verify of " + file_name + "")
    elif action_type == '-f' or action_type == '--format':
        formatter.print_all_tokens(file_name)
        print("Done format of " + file_name + "")
    del formatter


def _check_files_in_dir(my_path, conf_name, action_type):
    js_files = _get_js_files_from_path(my_path)
    for js_file in js_files:
        _get_result(join(my_path, js_file), conf_name, action_type)


def _check_rec(my_path, conf_name, action_type):
    _check_files_in_dir(my_path, conf_name, action_type)

    dirs = _get_dirs_from_path(my_path)
    for dir in dirs:
        _check_rec(join(my_path, dir), conf_name, action_type)


if __name__ == '__main__':
    if os.path.exists("log.txt"):
        os.remove("log.txt")
    if sys.argv[1] == '-h' or sys.argv[1] == '--help':
        print("Basic commands:")
        print("\t-h, --help\t\t\t\t: help menu")
        print("\t-v, --verify template file -(p|d|f) /..\t: verify your files(as output log.txt file);")
        print("\t\t\t\t\t\t  template file - configuration file for JS(as default take: config/config.json);")
        print("\t\t\t\t\t\t  /.. - path to project directory or file")

        print("\t-f, --format template file -(p|d|f) /..\t: format your files(as output log.txt file);")
        print("\t\t\t\t\t\t  template file - configuration file for JS(as default take: config/config.json);")
        print("\t\t\t\t\t\t  /.. - path to project directory or file")
    elif len(sys.argv) == 5 and sys.argv[3] == '-p':
        _check_rec(sys.argv[4], sys.argv[2], sys.argv[1])
    elif len(sys.argv) == 5 and sys.argv[3] == '-d':
        _check_files_in_dir(sys.argv[4], sys.argv[2], sys.argv[1])
    elif len(sys.argv) == 5 and sys.argv[3] == '-f':
        _get_result(sys.argv[4], sys.argv[2], sys.argv[1])
    else:
        print("Call help menu (-h, --help) for more details")
