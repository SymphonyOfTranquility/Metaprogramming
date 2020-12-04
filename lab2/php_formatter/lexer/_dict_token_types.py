from enum import Enum, auto


class Tokens(Enum):
    WhiteSpace = 'WhiteSpace'
    Space = ' '
    Tab = '\t'
    Enter = '\n'

    SingleLineComment = '//'
    MultiLineComment = '/*'

    Keyword = ('__halt_compiler', 'abstract', 'and', 'array', 'as', 'break', 'callable', 'case', 'catch', 'class',
               'clone', 'const', 'continue', 'declare', 'default', 'die', 'do', 'echo', 'else', 'elseif', 'empty',
               'enddeclare', 'endfor', 'endforeach', 'endif', 'endswitch', 'endwhile', 'eval', 'exit', 'extends',
               'final', 'finally', 'fn', 'for', 'foreach', 'function', 'global', 'goto', 'if', 'implements', 'include',
               'include_once', 'instanceof', 'insteadof', 'interface', 'isset', 'list',	'namespace', 'new', 'or',
               'print', 'private', 'protected', 'public', 'require', 'require_once', 'return', 'static', 'switch',
               'throw', 'trait', 'try', 'unset', 'use', 'var', 'while', 'xor', 'yield', 'from',

               'int', 'float', 'bool', 'string', 'void', 'iterable', 'object', 'resource', 'mixed', 'numeric',

               'Directory', 'stdClass', '__PHP_Incomplete_Class', 'Exception', 'ErrorException', 'php_user_filter',
               'Closure', 'Generator', 'ArithmeticError', 'AssertionError', 'DivisionByZeroError', 'Error',
               'Throwable', 'ParseError', 'TypeError', 'self', 'static', 'parent')

    ConstLiteral = ('null', 'true', 'false',

                    '__CLASS__', '__DIR__', '__FILE__', '__FUNCTION__', '__LINE__',
                    '__METHOD__', '__NAMESPACE__', '__TRAIT__',

                    'PHP_VERSION', 'PHP_MAJOR_VERSION', 'PHP_MINOR_VERSION', 'PHP_RELEASE_VERSION', 'PHP_VERSION_ID',
                    'PHP_EXTRA_VERSION', 'PHP_ZTS', 'PHP_DEBUG', 'PHP_MAXPATHLEN', 'PHP_OS', 'PHP_OS_FAMILY',
                    'PHP_SAPI', 'PHP_EOL', 'PHP_INT_MAX', 'PHP_INT_MIN', 'PHP_INT_SIZE', 'PHP_FLOAT_DIG',
                    'PHP_FLOAT_EPSILON', 'PHP_FLOAT_MIN', 'PHP_FLOAT_MAX', 'DEFAULT_INCLUDE_PATH', 'PEAR_INSTALL_DIR',
                    'PEAR_EXTENSION_DIR', 'PHP_EXTENSION_DIR', 'PHP_PREFIX', 'PHP_BINDIR', 'PHP_BINARY', 'PHP_MANDIR',
                    'PHP_LIBDIR', 'PHP_DATADIR', 'PHP_SYSCONFDIR', 'PHP_LOCALSTATEDIR', 'PHP_CONFIG_FILE_PATH',
                    'PHP_CONFIG_FILE_SCAN_DIR', 'PHP_SHLIB_SUFFIX', 'PHP_FD_SETSIZE', 'E_ERROR', 'E_WARNING', 'E_PARSE',
                    'E_NOTICE', 'E_CORE_ERROR', 'E_CORE_WARNING', 'E_COMPILE_ERROR', 'E_COMPILE_WARNING',
                    'E_USER_ERROR', 'E_USER_WARNING', 'E_USER_NOTICE', 'E_RECOVERABLE_ERROR', 'E_DEPRECATED',
                    'E_USER_DEPRECATED', 'E_ALL', 'E_STRICT', '__COMPILER_HALT_OFFSET__', 'TRUE', 'FALSE', 'NULL',
                    'PHP_WINDOWS_EVENT_CTRL_C', 'PHP_WINDOWS_EVENT_CTRL_BREAK')
    NumberLiteral = ('decimal_float',
                     'decimal_int', 'binary', 'octal', 'hexadecimal',
                     'B_decimal_int', 'B_binary', 'B_octal', 'B_hexadecimal')
    Identifier = 'identifier'
    Variable = 'variable'
    StringLiteral = ('\'', '"', '`')
    StartTemplateString = 'start "'
    EndTemplateString = 'end "'
    InterpolationStart = '${'
    InterpolationEnd = '}'

    Punctuation = ('[', ']', '(', ')', '{', '}', ';', ',')

    Operators = ('=', '+=', '-=', '*=', '/=', '%=', '**=', '&=', '|=', '^=', '<<=', '>>=', '??=',
                 '&&', '||', '!',
                 '==', '===', '!=', '<>', '!==', '>', '<', '>=', '<=', '<=>',
                 '&', '|', '^', '~',
                 '+', '-',
                 '*', '/', '%', '**',
                 '<<', '>>',
                 '++', '--',
                 '?', ':',
                 '.', '.=',
                 '->',
                 )
    Regex = 'regex'
    Invalid = 'Invalid'
    Interpolation = 'Interpolation'