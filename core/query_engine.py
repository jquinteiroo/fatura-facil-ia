import re
import unicodedata
from collections import defaultdict

from core.categories import CATEGORIES


def _normalize(text: str) -> str:
    text = unicodedata.normalize("NFKD", text or "")
    text = "".join(c for c in text if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", text).strip().lower()


def _money(value: float) -> str:
    formatted = f"{value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {formatted}"


def _positive(transactions):
    return [item for item in transactions if float(item.get("Valor", 0) or 0) > 0]


def build_summary(transactions: list[dict]) -> dict:
    txs = _positive(transactions)
    total = round(sum(float(item.get("Valor", 0) or 0) for item in txs), 2)
    by_category = defaultdict(float)
    by_merchant = defaultdict(float)

    for item in txs:
        value = float(item.get("Valor", 0) or 0)
        by_category[item.get("Categoria") or "Outros"] += value
        by_merchant[item.get("Lançamento") or "Lançamento"] += value

    return {
        "total": total,
        "count": len(txs),
        "average": round(total / len(txs), 2) if txs else 0.0,
        "by_category": dict(by_category),
        "by_merchant": dict(by_merchant),
        "largest": max(txs, key=lambda item: float(item.get("Valor", 0) or 0), default=None),
    }


def _category_from_question(question: str):
    normalized = _normalize(question)
    aliases = {
        "Alimentação": ("alimentacao", "comida", "restaurante"),
        "Mercado": ("mercado", "supermercado"),
        "Transporte": ("transporte", "combustivel", "gasolina"),
        "Moradia": ("moradia", "casa", "aluguel"),
        "Saúde": ("saude", "farmacia", "medico"),
        "Educação": ("educacao", "curso", "faculdade"),
        "Lazer": ("lazer", "cinema", "jogos"),
        "Compras": ("compras", "shopping"),
        "Assinaturas": ("assinatura", "assinaturas", "recorrente", "recorrentes"),
        "Viagens": ("viagem", "viagens", "hotel"),
        "Serviços": ("servico", "servicos", "internet", "telefone"),
        "Outros": ("outros",),
    }
    for category in CATEGORIES:
        if any(alias in normalized for alias in aliases.get(category, ())):
            return category
    return None


def answer_question(question: str, transactions: list[dict]) -> str:
    q = _normalize(question)
    summary = build_summary(transactions)
    txs = _positive(transactions)

    if not txs:
        return "Ainda não encontrei transações válidas nesta fatura."

    if any(term in q for term in ("quanto gastei no total", "total da fatura", "total gasto", "valor total")):
        return f"O total das transações identificadas é **{_money(summary['total'])}**."

    category = _category_from_question(question)
    if category:
        value = summary["by_category"].get(category, 0.0)
        percentage = (value / summary["total"] * 100) if summary["total"] else 0
        return f"Em **{category}**, foram **{_money(value)}** (**{percentage:.1f}%** do total identificado)."

    if any(term in q for term in ("maior gasto", "maior compra", "compra mais cara")):
        largest = summary["largest"]
        return f"Sua maior despesa identificada foi **{largest.get('Lançamento', 'Lançamento')}**, no valor de **{_money(float(largest['Valor']))}**."

    if any(term in q for term in ("5 maiores", "cinco maiores", "maiores compras", "maiores gastos")):
        top = sorted(txs, key=lambda item: float(item.get("Valor", 0) or 0), reverse=True)[:5]
        lines = [f"{i + 1}. **{item.get('Lançamento', 'Lançamento')}** — {_money(float(item['Valor']))}" for i, item in enumerate(top)]
        return "As maiores despesas identificadas foram:\n\n" + "\n".join(lines)

    if any(term in q for term in ("onde gastei mais", "categoria maior", "categoria que mais")):
        category_name, value = max(summary["by_category"].items(), key=lambda pair: pair[1])
        percentage = value / summary["total"] * 100 if summary["total"] else 0
        return f"A categoria com maior gasto foi **{category_name}**, com **{_money(value)}** (**{percentage:.1f}%** do total)."

    if any(term in q for term in ("quantas compras", "quantas transacoes", "quantas transações")):
        return f"Identifiquei **{summary['count']} transações** com valor positivo nesta fatura."

    if any(term in q for term in ("gasto medio", "gasto médio", "media por compra", "média por compra")):
        return f"O valor médio por transação foi de **{_money(summary['average'])}**."

    amount_match = re.search(r"(?:acima|maior(?:es)? que|mais de)\s*(?:r\$\s*)?(\d+(?:[.,]\d{1,2})?)", q)
    if amount_match:
        threshold = float(amount_match.group(1).replace(",", "."))
        found = [item for item in txs if float(item.get("Valor", 0) or 0) > threshold]
        if not found:
            return f"Não encontrei compras acima de **{_money(threshold)}**."
        found = sorted(found, key=lambda item: float(item["Valor"]), reverse=True)[:10]
        lines = [f"- **{item.get('Lançamento', 'Lançamento')}** — {_money(float(item['Valor']))}" for item in found]
        return f"Encontrei **{len(found)}** compra(s) acima de **{_money(threshold)}**:\n\n" + "\n".join(lines)

    merchant_terms = [token for token in re.findall(r"[a-z0-9]{3,}", q) if token not in {
        "quanto", "gastei", "gasto", "com", "no", "na", "nos", "nas", "meu", "minha", "valor", "foi", "total"
    }]
    for term in merchant_terms:
        matches = [item for item in txs if term in _normalize(item.get("Lançamento", ""))]
        if matches:
            value = sum(float(item["Valor"]) for item in matches)
            return f"Encontrei **{len(matches)}** lançamento(s) relacionados a **{term}**, somando **{_money(value)}**."

    return (
        "Consigo responder perguntas objetivas sobre a fatura, como **total gasto**, **maior compra**, "
        "**gastos por categoria**, **5 maiores despesas**, **quantas compras** ou **compras acima de um valor**."
    )
