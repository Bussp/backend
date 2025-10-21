# 🎨 Guia de Linting e Qualidade de Código - BusSP

## O que é Linting?

**Linting** é o processo de analisar código para encontrar:
- **Erros de programação**: Bugs potenciais, código não utilizado
- **Problemas de estilo**: Formatação inconsistente, convenções não seguidas
- **Construções suspeitas**: Padrões que podem causar problemas
- **Más práticas**: Código que funciona mas pode ser melhorado

Pense no linter como um **revisor de código automatizado** que verifica seu código 24/7.

### Por que Linting é Importante?

- **Consistência**: Código uniforme em todo o projeto
- **Manutenibilidade**: Código mais fácil de ler e entender
- **Prevenção de bugs**: Detecta problemas antes de chegar à produção
- **Padrões**: Segue convenções da comunidade Python (PEP 8)
- **Colaboração**: Facilita trabalho em equipe

## Usando Ruff

### Comandos Básicos

```bash
# Verificar problemas (apenas reporta)
ruff check src/ tests/

# Corrigir problemas auto-corrigíveis
ruff check --fix src/ tests/

# Formatar código (estilo consistente)
ruff format src/ tests/

# Verificar E formatar de uma vez
ruff check --fix src/ tests/ && ruff format src/ tests/
```

### Comandos Avançados

```bash
# Verificar arquivo específico
ruff check src/core/services/user_service.py

# Mostrar explicação de regras
ruff check --show-source src/

# Ver diferenças antes de aplicar correções
ruff check --diff src/

# Verificar apenas regras específicas
ruff check --select F,E src/  # F=pyflakes, E=pycodestyle errors

# Ignorar regras específicas
ruff check --ignore E501 src/  # Ignora linha muito longa

# Gerar relatório em formato JSON
ruff check --output-format=json src/ > report.json
```

## O que Ruff Verifica

### 1. Importações Não Utilizadas

```python
# ❌ Ruim - import não usado
import os
from typing import List, Dict  # Dict não é usado

def get_items() -> List[str]:
    return ["a", "b"]

# ✅ Bom - apenas imports necessários
from typing import List

def get_items() -> List[str]:
    return ["a", "b"]

# Ruff corrige automaticamente com --fix
```

### 2. Variáveis Não Utilizadas

```python
# ❌ Ruim
def calculate_score(distance: int, bonus: int) -> int:
    base = distance // 100
    multiplier = 2  # Declarado mas não usado
    return base

# ✅ Bom
def calculate_score(distance: int) -> int:
    base = distance // 100
    return base
```

### 3. Complexidade Excessiva

```python
# ❌ Ruim - muito complexo (complexidade ciclomática alta)
def process(x: int) -> str:
    if x > 0:
        if x < 10:
            if x % 2 == 0:
                if x != 6:
                    return "valid"
    return "invalid"

# ✅ Bom - simplificado
def process(x: int) -> str:
    if 0 < x < 10 and x % 2 == 0 and x != 6:
        return "valid"
    return "invalid"

# Ou melhor ainda
def process(x: int) -> str:
    is_valid = (
        0 < x < 10
        and x % 2 == 0
        and x != 6
    )
    return "valid" if is_valid else "invalid"
```

### 4. Formatação Inconsistente

```python
# ❌ Ruim
def calculate(x:int,y:int)->int:
    result=x+y
    return result

# ✅ Bom - formatado pelo Ruff
def calculate(x: int, y: int) -> int:
    result = x + y
    return result
```

### 5. Ordenação de Imports

```python
# ❌ Ruim - ordem incorreta
from src.core.models.user import User
import os
from typing import List
import sys

# ✅ Bom - ordenado pelo Ruff
import os
import sys
from typing import List

from src.core.models.user import User
```

**Ordem correta**:
1. Imports da biblioteca padrão
2. Imports de terceiros
3. Imports locais do projeto

### 6. Strings de Aspas Inconsistentes

```python
# ❌ Ruim - mistura de aspas
name = "João"
email = 'joao@test.com'
message = "Olá, " + name

# ✅ Bom - consistente (Ruff padroniza para aspas duplas)
name = "João"
email = "joao@test.com"
message = f"Olá, {name}"
```

