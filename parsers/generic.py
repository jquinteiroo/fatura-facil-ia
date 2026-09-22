from parsers.common import parse_standard


def parse(text: str, bank: str = "desconhecido") -> list[dict]:
    return parse_standard(text, bank)
