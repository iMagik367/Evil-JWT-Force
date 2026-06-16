from modules.jwt_utils import JWTIntegrator
from config.config_loader import load_config
import logging

logging.basicConfig(level=logging.INFO)

def test_full_flow(token):
    config = load_config()
    
    # Executa ferramentas externas
    integrator = JWTIntegrator()
    results = integrator._run_parallel(token)
    
    # Analisa resultados
    consolidated = integrator.analyze_results(results)
    
    # Integração com PentestGPT
    from pentestgpt import PentestGPT
    gpt = PentestGPT(api_key=config['pentestgpt']['api_key'])
    
    report = gpt.generate_report({
        'findings': consolidated,
        'token': token
    })
    
    return report

def main():
    test_token = generate_test_token()
    print(f"Token de teste gerado: {test_token}")
    
    report = test_full_flow(test_token)
    
    print("\nResultado da análise:")
    print(json.dumps(report, indent=2))

if __name__ == "__main__":
    main()