# Inteligência Artificial do Evil Force JWT

Este documento explica as funcionalidades avançadas de IA implementadas no Evil Force JWT para análise de tokens JWT e interação conversacional com capacidades similares ao ChatGPT, Gemini e DeepSeek.

## Recursos de IA

A ferramenta Evil Force JWT agora possui uma IA avançada com as seguintes capacidades:

1. **Chat Inteligente com Raciocínio Avançado**: Converse naturalmente em português com uma IA que entende contexto, responde com profundidade e pode explicar conceitos complexos.
2. **Análise Profunda de Tokens**: Análise detalhada de tokens JWT, identificando vulnerabilidades sutis e padrões de ataque avançados.
3. **Recomendações de Segurança Personalizadas**: Sugestões específicas e altamente contextuais para melhorar a segurança de tokens JWT.
4. **Análise de Código**: Capacidade de revisar e identificar problemas em implementações de JWT em diversos frameworks e linguagens.
5. **Geração de Payloads**: Criação inteligente de payloads para testes de penetração em sistemas JWT.

## Arquitetura de IA em Camadas

O sistema utiliza uma arquitetura em camadas para garantir o melhor desempenho possível:

1. **Ollama com Llama 3** (Nível Premium - Local): Modelo avançado de IA executado localmente com qualidade comparável ao ChatGPT e Gemini.
2. **API HuggingFace** (Nível Intermediário): Utilizada como fallback quando o Ollama não está disponível.
3. **Respostas Predefinidas** (Nível Básico): Sistema de respostas inteligentes para garantir funcionalidade mesmo sem conexão.

## Instalação do Ollama

Para aproveitar ao máximo os recursos de IA avançada, é necessário instalar o Ollama:

### Método Automatizado (Recomendado)

Execute o script de instalação incluído:

```bash
python install_ollama.py
```

Este script irá:
1. Verificar se o Ollama já está instalado
2. Baixar e instalar o Ollama se necessário
3. Iniciar o servidor Ollama
4. Baixar o modelo Llama 3 (aproximadamente 4GB)

### Instalação Manual

Se preferir instalar manualmente:

1. Visite [ollama.com/download](https://ollama.com/download) e baixe o instalador para seu sistema
2. Instale o Ollama seguindo as instruções na tela
3. Abra um terminal e execute:
   ```bash
   ollama pull llama3
   ```

## Uso da IA

Uma vez instalado o Ollama e baixado o modelo Llama 3, a IA avançada será automaticamente utilizada em todas as interações. Você pode:

1. Fazer perguntas sobre tokens JWT e segurança
2. Solicitar análise de vulnerabilidades específicas
3. Pedir recomendações para melhorar a segurança dos tokens
4. Obter explicações detalhadas sobre ataques e defesas

## Solução de Problemas

Se encontrar problemas com a IA:

1. Verifique se o Ollama está instalado e em execução:
   ```bash
   ollama ps
   ```

2. Reinicie o servidor Ollama:
   ```bash
   ollama serve
   ```

3. Verifique se o modelo Llama 3 está disponível:
   ```bash
   ollama list
   ```

4. Se o modelo não estiver disponível, baixe-o:
   ```bash
   ollama pull llama3
   ```

5. Se os problemas persistirem, a aplicação usará automaticamente o modo de fallback com a API HuggingFace ou respostas predefinidas.

## Requisitos de Sistema

Para obter o melhor desempenho da IA:

- **RAM**: Mínimo 8GB, recomendado 16GB
- **Armazenamento**: 5GB livres para o modelo
- **Processador**: x64 compatível com SSE4.1
- **GPU**: Opcional, mas melhora significativamente o desempenho

## Perguntas Frequentes

**P: Posso usar a ferramenta sem baixar o modelo de IA?**  
R: Sim, a ferramenta funciona em modo de fallback com capacidades limitadas, mas ainda úteis.

**P: O modelo é enviado para algum servidor externo?**  
R: Não, tudo é processado localmente em seu computador, garantindo total privacidade.

**P: A IA funciona em idiomas além do português?**  
R: Sim, embora otimizada para português, o modelo Llama 3 tem excelentes capacidades multilíngues.

**P: Como a qualidade se compara a ChatGPT ou Gemini?**  
R: O modelo Llama 3 fornece respostas de alta qualidade, muito próximas aos modelos premium, com a vantagem de ser totalmente gratuito e privado.

## Desligamento Seguro

Ao fechar a interface de IA, o sistema desligará automaticamente todos os servidores locais para liberar recursos.

---

*Evil Force JWT - Suite Avançada de Ataques com IA Premium* 