### 7. Comparações Problemáticas

```python
# ❌ Ruim - comparação com None usando ==
if user == None:
    return

# ✅ Bom - use 'is' para None
if user is None:
    return

# ❌ Ruim - comparação com True/False
if is_active == True:
    process()

# ✅ Bom - teste direto
if is_active:
    process()
```

### 8. List/Dict Comprehensions

```python
# ❌ Ruim - loop desnecessário
result = []
for item in items:
    result.append(item.upper())

# ✅ Bom - list comprehension
result = [item.upper() for item in items]

# ❌ Ruim
users = {}
for user in user_list:
    users[user.id] = user.name

# ✅ Bom - dict comprehension
users = {user.id: user.name for user in user_list}
```

### 9. F-strings vs Concatenação

```python
# ❌ Ruim - concatenação
message = "Olá, " + name + "! Você tem " + str(score) + " pontos."

# ❌ Ruim - .format()
message = "Olá, {}! Você tem {} pontos.".format(name, score)

# ✅ Bom - f-string (mais rápido e legível)
message = f"Olá, {name}! Você tem {score} pontos."
```

### 10. Código Morto

```python
# ❌ Ruim - código nunca executado
def process(value: int) -> str:
    return "processed"
    print("Isso nunca executa")  # Código morto

# ✅ Bom
def process(value: int) -> str:
    return "processed"
```

## Configuração no `pyproject.toml`

```toml
[tool.ruff]
# Comprimento máximo de linha
line-length = 88

# Versão do Python
target-version = "py311"

# Excluir arquivos/diretórios
exclude = [
    ".git",
    ".mypy_cache",
    ".ruff_cache",
    "venv",
    "__pycache__",
]

[tool.ruff.lint]
# Regras ativadas
select = [
    "E",   # pycodestyle errors
    "W",   # pycodestyle warnings
    "F",   # pyflakes
    "I",   # isort (ordenação de imports)
    "B",   # flake8-bugbear (bugs comuns)
    "C4",  # flake8-comprehensions
    "UP",  # pyupgrade (modernização)
]

# Regras ignoradas (se necessário)
ignore = [
    "E501",  # linha muito longa (deixe o formatter lidar)
]

# Permitir correções automáticas
fixable = ["ALL"]

# Nunca corrigir automaticamente
unfixable = []

[tool.ruff.lint.per-file-ignores]
# Ignorar regras específicas em arquivos de teste
"tests/**/*.py" = [
    "S101",  # Permitir asserts em testes
]

[tool.ruff.format]
# Estilo de aspas (double ou single)
quote-style = "double"

# Indentação
indent-style = "space"

# Preferir aspas duplas em docstrings
docstring-code-format = true
```

## Principais Categorias de Regras

### Pyflakes (F)
Detecta erros de programação:
- Imports não utilizados
- Variáveis não definidas
- Código não alcançável

### pycodestyle (E, W)
Verifica estilo PEP 8:
- Espaçamento
- Linhas em branco
- Indentação

### isort (I)
Ordena imports:
- Agrupa por tipo
- Ordena alfabeticamente
- Remove duplicatas

### flake8-bugbear (B)
Encontra bugs comuns:
- Argumentos mutáveis padrão
- Uso incorreto de assert
- Loops problemáticos

### pyupgrade (UP)
Moderniza código:
- Sintaxe antiga → moderna
- Type hints modernos
- F-strings

## Integração com Editor

### VS Code

Instale a extensão Ruff e configure em `settings.json`:

```json
{
    "[python]": {
        "editor.formatOnSave": true,
        "editor.codeActionsOnSave": {
            "source.fixAll": true,
            "source.organizeImports": true
        },
        "editor.defaultFormatter": "charliermarsh.ruff"
    },
    "ruff.lint.enable": true,
    "ruff.format.args": ["--config=pyproject.toml"]
}
```

## Workflow Recomendado

### Antes de Commitar

```bash
# 1. Verificar problemas
ruff check src/ tests/

# 2. Corrigir automaticamente
ruff check --fix src/ tests/

# 3. Formatar código
ruff format src/ tests/

# 4. Verificar tipos (MyPy)
mypy src/

# 5. Executar testes
pytest
```