## Why

Rejestracja narzędzi odbywa się jako side-effect importu — każdy moduł w `builtin_tools/` importuje globalny singleton `tools` i rejestruje się natychmiast przy definicji funkcji. Uniemożliwia to zewnętrznym projektom używającym agenta jako biblioteki dodawanie własnych narzędzi do wspólnego rejestru w sposób jawny i kontrolowany.

## What Changes

- **BREAKING** Nowy moduł `agent/tool.py` z dekoratorem `@tool(...)`, który tylko adnotuje funkcję metadanymi — bez rejestracji
- **BREAKING** Builtin tools (`builtin_tools/*.py`) przestają importować singleton `tools`; używają `@tool(...)` zamiast `@tools.register(...)`
- `ToolsRegistry` zyskuje metodę `include(module_or_package)` do jawnej rejestracji narzędzi z modułu lub całego pakietu (rekurencyjnie)
- `agent/__init__.py` rejestruje builtin tools jawnie przez `tools.include("agent.builtin_tools")` zamiast side-effectu importu
- **BREAKING** `builtin_tools/__init__.py` przestaje być ręczną listą importów

## Capabilities

### New Capabilities

- `tool-decorator`: Standalone dekorator `@tool(...)` adnotujący funkcję metadanymi narzędzia bez rejestracji w żadnym rejestrze
- `tool-include`: Metoda `ToolsRegistry.include()` zbierająca funkcje oznaczone `@tool` z modułu lub rekurencyjnie z pakietu

### Modified Capabilities

## Impact

- `src/agent/tool.py` — nowy plik
- `src/agent/registry.py` — nowa metoda `include()`
- `src/agent/__init__.py` — `import agent.builtin_tools` zastąpione przez `tools.include("agent.builtin_tools")`
- `src/agent/builtin_tools/__init__.py` — ręczne importy usunięte
- `src/agent/builtin_tools/*.py` — każdy plik: `from agent import tools` + `@tools.register(...)` zastąpione przez `from agent.tool import tool` + `@tool(...)`
- Zewnętrzne projekty: `from agent.tool import tool` + `tools.include(mymodule)`
