# EVIL_JWT_FORCE
Ferramenta ofensiva completa para pentesters, bug hunters e pesquisadores de segurança, que automatiza ataques e análises de JWT (JSON Web Tokens) e oferece vários módulos de exploração, tudo acessível via CLI e interface gráfica PyQt5.

## Sumário
- [Descrição](#descrição)
- [Principais Funcionalidades](#principais-funcionalidades)
- [Instalação](#instalação)
- [Uso](#uso)
  - [CLI](#linha-de-comando-cli)
  - [GUI](#interface-gráfica-gui)
- [Estrutura do Projeto](#estrutura-do-projeto)
- [Requisitos](#requisitos)
- [Licença](#licença)
- [Disclaimer](#disclaimer)

## Descrição
EVIL_JWT_FORCE é uma suíte Python que reúne:

- Força-bruta de segredos JWT (HS256/HS384/HS512) com wordlists personalizáveis.
- Fuzzing de algoritmos e payloads JWT (mutational, templates, coverage-guided).
- Injeção SQL autenticada via JWT (Boolean, Time, Union, Error-Based).
- Coleta OSINT integrada (social, buscadores, WHOIS, DNS) com filtros e exportação.
- Geração de wordlists baseadas em dados OSINT e variações avançadas.
- Análise criptográfica (AES encrypt/decrypt, hash SHA256/SHA512/MD5).
- Scanner de vulnerabilidades (SQLi, XSS, CSRF, LFI, SSTI, IDOR, Path Traversal).
- Exploração de saldo/account takeover com requisições forjadas.
- Interceptação de tráfego via Selenium WebDriver e Burp Suite API.
- Integração com IA para sugestões e automação de payloads (OpenAI, HuggingFace, Ollama, etc.).
- Relatórios HTML/JSON com gráficos (matplotlib) e exportação de logs.
- Pipeline de execução sequencial de tarefas (OSINT → Scan → Fuzz → SQLi).
- Suporte a VPN e Tor para anonimização do tráfego.
- Interface interativa de chat com IA embutida.
- Splash Screen de carregamento inicial.
- Integração com API Void Sync: busca e parsing avançado via módulo VoidSyncClient para enriquecer OSINT e geração de wordlists.

## Principais Funcionalidades

### Linha de Comando (CLI)
Use `eviljwtforce` para invocar qualquer módulo:
```bash
# Bruteforce JWT
eviljwtforce bruteforce --token <TOKEN> --wordlist wordlist.txt --alg HS256

# Fuzzing de payload
eviljwtforce fuzz --endpoint https://api.exemplo.com/auth --template payloads/default.json

# OSINT
eviljwtforce osint --target fulano --social Facebook,Instagram --engine Google,Bing --export-json --export-html
``` 

### Interface Gráfica (GUI)
Execute:
```bash
python main.py
```

#### Splash Screen
- Exibe imagem personalizada (700×400px) enquanto a aplicação carrega.

#### Dashboard
- Console de logs em tempo real.
- Contadores de tokens, alvos e injeções.
- Botões para salvar/limpar log e gerar relatório HTML.

#### OSINT Integrado
- Coleta em redes sociais, buscadores, scraping de domínios e vazamentos.
- Filtros por plataforma, TLDs, ccTLDs, limite e delay.
- Exportação em JSON/HTML.

#### Shodan
- Conexão via API Key.
- Consultas: hosts por país, exploits, scan de portas, tecnologias, vulnerabilidades.

#### Pix Fake (Simulador de Confirmação PIX)
- Campos: Código Copia-e-Cola, URL Base, Token JWT, User ID, Valor Pix, Endpoint, TXID, Nome do Recebedor, Data/Hora.
- Botões: Extrair Dados, Gerar Payload, Enviar Webhook, Exportar Payload, Limpar Campos.
- Botões adicionais: 📷 Importar QR (OCR) para ler Pix Copia-e-Cola a partir de imagem.
- 💣 Injetar Automático: executa spoof avançado de webhook e gera TXID realístico.
- Integração com `core/fake_pix_confirmer`: build_payload, send_webhook, save_payload, parse_emv_payload.
- Módulos auxiliares: `modules/fake_pix_module.py` para execução automatizada, `utils/txid_generator.py` (geração de TXID), `utils/ocr_parser.py` (OCR de QR Codes), `utils/webhook_spoofer.py` (spoof de requisições).
- Preview JSON e logs em `output/fake_pix_payload.json` e `output/fake_pix_logs.txt`.
  
Dados enriquecidos exibidos em painel com status de injeção, TXID gerado e respostas do PSP.
- Scroll automático para exibir todos os campos.

#### JWT
- Bruteforce de segredos (HS*).
- Injeção SQL em JWT.
- Decodificação e análise de header/payload, verificação de assinatura, claims.

#### Crypto
- Encrypt/Decrypt AES (vários modos).
- Hash SHA-256, SHA-512, MD5.

#### Wordlist
- Geração baseada em resultados OSINT.
- Variações (leetspeak, sufixos) e filtros de tamanho.
- Exportação para arquivos.

#### Scan
- Scanner de vulnerabilidades em URL alvo.
- Tipos: SQLi, XSS, CSRF, LFI, SSTI, IDOR, Path Traversal.

#### Balance
- Injeção de saldo via requisições forjadas.
- Configuração de endpoint, headers, body e autenticação.

#### Manual Attack
- Painel unificado para executar e testar manualmente diferentes ataques.

#### Fuzzing
- Fuzzing avançado com templates, mutational, guided.
- Progresso e logs ao vivo.

#### SQLi
- Interceptação via Selenium e Burp API.
- Tabela de fluxos com scroll, controles de navegação, exportação de HAR.
- Sugestões IA para payloads.

#### Pipeline
- Execução passo a passo: OSINT → Scan → Fuzz → SQLi.
- Barra de progresso e logs.

#### Relatórios
- Logs e gráficos de pizza (matplotlib).
- Console de relatórios integrado.

#### Configurações
- API Keys persistentes (OpenAI, HuggingFace, Shodan).
- VPN (OpenVPN .ovpn): start/stop.
- Tor: start/stop e redirecionamento de tráfego via SOCKS5.
- Aba "Config" com grupo "Integração de API": combobox de provedores (OpenAI, Mistral, Anthropic, Pentest Muse, Void Sync API) e campos para inserir chaves de acesso.
- Checkboxes para habilitar scraping e geração de wordlists via Void Sync.
- Botões "Testar Conexão" para cada provedor, com feedback visual (✅/❌).
- Injeção de PyOpenSSL no urllib3 para contornar erros de handshake TLS no Windows.
- Configuração via `config/config.yaml`: `api_provider`, bloco `voidsync` (access_key, enable_scraper, enable_wordlist) e `librechat` (endpoint, api_key, model).
- VPN (OpenVPN .ovpn): start/stop.
- Tor: start/stop e redirecionamento de tráfego via SOCKS5.

#### VPN & Tor
- Gerenciamento de processos VPN/Tor via `utils/network/network_manager`.
- Diálogo de logs em tempo real e exibição de IP externo + localização.

#### Chat com IA
- Dock interativo para enviar mensagens.
- Integração com OpenAI, HuggingFace, Ollama, JWTPredictor.
- Sugestões e automação de payloads.

## Estrutura do Projeto
```
Evil-Force-JWT/
├── core/               # Núcleo: brute-force, fuzzing, SQLi, fake_pix_confirmer, report, selenium_interceptor
├── modules/            # Módulos auxiliares: osint, scanner, crypto_utils, token_bruteforce, fake_pix_confirmer
├── gui/                # Interface PyQt5 (qt_interface.py) + assets (ícones, splash.png)
├── ai_module/          # ChatManager e AIWorker para integrações de IA
├── utils/              # Helpers: network_manager, wordlist_utils, proxy_rotator
├── output/             # Saída: osint, fuzzing_logs, fake_pix_payload.json, wordlists
├── reports/            # Relatórios HTML gerados
├── main.py             # Inicializador CLI/GUI
├── README.md           # Documentação (atualizado)
├── requirements.txt    # Dependências
└── LICENSE             # Licença MIT
```

## Instalação
```bash
git clone https://github.com/usuario/Evil-Force-JWT.git
cd Evil-Force-JWT
python3 -m venv evil_jwt_env
# Windows
evil_jwt_env\Scripts\activate
# Linux/macOS
source evil_jwt_env/bin/activate
pip install -r requirements.txt
```

## Uso CLI
Veja `eviljwtforce --help` para comandos disponíveis.

## Uso GUI
```bash
python main.py
```

## Requisitos
- Python 3.11+
- PyQt5, requests, beautifulsoup4, PyJWT, whois, selenium, selenium-wire, cryptography, matplotlib (opcional)
- Cliente OpenVPN, Tor Expert Bundle (opcional para anonimização)

## Licença
MIT License. Veja [LICENSE](LICENSE).

## Disclaimer
Use apenas em ambientes autorizados e para fins educacionais/testes. A equipe não se responsabiliza por usos indevidos.
