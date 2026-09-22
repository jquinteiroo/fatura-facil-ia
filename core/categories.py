import re
import unicodedata

CATEGORIES = (
    "Alimentação",
    "Mercado",
    "Transporte",
    "Moradia",
    "Saúde",
    "Educação",
    "Lazer",
    "Compras",
    "Assinaturas",
    "Viagens",
    "Serviços",
    "Outros",
)

CATEGORY_RULES = {
    "Assinaturas": (
        "NETFLIX", "SPOTIFY", "DISNEY", "HBO", "MAX.COM", "AMAZON PRIME",
        "PRIME VIDEO", "YOUTUBE PREMIUM", "GOOGLE ONE", "ICLOUD", "CHATGPT",
        "OPENAI", "DEEZER", "CANVA", "ADOBE",
    ),
    "Alimentação": (
        "IFOOD", "RAPPI", "MCDONALD", "BURGER KING", "RESTAURANTE", "PIZZARIA",
        "LANCHONETE", "PADARIA", "CAFETERIA", "STARBUCKS", "SUBWAY",
    ),
    "Mercado": (
        "SUPERMERCADO", "MERCADO", "HIPERMERCADO", "ATACADAO", "ATACADÃO",
        "ASSAI", "ASSAÍ", "CARREFOUR", "PAGUE MENOS MERCADO", "HORTIFRUTI",
    ),
    "Transporte": (
        "UBER", "99APP", "99 APP", "POSTO", "SHELL", "IPIRANGA", "PETROBRAS",
        "ESTACIONAMENTO", "PEDAGIO", "PEDÁGIO", "SEM PARAR", "VELOE",
    ),
    "Saúde": (
        "FARMACIA", "FARMÁCIA", "DROGARIA", "DROGA RAIA", "DROGASIL", "HOSPITAL",
        "CLINICA", "CLÍNICA", "LABORATORIO", "LABORATÓRIO", "ODONTO",
    ),
    "Educação": (
        "PUC", "UNIVERSIDADE", "FACULDADE", "UDEMY", "ALURA", "COURSERA",
        "ESCOLA", "CURSO", "LIVRARIA",
    ),
    "Lazer": (
        "CINEMA", "INGRESSO", "STEAM", "PLAYSTATION", "XBOX", "NINTENDO",
        "EVENTIM", "TICKETMASTER", "SPOTIFY EVENT",
    ),
    "Viagens": (
        "AIRBNB", "BOOKING", "HOTEL", "HOTEIS.COM", "DECOLAR", "LATAM",
        "GOL LINHAS", "AZUL LINHAS", "UBER TRIP",
    ),
    "Moradia": (
        "ENERGIA", "ELETRICIDADE", "CEMIG", "SABESP", "SANEPAR", "COPASA",
        "CONDOMINIO", "CONDOMÍNIO", "ALUGUEL", "IMOBILIARIA", "IMOBILIÁRIA",
    ),
    "Serviços": (
        "VIVO", "CLARO", "TIM", "OI ", "INTERNET", "HOSTINGER", "GITHUB",
        "GOOGLE CLOUD", "AWS", "MICROSOFT", "DOMINIO", "DOMÍNIO",
    ),
    "Compras": (
        "AMAZON", "MERCADO LIVRE", "SHOPEE", "MAGALU", "MAGAZINE LUIZA",
        "SHEIN", "ALIEXPRESS", "RENNER", "RIACHUELO", "C&A", "ZARA",
    ),
}


def _normalize(text: str) -> str:
    text = unicodedata.normalize("NFKD", text or "")
    text = "".join(char for char in text if not unicodedata.combining(char))
    text = re.sub(r"\s+", " ", text).strip().upper()
    return text


def categorize(description: str) -> str:
    normalized = _normalize(description)
    for category, keywords in CATEGORY_RULES.items():
        if any(_normalize(keyword) in normalized for keyword in keywords):
            return category
    return "Outros"
