from Lexer import Lexer
from DictTokenTypes import Tokens
from CharChecks import *
from JsFormatter import JsFormatter


def d(func):
    print(func('3'))


if __name__ == '__main__':
    # lexer = Lexer()
    # lexer.process_js_file('code.js')
    # lexer.print_all()
    formatter = JsFormatter()
    formatter.set_up_config('config/config.json')
    formatter.process_js_file('code.js')
    formatter.print_all_tokens()
    formatter.print_all()


