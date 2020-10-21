from DictTokenTypes import Tokens


class Token:

    def __init__(self, token_type=None, row=None, column=None,  index=None, spec=None):
        self.type = token_type
        self.spec = spec
        self.index = index
        self.row = row
        self.column = column

    def set_invalid(self):
        self.index = self.row = self.column = self.spec = None
        self.type = Tokens.Invalid

    def __str__(self):
        ans = ''
        if self.type is not None:
            if self.spec is not None:
                ans += str(self.type).ljust(20)
            else:
                ans += str(self.type).ljust(40)
        if self.spec is not None:
            ans += (' ( ' + self.spec + ' ) ').ljust(20)
        if self.row is not None:
            ans += '|' + str(self.row) + '|'
        if self.column is not None:
            ans += (str(self.column) + '|').ljust(8)
        if self.index is not None:
            ans += str(self.index) + ') '
        return ans


class WrongToken:

    def __init__(self, message=None, token=None):
        self.error_message = message
        self.token = token

    def __str__(self):
        return self.error_message.ljust(40) + '|' + str(self.token)
