# Instalação do Evil JWT Force

Este documento descreve como instalar o Evil JWT Force em diferentes sistemas operacionais.

## Requisitos do Sistema

- Python 3.8 ou superior
- Java Runtime Environment (JRE) 8 ou superior
- Chrome ou Firefox (para funcionalidades Selenium)
- 4GB RAM mínimo
- 1GB espaço em disco
- Git (para instalação)

## Instalação

O Evil JWT Force oferece dois métodos de instalação:

1. **Instalador Gráfico (Recomendado)**
   - Interface amigável
   - Opções de instalação personalizáveis
   - Feedback visual do progresso
   - Log detalhado da instalação

2. **Instalação via Linha de Comando**
   - Método alternativo
   - Útil para automação ou servidores

### Windows

1. Instale o Python 3.8 ou superior
   - Baixe do [site oficial do Python](https://www.python.org/downloads/)
   - Marque a opção "Add Python to PATH" durante a instalação

2. Instale o Java Runtime Environment
   - Baixe do [site oficial da Oracle](https://www.java.com/download/)
   - Ou use o [OpenJDK](https://adoptopenjdk.net/)

3. Instale o Git
   - Baixe do [site oficial do Git](https://git-scm.com/download/win)

4. Clone o repositório
   ```bash
   git clone https://github.com/seu-usuario/evil-jwt-force.git
   cd evil-jwt-force
   ```

5. Execute o instalador
   - Dê um duplo clique em `install.bat`
   - O instalador gráfico será iniciado automaticamente
   - Se o instalador gráfico falhar, a instalação via linha de comando será tentada

### Kali Linux

1. Atualize o sistema
   ```bash
   sudo apt update
   sudo apt upgrade
   ```

2. Instale as dependências do sistema
   ```bash
   sudo apt install python3 python3-pip python3-venv git default-jre
   ```

3. Clone o repositório
   ```bash
   git clone https://github.com/seu-usuario/evil-jwt-force.git
   cd evil-jwt-force
   ```

4. Execute o instalador
   ```bash
   chmod +x install.sh
   ./install.sh
   ```
   - O instalador gráfico será iniciado automaticamente
   - Se o instalador gráfico falhar, a instalação via linha de comando será tentada

## Opções do Instalador Gráfico

O instalador gráfico oferece as seguintes opções:

1. **Criar ambiente virtual**
   - Recomendado para isolar as dependências
   - Evita conflitos com outros pacotes Python

2. **Instalar dependências**
   - Instala todas as bibliotecas necessárias
   - Inclui ferramentas de desenvolvimento

3. **Criar atalho global**
   - Permite executar o programa de qualquer diretório
   - Adiciona o comando `evil-jwt-force` ao PATH

4. **Diretório de instalação**
   - Escolha onde o programa será instalado
   - Use o botão "Procurar..." para navegar

## Desinstalação

### Windows
1. Execute `uninstall.bat`
2. Siga as instruções na tela

### Kali Linux
1. Execute `./uninstall.sh`
2. Siga as instruções na tela

## Solução de Problemas

### Erro do Instalador Gráfico
Se o instalador gráfico falhar:
1. Verifique se o PyQt5 está instalado:
   ```bash
   pip install PyQt5
   ```
2. Tente a instalação via linha de comando:
   ```bash
   python install_deps.py
   ```

### Erro de Dependências
Se encontrar erros durante a instalação das dependências:
1. Verifique se o Python 3.8+ está instalado
2. Verifique se o pip está atualizado
3. Tente instalar as dependências manualmente:
   ```bash
   pip install -r requirements.txt
   ```

### Erro de Permissão
Se encontrar erros de permissão no Linux:
1. Verifique se você tem permissões de superusuário
2. Tente executar com sudo:
   ```bash
   sudo ./install.sh
   ```

### Erro do Selenium
Se o Selenium não funcionar:
1. Verifique se o Chrome/Firefox está instalado
2. Verifique se o webdriver está atualizado
3. Tente reinstalar o webdriver:
   ```bash
   pip install --upgrade webdriver-manager
   ```

## Suporte

Para reportar problemas ou solicitar ajuda:
1. Abra uma issue no GitHub
2. Descreva o problema detalhadamente
3. Inclua logs de erro se disponíveis
4. Especifique seu sistema operacional e versão 