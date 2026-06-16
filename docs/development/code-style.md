# Guia de Estilo de Código

O projeto segue as melhores práticas de Python:

- **Black** para formatação automática
- **isort** para organização de imports
- **flake8** para linting
- **mypy** para verificação de tipos
- **docstrings** no padrão Google

## Exemplo de função documentada
```python
def soma(a: int, b: int) -> int:
    """Soma dois números inteiros.

    Args:
        a (int): Primeiro número
        b (int): Segundo número

    Returns:
        int: Resultado da soma
    """
    return a + b
``` 