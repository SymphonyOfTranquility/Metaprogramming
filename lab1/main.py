from Lexer import Lexer
from DictTokenTypes import Tokens
from CharChecks import *


def d(func):
    print(func('3'))


if __name__ == '__main__':
    lexer = Lexer()
    lexer.get_all_tokens('code.js')
    lexer.print_all()

