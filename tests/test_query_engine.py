from core.query_engine import answer_question, build_summary

TXS = [
    {"Lançamento": "IFOOD", "Categoria": "Alimentação", "Valor": 50.0},
    {"Lançamento": "UBER", "Categoria": "Transporte", "Valor": 20.0},
    {"Lançamento": "NETFLIX", "Categoria": "Assinaturas", "Valor": 30.0},
]


def test_summary():
    summary = build_summary(TXS)
    assert summary["total"] == 100.0
    assert summary["count"] == 3
    assert summary["by_category"]["Alimentação"] == 50.0


def test_total_question():
    answer = answer_question("Quanto gastei no total?", TXS)
    assert "R$ 100,00" in answer


def test_category_question():
    answer = answer_question("Quanto gastei com alimentação?", TXS)
    assert "R$ 50,00" in answer


def test_merchant_question_is_not_category_total():
    answer = answer_question("Quanto gastei no iFood?", TXS)
    assert "R$ 50,00" in answer
    assert "lançamento" in answer.lower()
