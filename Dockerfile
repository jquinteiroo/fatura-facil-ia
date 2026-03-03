# 1. Usa uma versão oficial e leve do Python
FROM python:3.10-slim

# 2. Define a pasta de trabalho dentro do servidor do Google
WORKDIR /app

# 3. Copia o ficheiro de dependências e instala tudo
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. Copia o resto do seu projeto (HTML, Python, etc.)
COPY . .

# 5. Comando de arranque otimizado para o Cloud Run (1 worker e 8 threads)
CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 app:app