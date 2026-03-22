## 1. Dekorator @tool

- [x] 1.1 Utwórz `src/agent/tool.py` z dekoratorem `tool(name, group, validators, domain)` zapisującym `_tool_meta` na funkcji
- [x] 1.2 Zweryfikuj brak circular imports: `python -c "from agent.tool import tool"` nie powinno ładować `agent.registry` ani `agent.sandbox`

## 2. Metoda include() w ToolsRegistry

- [x] 2.1 Dodaj metodę `include(module_or_package)` w `src/agent/registry.py` — akceptuje obiekt modułu lub string
- [x] 2.2 Zaimplementuj skanowanie namespace modułu w poszukiwaniu funkcji z `_tool_meta`
- [x] 2.3 Dodaj wykrywanie pakietów (`__path__`) i rekurencyjne importowanie submodułów przez `pkgutil.walk_packages()`

## 3. Migracja builtin tools

- [x] 3.1 Zaktualizuj `src/agent/builtin_tools/hello_world.py`: `@tools.register(...)` → `@tool(...)`
- [x] 3.2 Zaktualizuj `src/agent/builtin_tools/http_get.py`
- [x] 3.3 Zaktualizuj `src/agent/builtin_tools/http_post.py`
- [x] 3.4 Zaktualizuj `src/agent/builtin_tools/http_download.py`
- [x] 3.5 Zaktualizuj `src/agent/builtin_tools/read_file.py`
- [x] 3.6 Zaktualizuj `src/agent/builtin_tools/write_file.py`
- [x] 3.7 Zaktualizuj `src/agent/builtin_tools/delegate.py`
- [x] 3.8 Zaktualizuj `src/agent/builtin_tools/analyze_image.py`

## 4. Wyczyszczenie __init__.py i integracja

- [x] 4.1 Wyczyść `src/agent/builtin_tools/__init__.py` — usuń wszystkie ręczne importy
- [x] 4.2 Zaktualizuj `src/agent/__init__.py` — zastąp `import agent.builtin_tools` przez `tools.include("agent.builtin_tools")`
- [x] 4.3 Eksportuj `tool` w `src/agent/__init__.py` (`from agent.tool import tool`) i dodaj do `__all__`

## 5. Weryfikacja

- [x] 5.1 Uruchom istniejące testy — wszystkie powinny przejść
- [x] 5.2 Sprawdź `tools.names()` po starcie — lista narzędzi musi być identyczna jak przed zmianą
