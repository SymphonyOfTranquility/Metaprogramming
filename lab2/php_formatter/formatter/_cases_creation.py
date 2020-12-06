def correct_snake_case(s):
    new_s = ''
    for i in range(len(s)):
        if (s[i]).isupper() and i != 0 and ((s[i - 1]).islower() or i + 1 < len(s) and (s[i + 1]).islower()):
            new_s += '_'
        new_s += (s[i]).lower()
    return new_s


def correct_screaming_snake_case(s):
    return s.upper()
