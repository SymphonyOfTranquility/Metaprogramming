def is_number(c):
    return c in "01233456789"


def is_symbol(c):
    return 'a' <= c <= 'z' or 'A' <= c <= 'Z' or c == '_'


def is_dot(c):
    return c == '.'


def is_whitespace(c):
    return c == ' ' or c == '\t' or c == '\n'


def is_punctuation(c):
    return c in ";,[](){}"


def is_operation(c):
    return c in "+-*/%^|&=<>!?:~."


def is_comment(c1, c2):
    return c1 == '/' and (c2 == '/' or c2 == '*')


def is_word(c):
    return is_symbol(c) or is_number(c)


def is_string(c):
    return c == '\'' or c == '"'


def is_correct_after_number(c):
    return is_punctuation(c) or is_whitespace(c) or is_operation(c)


def is_hex(c):
    return c in "0123456789AaBbCcDdEeFf"


def is_binary(c):
    return c in "01"


def is_octal(c):
    return c in "01234567"


def is_down_dash(c):
    return c == '_'


def is_e(c):
    return c in "Ee"


def is_nonnormal_start(state, check_func, type_letter):
    if state.line[state.column] == '0':
        if state.column + 1 < len(state.line) and state.line[state.column+1] in type_letter:
            if state.column + 2 < len(state.line):
                if check_func(state.line[state.column+2]):
                    return 1
            return 0
    return -1


def is_dollar(c):
    return c == '$'
