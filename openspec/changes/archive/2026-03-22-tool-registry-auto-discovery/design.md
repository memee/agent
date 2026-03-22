## Context

Aktualny mechanizm rejestracji narzędzi opiera się na side-effectach importu: każdy moduł w `builtin_tools/` importuje globalny singleton `tools` i rejestruje się przez `@tools.register(...)` przy definicji funkcji. `builtin_tools/__init__.py` utrzymuje ręczną listę importów wyzwalających te side-effecty.

Zmiana wprowadza jawną rejestrację: dekorator `@tool(...)` tylko adnotuje funkcję, a metoda `include()` jawnie zbiera i rejestruje narzędzia z modułu lub pakietu.

## Goals / Non-Goals

**Goals:**

- Rejestracja narzędzi jest jawnym aktem, nie side-effectem importu
- Zewnętrzny projekt może dodawać własne narzędzia do singletona `tools` przez `tools.include(module)`
- Dodanie nowego builtin tool nie wymaga edycji `builtin_tools/__init__.py`
- `agent/tool.py` nie ma zależności od reszty frameworka (zero circular imports)

**Non-Goals:**

- Dynamiczne ładowanie pluginów w runtime (po starcie agenta)
- Entry points / setuptools plugin mechanism
- Wiele instancji rejestru z różnymi podzbiorami builtin tools

## Decisions

### D1: Dekorator `@tool` jako czysty annotator

`@tool(...)` zapisuje metadane na funkcji jako atrybut `_tool_meta: dict` i zwraca funkcję bez zmian. Nie dotyka żadnego rejestru.

```python
# agent/tool.py
def tool(name, group=None, validators=None, domain=None):
    def decorator(fn):
        fn._tool_meta = {
            "name": name,
            "group": group,
            "validators": validators or {},
            "domain": domain,
        }
        return fn
    return decorator
```

**Alternatywa odrzucona**: globalny `_pending` dict w `tool.py` (class-level registry). Wprowadza globalny stan, komplikuje testy z wieloma rejestrami.

### D2: `include()` akceptuje moduł lub string

```python
registry.include(myproject.tools)         # obiekt modułu
registry.include("agent.builtin_tools")   # string → auto-import
```

Wewnętrznie: jeśli string — `importlib.import_module()`, potem ta sama ścieżka co dla modułu.

### D3: Rekurencyjne skanowanie pakietów

Jeśli argument jest pakietem (ma `__path__`), `include()` używa `pkgutil.walk_packages()` do rekurencyjnego importu wszystkich submodułów, następnie zbiera funkcje z `_tool_meta` ze wszystkich z nich.

Jeśli argument jest zwykłym modułem — skanuje tylko jego namespace.

**Alternatywa odrzucona**: skanowanie tylko `__init__.py` pakietu. Wymaga przeniesienia wszystkich `@tool` do `__init__.py` — cofa się do ręcznego utrzymywania listy.

### D4: Zachowanie metody `register()` na instancji

`ToolsRegistry.register()` (dekorator instancji) pozostaje dla przypadków programatycznej rejestracji. `@tool` + `include()` to nowy, preferowany styl deklaratywny.

## Risks / Trade-offs

- **Circular import** → `agent/tool.py` musi być całkowicie wolny od importów z `agent.*`. Weryfikacja: `python -c "from agent.tool import tool"` bez ładowania reszty frameworka.
- **`pkgutil.walk_packages` importuje wszystkie submoduły** → jeśli submoduł ma błąd na poziomie importu, `include()` go zgłosi. Jest to pożądane zachowanie (fail fast), ale warto to odnotować.
- **Breaking change dla istniejących narzędzi** → każdy plik w `builtin_tools/` wymaga mechanicznej zmiany dekoratora. ~8 plików, niskie ryzyko.

## Migration Plan

1. Dodaj `agent/tool.py` z dekoratorem `@tool`
2. Dodaj `ToolsRegistry.include()` w `registry.py`
3. Zaktualizuj każdy plik w `builtin_tools/` (zmiana dekoratora)
4. Wyczyść `builtin_tools/__init__.py`
5. Zaktualizuj `agent/__init__.py` — zastąp side-effect przez `tools.include("agent.builtin_tools")`

Rollback: przywrócenie `builtin_tools/__init__.py` i oryginalnych dekoratorów.
