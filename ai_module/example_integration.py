from ai_module.error_handler import run_with_error_handling
from ai_module.utils.logger import log_debug

# Exemplo de função que pode falhar
def risky_function():
    import non_existent_module  # Isso causará um ImportError
    return "Tudo certo!"

# Executa a função com tratamento de erros
def main():
    log_debug("Iniciando execução do programa.")
    result = run_with_error_handling(risky_function, context="Testando função arriscada")
    if result:
        print(f"Resultado: {result}")
    log_debug("Execução finalizada.")

if __name__ == "__main__":
    main() 