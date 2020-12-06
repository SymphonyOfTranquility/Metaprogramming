def snake_case(s):
    new_s = ''
    for i in range(len(s)):
        if (s[i]).isupper() and i != 0 and ((s[i - 1]).islower() or i + 1 < len(s) and (s[i + 1]).islower()):
            new_s += '_'
        new_s += (s[i]).lower()
    return new_s


def screaming_snake_case(s):
    return s.upper()


def camel_case(s):
    new_s = ''
    is_first = True
    for i in range(len(s)):
        if s[i] != '_':
            if is_first:
                new_s += (s[i]).upper()
                is_first = False
            elif i > 0 and s[i-1] == '_':
                new_s += s[i].upper()
            else:
                new_s += s[i]

    return new_s


def file_name_case(s):
    new_s = ''
    for i in range(len(s)):
        if s[i] != '_':
            if (s[i]).isupper() and i != 0 and ((s[i - 1]).islower() or i + 1 < len(s) and (s[i + 1]).islower()):
                new_s += '-'
            new_s += (s[i]).lower()
        elif i > 0 and s[i-1] not in '-_':
            new_s += '-'
    return new_s
