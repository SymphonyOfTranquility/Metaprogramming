from enum import Enum, auto


class Tokens(Enum):
    WhiteSpace = 'WhiteSpace'
    Space = ' '
    Tab = '\t'
    Enter = '\n'

    SingleLineComment = '//'
    MultiLineComment = '/*'

    Keyword = ('async', 'await', 'break', 'case', 'catch', 'class', 'const', 'continue', 'debugger', 'default', 'delete', 'do',
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

    Operators = ('=', '+=', '-=', '*=', '/=', '%=', '**=', '&=', '|=', '^=', '<<=', '>>=', '>>>=',
                 '&&', '||',
                 '==', '===', '!=', '!==', '>', '<', '>=', '<=',
                 '&', '|', '^', '~',
                 '+', '-',
                 '*', '/', '%', '**',
                 '<<', '>>', '>>>',
                 '++', '--',
                 '=>',
                 '!', '!!',
                 '?', ':',
                 '...'
                 )
    Regex = 'regex'
    Invalid = 'Invalid'
    Interpolation = 'Interpolation'


class Scope(Enum):
    FuncDeclaration = auto()
    FuncCall = auto()
    FuncExpression = auto()
    AsyncFunc = auto()
    Grouping = auto()
    If = auto()
    Else = auto()
    For = auto()
    While = auto()
    Do = auto()
    Switch = auto()
    Try = auto()
    Catch = auto()
    Finally = auto()
    PropertyNameValue = auto()
    TernaryIf = auto()
    Class = auto()

    GeneralBrace = auto()
    GeneralScope = auto()
    ES6ImportBrace = auto()
    ObjectLiteralBrace = auto()
    Interpolation = auto()

    IndexAccessBrackets = auto()
    ArrayBrackets = auto()

    AssignmentOperators = ('=', '+=', '-=', '*=', '/=', '%=', '**=', '&=', '|=', '^=', '<<=', '>>=', '>>>=')
    LogicOperators = ('&&', '||')
    EqualityOperators = ('==', '===', '!=', '!==')
    RelationalOperators = ('>', '<', '>=', '<=')
    BitwiseOperators = ('&', '|', '^', '~')
    AdditiveOperators = ('+', '-')
    MultiplicativeOperators = ('*', '/', '%', '**')
    ShiftOperators = ('<<', '>>', '>>>')
    UnaryAdditiveOperators = ('+', '-', '++', '--')
    ArrowFunction = tuple(["=>"])
    BeforeUnaryNot = ('!', '!!')
    AfterUnaryNot = ('!', '!!')

    AfterQuestMark = tuple(['?'])
    BeforeQuestMark = tuple(['?'])
    AfterColon = tuple([':'])
    BeforeColon = tuple([':'])

    AfterComma = tuple([','])
    BeforeComma = tuple([','])


class BlankLines(Enum):
    Max = auto()

    Imports = auto()
    Class = auto()
    Field = auto()
    Method = auto()
    Func = auto()
