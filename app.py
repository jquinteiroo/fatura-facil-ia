from flask import Flask, render_template, request, jsonify
import pandas as pd
import google.generativeai as genai
import PyPDF2
import os
import json
import re
import csv
import os
from datetime import datetime
import requests

app = Flask(__name__)

CHAVES_API = [ # Chaves de API da IA
    os.environ.get("GEMINI_API_KEY_1", ""),
    os.environ.get("GEMINI_API_KEY_2", ""),
    os.environ.get("GEMINI_API_KEY_3", "")
]

CHAVES_ATIVAS = [k for k in CHAVES_API if k]

def gerar_conteudo_com_rodizio(prompt): # Rodízio de chaves, para não parar de rodar
    """Tenta usar as chaves uma por uma caso o limite seja atingido"""
    for chave in CHAVES_ATIVAS:
        try:
            genai.configure(api_key=chave)
            model = genai.GenerativeModel('gemini-2.5-flash')
            resposta = model.generate_content(prompt)
            return resposta
        except Exception as e:
            
            if "429" in str(e):
                print(f"Limite atingido na chave atual, tentando a próxima...")
                continue
            else:
                raise e 
    return None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/processar', methods=['POST'])  # Processamento do arquivo da fatura
def processar():
    if 'file' not in request.files:
        return jsonify({'erro': 'Nenhum arquivo enviado'})
    
    file = request.files['file']
    filename = file.filename.lower()
    
    try:
        if filename.endswith('.csv'):
            try:
                df = pd.read_csv(file)
                if 'Valor' not in df.columns:
                    file.seek(0)
                    df = pd.read_csv(file, sep=';', encoding='utf-8')
            except:
                file.seek(0)
                df = pd.read_csv(file, sep=';', encoding='utf-8')
                
            if 'Valor' not in df.columns:
                return jsonify({'erro': 'A coluna "Valor" não foi encontrada no CSV.'})
                
            df['Valor'] = df['Valor'].astype(str).str.replace('R$', '').str.replace('.', '').str.replace(',', '.').astype(float)
            
            if 'Categoria' in df.columns:
                df['Categoria'] = df['Categoria'].fillna('OUTROS').str.upper()
            else:
                df['Categoria'] = 'OUTROS'
                
            df = df.dropna(subset=['Valor'])
            
            dados_json = df.to_dict(orient='records')
            total = df['Valor'].sum()
            
            return jsonify({'sucesso': True, 'tipo': 'csv', 'dados': dados_json, 'total': total})

        elif filename.endswith('.pdf'):
            leitor = PyPDF2.PdfReader(file)
            texto_pdf = "".join([p.extract_text() for p in leitor.pages])
            
            prompt_extracao = f"""Você é um extrator de dados financeiros de altíssima precisão.
Extraia TODAS as transações (compras e despesas) do texto da fatura abaixo.

REGRAS ESTRITAS (Obrigatório):
1. IGNORE TOTALMENTE pagamentos da própria fatura (ex: "PAGAMENTO DE FATURA", "SALDO ANTERIOR").
2. IGNORE resumos, blocos de totais, juros e textos informativos.
3. O campo "Valor" DEVE ser obrigatoriamente um número (float). Use PONTO para decimais. NUNCA inclua "R$" ou vírgula. Exemplo correto: 320.50
4. Retorne APENAS um array JSON válido. Nenhuma palavra a mais, nem antes nem depois.

Formato esperado:
[
  {{"Lançamento": "Nome do local", "Categoria": "NOME DA CATEGORIA", "Valor": 150.50}}
]

Texto da fatura:
{texto_pdf}"""
            
            resposta_ia = gerar_conteudo_com_rodizio(prompt_extracao)
            
            if not resposta_ia:
                return jsonify({'erro': 'Nenhuma chave da API configurada ou limite de requisições excedido.'})
            
            try:
                texto_limpo = re.search(r'\[.*\]', resposta_ia.text, re.DOTALL).group(0)
                dados_pdf = json.loads(texto_limpo)
                # Formatação dos números, para prever erros
                for item in dados_pdf:
                    valor_bruto = str(item.get('Valor', '0')).upper().replace('R$', '').replace(' ', '').strip()
                    
                    # Converte para um formato de valor 
                    if ',' in valor_bruto and '.' in valor_bruto:
                        valor_bruto = valor_bruto.replace('.', '').replace(',', '.')
                    elif ',' in valor_bruto:
                        valor_bruto = valor_bruto.replace(',', '.')
                        
                    try:
                        item['Valor'] = float(valor_bruto)
                    except:
                        item['Valor'] = 0.0
                
                # Soma com segurança
                total_pdf = sum(item['Valor'] for item in dados_pdf)
                    
                return jsonify({'sucesso': True, 'tipo': 'pdf_estruturado', 'dados': dados_pdf, 'total': total_pdf})
            except Exception as e:
                return jsonify({'erro': f'A IA não retornou um formato válido. Tente novamente. Detalhe: {str(e)}'})
            
    except Exception as e:
        return jsonify({'erro': f"Erro interno ou IA falhou ao ler PDF: {str(e)}"})

@app.route('/sugerir_banco', methods=['POST']) # Formulário de sugestão
def sugerir_banco():
    dados = request.json
    nome = dados.get('nome', 'Anônimo')
    banco = dados.get('banco', 'Não informado')
    contato = dados.get('contato', 'Nenhum')

    data_hora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    
    # Planilha a ser criada
    arquivo_csv = 'sugestoes_bancos.csv'
    cabecalho_existe = os.path.isfile(arquivo_csv)
    
    # Abre o arquivo em modo 'a' para não apagar o que já tem
    try:
        with open(arquivo_csv, mode='a', newline='', encoding='utf-8') as file:
            writer = csv.writer(file, delimiter=';') 
            
            # Escreve o cabeçalho, quando arquivo novo
            if not cabecalho_existe:
                writer.writerow(['Data/Hora', 'Banco Sugerido', 'Nome', 'Contato'])
            
            # Escreve a sugestão
            writer.writerow([data_hora, banco, nome, contato])
            
        print(f"✅ SALVO NA PLANILHA: {banco} por {nome}")
        return jsonify({'sucesso': True})
    except Exception as e:
        print(f"Erro ao salvar na planilha: {e}")
        return jsonify({'erro': 'Falha ao salvar'}), 500

@app.route('/chat', methods=['POST']) # Rota para processar a pergunta feita pelo usuário
def chat():
    dados = request.json
    pergunta = dados.get('pergunta', '')
    contexto = dados.get('contexto', '')
    resumo = dados.get('resumo', '') 
    
    if not CHAVES_ATIVAS:
         return jsonify({'resposta': 'Erro: API Key do Gemini não configurada no servidor.'})
    
    prompt = f"""
    Você é um consultor financeiro especialista. 
    REGRA DE OURO: NUNCA tente calcular totais por categoria somando os dados detalhados. Você deve usar EXCLUSIVAMENTE os totais fornecidos no 'RESUMO EXATO' abaixo.
    
    {resumo}
    
    DETALHAMENTO DE TRANSAÇÕES:
    {contexto}
    
    Pergunta do usuário: {pergunta}
    """
    
    try:
        resposta = gerar_conteudo_com_rodizio(prompt)
        return jsonify({'resposta': resposta.text})
    except Exception as e:
        return jsonify({'resposta': f"Erro ao gerar resposta da IA: {str(e)}"})

if __name__ == '__main__':
    app.run(debug=True, port=int(os.environ.get("PORT", 5000)), host='0.0.0.0')