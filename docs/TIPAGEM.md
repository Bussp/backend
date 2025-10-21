# 🔍 Guia de Tipagem Estática - BusSP

## O que é Tipagem Estática?

**Tipagem estática** significa que os tipos de variáveis são verificados **antes** da execução do código. Python é uma linguagem dinamicamente tipada, mas com **type hints** podemos adicionar anotações de tipo que ferramentas como MyPy verificam.

### Benefícios

- **Detecção precoce de erros**: Encontre bugs de tipo antes de rodar o código
- **Melhor IDE/editor**: Autocompletar mais inteligente e sugestões precisas
- **Documentação viva**: Tipos documentam o código automaticamente
- **Refatoração segura**: Mudanças de tipo são detectadas em todo o codebase
- **Manutenibilidade**: Código mais claro e fácil de entender

## Como Funciona MyPy

MyPy analisa seu código Python e verifica se os tipos estão sendo usados corretamente:

```python
# ✅ Correto
def calculate_score(distance: int) -> int:
    return distance // 100

score: int = calculate_score(1000)  # OK: retorna int

# ❌ Erro detectado pelo MyPy
score: str = calculate_score(1000)  # ERRO: int não é compatível com str
result = calculate_score("1000")    # ERRO: str não é compatível com int
```

## Executando MyPy

```bash
# Verificar todos os arquivos
mypy src/

# Verificar arquivo específico
mypy src/core/services/user_service.py

# Verificar com relatório detalhado
mypy --show-error-codes src/

# Verificar e mostrar apenas erros (sem warnings)
mypy --no-error-summary src/
```

## Configuração Rigorosa

Este projeto usa configuração **strict** no `mypy.ini`:

Isso significa:
- **Todas** as funções precisam de type hints
- **Nenhum** `Any` implícito é permitido
- Retornos devem ter tipos explícitos
- Parâmetros devem ter tipos explícitos
