tokens = {
    "whitespace": (' ', '\t', '\n'),
    "comment": ('//', '/* */', '#!'),
    "keyword": ('await', 'break', 'case', 'catch', 'class', 'const', 'continue', 'debugger', 'default', 'delete', 'do',
                'else', 'enum', 'export', 'extends', 'finally', 'for', 'function', 'if', 'import', 'implements', 'in',
                'instanceof', 'interface', 'let', 'new', 'package', 'private', 'protected', 'public', 'return',
                'static', 'super', 'switch', 'this', 'throw', 'try', 'typeof', 'var', 'void', 'while', 'with', 'yield'),
    "const_literal": ('null', 'true', 'false'),
    "number_literal": ('decimal_int', 'decimal_float', "binary", 'octal', 'hexadecimal', 'bigint'),
    "string_literal": ('\'\'', '""', '``'),
    "operator": ('=',
                 '?', ':',
                 '||', '&&', '|', '^', '&',
                 '==', '!=', '===', '!==',
                 '<', '<=', '>=', '>',
                 '<<', '>>', '>>>',
                 '+', '-', '*', '/', '%',
                 '!', '~', '++', '--',
                 '.'),
    "punctuation": (';', ',', '[', ']', '{', '}', '(', ')'),
    "identifier": 'identifier',
    "invalid": 'invalid'
}

token_names = {
    "whitespace": ('space', 'tab', 'new_line'),
    "comment": ('single_line_comment', 'multi_line_comment'),
    "keyword": ('await', 'break', 'case', 'catch', 'class', 'const', 'continue', 'debugger', 'default', 'delete', 'do',
                'else', 'enum', 'export', 'extends', 'finally', 'for', 'function', 'if', 'import', 'implements', 'in',
                'instanceof', 'interface', 'let', 'new', 'package', 'private', 'protected', 'public', 'return',
                'static', 'super', 'switch', 'this', 'throw', 'try', 'typeof', 'var', 'void', 'while', 'with', 'yield'),
    "const_literal": ('null', 'true', 'false'),
    "number_literal": ('decimal_int', 'decimal_float', "binary", 'octal', 'hexadecimal', 'bigint'),
    "string_literal": ('single_quote', 'double_quote', 'single_other_quote'),
    "operator": ('assignment',
                 'quest_mark', 'colon',
                 'or_symb', 'and_symb', 'or_bitwise', 'xor_bitwise', 'and_bitwise',
                 'equal', 'not_equal', 'identical', 'not_identical',
                 '<', '<=', '>=', '>',
                 '<<', '>>', '>>>',
                 '+', '-', '*', '/', '%',
                 '!', '~', '++', '--',
                 '.'),
    "punctuation": (';', ',', '[', ']', '{', '}', '(', ')'),
    "identifier": 'identifier',
    "invalid": 'invalid'
}


from enum import Enum


class Tokens(Enum):
    Space = ' '
    Tab = '\t'
    Enter = '\n'

    SingleLineComment = '//'
    MultiLineComment = '/*'

    Keyword = ('await', 'break', 'case', 'catch', 'class', 'const', 'continue', 'debugger', 'default', 'delete', 'do',
               'else', 'enum', 'export', 'extends', 'finally', 'for', 'function', 'if', 'import', 'implements', 'in',
               'instanceof', 'interface', 'let', 'new', 'package', 'private', 'protected', 'public', 'return',
               'static', 'super', 'switch', 'this', 'throw', 'try', 'typeof', 'var', 'void', 'while', 'with', 'yield')

    ConstLiteral = ('null', 'true', 'false')
    NumberLiteral = ('decimal_float',
                     'decimal_int', 'binary', 'octal', 'hexadecimal',
                     'B_decimal_int', 'B_binary', 'B_octal', 'B_hexadecimal')
    Identifier = 'identifier'
    StringLiteral = ('\'', '"', '`')

    OpAdd = '+'
    OpSub = '-'
    OpMulti = '*'
    OpDiv = '/'
    OpMod = '%'
    OpIncrement = '++'
    OpDecrement = '--'
    OpExp = '**'

    OpEqual = '=='
    OpIdentical = '==='
    OpNotEqual = '!='
    OpNotIdentical = '!=='
    OpGreaterThan = '>'
    OpLessThan = '<'
    OpGreaterThanEqual = '>='
    OpLessThanEqual = '<='

    # logic
    OpBitwiseAnd = '&'
    OpBitwiseOr = '|'
    OpBitwiseXor = '^'
    OpBitwiseNot = '~'

    OpLeftShift = '<<'
    OpRightShift = '>>'
    OpZeroFillRight = '>>>'

    OpAndSymb = '&&'
    OpOrSymb = '||'
    OpNot = '!'

    # assignment
    OpAssignment = '='
    OpAddAssignment = '+='
    OpSubAssignment = '-='
    OpMultiAssignment = '*='
    OpDivAssignment = '/='
    OpModAssignment = '%='
    OpExpAssignment = '**='

    OpBitwiseAndAssignment = '&='
    OpBitwiseOrAssignment = '|='
    OpBitwiseXorAssignment = '^='
    OpLeftShiftAssignment = '<<='
    OpRightShiftAssignment = '>>='
    OpZeroFillRightAssignment = '>>>='

    # conditional assignment
    OpQuestMark = '?'
    OpColon = ':'

    Operators = ('+', '-', '*', '/', '%', '++', '--', '**',
                 '==', '===', '!=', '!==', '>', '<', '>=', '<=',
                 '&', '|', '^', '~', '<<', '>>', '>>>', '&&', '||', '!',
                 '=', '+=', '-=', '*=', '/=', '%=', '**=', '&=', '|=', '^=', '<<=', '>>=', '>>>=',
                 '?', ':'
                 )

    Invalid = 'Invalid'
