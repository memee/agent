## ADDED Requirements

### Requirement: include() rejestruje narzędzia z modułu

`ToolsRegistry` SHALL udostępniać metodę `include(module_or_package)`, która skanuje podany moduł w poszukiwaniu funkcji z atrybutem `_tool_meta` i rejestruje je w rejestrze. Metoda przyjmuje obiekt modułu lub string z nazwą pakietu.

#### Scenario: Rejestracja narzędzi z obiektu modułu

- **WHEN** `registry.include(some_module)` jest wywołane, a `some_module` zawiera funkcje z `_tool_meta`
- **THEN** wszystkie funkcje z `_tool_meta` są zarejestrowane w rejestrze pod nazwami z `_tool_meta["name"]`

#### Scenario: Rejestracja przez string z nazwą modułu

- **WHEN** `registry.include("mypackage.tools")` jest wywołane
- **THEN** moduł jest importowany, a jego narzędzia rejestrowane tak samo jak przy przekazaniu obiektu modułu

#### Scenario: Funkcje bez _tool_meta są pomijane

- **WHEN** moduł zawiera mieszankę funkcji z `_tool_meta` i bez
- **THEN** tylko funkcje z `_tool_meta` są rejestrowane

### Requirement: include() rekurencyjnie skanuje pakiety

Gdy argument jest pakietem (posiada atrybut `__path__`), `include()` SHALL rekurencyjnie importować wszystkie submoduły pakietu i zbierać narzędzia z każdego z nich.

#### Scenario: Rejestracja wszystkich narzędzi z pakietu

- **WHEN** `registry.include("agent.builtin_tools")` jest wywołane, a pakiet ma submoduły z `@tool`
- **THEN** narzędzia ze wszystkich submodułów są zarejestrowane bez konieczności ręcznego importowania submodułów

#### Scenario: Zwykły moduł nie jest skanowany rekurencyjnie

- **WHEN** argument nie posiada `__path__` (jest zwykłym modułem, nie pakietem)
- **THEN** skanowany jest tylko namespace tego modułu

### Requirement: include() jest idempotentne dla tej samej nazwy narzędzia

Ponowne wywołanie `include()` z tym samym modułem SHALL nadpisać istniejące wpisy (ostatni wygrywa), nie powodując błędu ani duplikatów.

#### Scenario: Podwójne include() nie duplikuje narzędzi

- **WHEN** `registry.include(module)` jest wywołane dwukrotnie z tym samym modułem
- **THEN** w rejestrze każde narzędzie z modułu występuje dokładnie raz
