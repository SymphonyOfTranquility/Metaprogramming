from enum import Enum


class Tokens(Enum):
    WhiteSpace = 'WhiteSpace'
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
    StartTemplateString = 'start `'
    EndTemplateString = 'end `'
    InterpolationStart = '${'
    InterpolationEnd = '}'

    Punctuation = ('[', ']', '(', ')', '{', '}', '.', ';', ',')

    Operators = ('+', '-', '*', '/', '%', '++', '--', '**',
                 '==', '===', '!=', '!==', '>', '<', '>=', '<=',
                 '&', '|', '^', '~', '<<', '>>', '>>>', '&&', '||', '!',
                 '=', '+=', '-=', '*=', '/=', '%=', '**=', '&=', '|=', '^=', '<<=', '>>=', '>>>=',
                 '?', ':'
                 )

    Invalid = 'Invalid'
    Interpolation = 'Interpolation'
