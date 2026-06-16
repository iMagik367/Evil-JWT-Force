import os
try:
    from openai import OpenAI
except ImportError:
    print("Biblioteca 'openai' não está instalada. Instale-a com 'pip install openai'")
    exit(1)

# Definir a chave da API via variável de ambiente
api_key = os.environ.get('OPENAI_API_KEY', '')
if not api_key:
    print("Erro: Chave da API da OpenAI não configurada.")
    exit(1)

print("Chave da API da OpenAI configurada.")

# Inicializar o cliente da OpenAI
client = OpenAI(api_key=api_key)

# Simular um histórico de conversa como o ChatManager pode usar
conversation_history = [
    {"role": "system", "content": "Você é um especialista em segurança de JWT. Antes de responder, pense passo a passo e explique seu raciocínio de forma clara."},
    {"role": "user", "content": "Olá, teste de conectividade."}
]

try:
    # Fazer uma chamada à API com histórico de conversa
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=conversation_history,
        max_tokens=100
    )
    print("Conexão bem-sucedida com a API da OpenAI!")
    print("Resposta da API:", response.choices[0].message.content)
except Exception as e:
    print("Erro ao conectar à API da OpenAI:", str(e)) 