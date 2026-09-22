import re
from typing import Iterable

from core.categories import categorize

MONTHS = {
    "JAN": 1, "FEV": 2, "MAR": 3, "ABR": 4, "MAI": 5, "JUN": 6,
    "JUL": 7, "AGO": 8, "SET": 9, "OUT": 10, "NOV": 11, "DEZ": 12,
}

IGNORED_TERMS = (
    "PAGAMENTO DE FATURA",
    "PAGAMENTO RECEBIDO",
    "SALDO ANTERIOR",
    "TOTAL DA FATURA",
    "TOTAL A PAGAR",
    "PAGAMENTO MINIMO",
    "PAGAMENTO MÍNIMO",
    "LIMITE DISPONIVEL",
    "LIMITE DISPONÍVEL",
    "ENCARGOS",
    "JUROS",
    "IOF",
)

BANK_MARKERS = {
    "nubank": ("NUBANK", "NU PAGAMENTOS"),
    "inter": ("BANCO INTER", "INTER PAGAMENTOS"),
    "mercado_pago": ("MERCADO PAGO", "MERCADOPAGO"),
    "sicredi": ("SICREDI",),
}

DATE_PATTERNS = (
    re.compile(r"^(?P<day>\d{1,2})[/-](?P<month>\d{1,2})(?:[/-](?P<year>\d{2,4}))?\s+"),
    re.compile(r"^(?P<day>\d{1,2})\s+(?P<month_name>JAN|FEV|MAR|ABR|MAI|JUN|JUL|AGO|SET|OUT|NOV|DEZ)\s+", re.I),
)

AMOUNT_AT_END = re.compile(
    r"(?P<sign>-)?\s*(?:R\$\s*)?(?P<amount>\d{1,3}(?:\.\d{3})*,\d{2}|\d+,\d{2}|\d+\.\d{2})\s*$"
)

INSTALLMENT_PATTERN = re.compile(r"(?:PARC(?:ELA)?\s*)?(?P<current>\d{1,2})\s*/\s*(?P<total>\d{1,2})", re.I)


def detect_bank(text: str) -> str:
    upper = (text or "").upper()
    for bank, markers in BANK_MARKERS.items():
        if any(marker in upper for marker in markers):
            return bank
    return "desconhecido"


def parse_amount(raw: str) -> float:
    value = (raw or "").replace("R$", "").replace(" ", "").strip()
    if not value:
        raise ValueError("valor vazio")

    if "," in value:
        value = value.replace(".", "").replace(",", ".")
    elif value.count(".") > 1:
        value = value.replace(".", "")
    return float(value)


def _should_ignore(line: str) -> bool:
    upper = line.upper()
    return any(term in upper for term in IGNORED_TERMS)


def _extract_date(line: str):
    for pattern in DATE_PATTERNS:
        match = pattern.match(line)
        if not match:
            continue
        groups = match.groupdict()
        month = groups.get("month")
        if month:
            month_value = int(month)
        else:
            month_value = MONTHS[groups["month_name"].upper()]
        year = groups.get("year")
        year_value = int(year) if year else None
        if year_value is not None and year_value < 100:
            year_value += 2000
        return {
            "day": int(groups["day"]),
            "month": month_value,
            "year": year_value,
            "end": match.end(),
        }
    return None


def _clean_description(text: str) -> str:
    text = INSTALLMENT_PATTERN.sub("", text)
    text = re.sub(r"\s{2,}", " ", text)
    return text.strip(" -–—|")


def _transaction_from_line(line: str, bank: str):
    if not line or _should_ignore(line):
        return None

    amount_match = AMOUNT_AT_END.search(line)
    if not amount_match:
        return None

    try:
        amount = parse_amount(amount_match.group("amount"))
    except ValueError:
        return None

    if amount_match.group("sign"):
        amount *= -1

    prefix = line[:amount_match.start()].strip()
    date_info = _extract_date(prefix)
    if date_info:
        description_source = prefix[date_info["end"]:].strip()
    else:
        description_source = prefix

    if len(description_source) < 2:
        return None

    installment_match = INSTALLMENT_PATTERN.search(description_source)
    installment_current = int(installment_match.group("current")) if installment_match else None
    installment_total = int(installment_match.group("total")) if installment_match else None
    description = _clean_description(description_source)

    if not description or description.upper() in {"TOTAL", "SUBTOTAL"}:
        return None

    transaction = {
        "Lançamento": description,
        "Categoria": categorize(description),
        "Valor": round(amount, 2),
        "Banco": bank,
        "ParcelaAtual": installment_current,
        "ParcelasTotal": installment_total,
    }

    if date_info:
        transaction["Dia"] = date_info["day"]
        transaction["Mes"] = date_info["month"]
        transaction["Ano"] = date_info["year"]

    return transaction


def _join_candidate_lines(lines: Iterable[str]) -> list[str]:
    cleaned = [re.sub(r"\s+", " ", line).strip() for line in lines if line and line.strip()]
    candidates: list[str] = []
    for index, line in enumerate(cleaned):
        candidates.append(line)
        if index + 1 < len(cleaned):
            next_line = cleaned[index + 1]
            if _extract_date(line) and not AMOUNT_AT_END.search(line):
                candidates.append(f"{line} {next_line}")
    return candidates


def parse_transactions(text: str) -> dict:
    bank = detect_bank(text)
    transactions = []
    seen = set()

    for line in _join_candidate_lines((text or "").splitlines()):
        transaction = _transaction_from_line(line, bank)
        if not transaction:
            continue

        signature = (
            transaction.get("Dia"), transaction.get("Mes"), transaction.get("Ano"),
            transaction["Lançamento"].upper(), transaction["Valor"],
        )
        if signature in seen:
            continue
        seen.add(signature)
        transactions.append(transaction)

    total = round(sum(item["Valor"] for item in transactions if item["Valor"] > 0), 2)
    return {
        "bank": bank,
        "transactions": transactions,
        "total": total,
    }
