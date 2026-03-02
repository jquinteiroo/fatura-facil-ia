from flask import Flask, render_template, request, jsonify
import pandas as pd
import google.generativeai as genai
import PyPDF2
import os
import io

app = Flask(__name__)

# Configuração da IA
MINHA_CHAVE_GEMINI = os.environ.get("GEMINI_API_KEY", "")
if MINHA_CHAVE_GEMINI:
    genai.configure(api_key=MINHA_CHAVE_GEMINI)
    model = genai.GenerativeModel('gemini-2.5-flash')

@app.route('/')
def index():
    # Isso faz o Flask mostrar o seu arquivo HTML que está na pasta templates
    return render_template('index.html')

@app.route('/processar', methods=['POST'])
def processar():
    if 'file' not in request.files:
        return jsonify({'erro': 'Nenhum arquivo enviado'})
    
    file = request.files['file']
    filename = file.filename.lower()
    
    try:
        # 1. SE FOR CSV
        if filename.endswith('.csv'):
            df = pd.read_csv(file)
            if 'Valor' not in df.columns:
                file.seek(0)
                df = pd.read_csv(file, sep=';', encoding='utf-8')
                
            # Limpeza rápida do valor
            df['Valor'] = df['Valor'].astype(str).str.replace('R$', '').str.replace('.', '').str.replace(',', '.').astype(float)
            dados_json = df.to_dict(orient='records')
            total = df['Valor'].sum()
            return jsonify({'sucesso': True, 'tipo': 'csv', 'dados': dados_json, 'total': total})
            
        # 2. SE FOR PDF
        elif filename.endswith('.pdf'):
            leitor = PyPDF2.PdfReader(file)
            texto_pdf = ""
            for pagina in leitor.pages:
                texto_pdf += pagina.extract_text() + "\n"
                
            # Pedimos para a IA extrair os dados do texto bagunçado do PDF
            prompt = f"""
            Você é um extrator de dados. Leia o texto desta fatura de cartão e extraia as transações.
            Retorne APENAS um formato JSON válido com uma lista de objetos contendo 'Data', 'Lançamento', 'Categoria' e 'Valor' (apenas números).
            Texto: {texto_pdf[:10000]}
            """
            resposta_ia = model.generate_content(prompt)
            # Aqui no futuro podemos tratar o JSON da resposta, mas vamos retornar o texto cru por enquanto
            return jsonify({'sucesso': True, 'tipo': 'pdf', 'texto_extraido': resposta_ia.text})
            
        else:
            return jsonify({'erro': 'Formato não suportado. Envie CSV ou PDF.'})
            
    except Exception as e:
        return jsonify({'erro': str(e)})

@app.route('/chat', methods=['POST'])
def chat():
    dados = request.json
    pergunta = dados.get('pergunta')
    contexto = dados.get('contexto')
    
    prompt = f"Você é um consultor financeiro. Fatura: {contexto}. Pergunta: {pergunta}"
    resposta = model.generate_content(prompt)
    
    return jsonify({'resposta': resposta.text})

if __name__ == '__main__':
    app.run(debug=True, port=int(os.environ.get("PORT", 5000)), host='0.0.0.0')