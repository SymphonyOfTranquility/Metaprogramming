from DictTokenTypes import Tokens


def is_whitespace_token(token_type):
    return token_type == Tokens.Tab or token_type == Tokens.Space or token_type == Tokens.Enter
