## ADDED Requirements

### Requirement: Dekorator tool adnotuje funkcję metadanymi

Moduł `agent.tool` SHALL udostępniać dekorator `tool(name, group, validators, domain)`, który zapisuje metadane na funkcji jako atrybut `_tool_meta` i zwraca funkcję bez żadnych efektów ubocznych. Dekorator nie rejestruje funkcji w żadnym rejestrze.

#### Scenario: Funkcja po dekoracji ma atrybut _tool_meta

- **WHEN** funkcja jest udekorowana przez `@tool("my_tool", group="mygroup")`
- **THEN** funkcja ma atrybut `_tool_meta` z kluczami `name`, `group`, `validators`, `domain`

#### Scenario: Dekorator nie zmienia zachowania funkcji

- **WHEN** udekorowana funkcja jest wywołana z poprawnymi argumentami
- **THEN** zwraca ten sam wynik co bez dekoratora

#### Scenario: Import agent.tool nie ładuje reszty frameworka

- **WHEN** wykonywany jest `from agent.tool import tool` w izolowanym środowisku (bez załadowanego `agent`)
- **THEN** import się powodzi bez importowania `agent.registry`, `agent.sandbox` ani innych modułów frameworka

### Requirement: Domyślne wartości metadanych

Dekorator `tool` SHALL przyjmować `group=None`, `validators=None`, `domain=None` jako wartości domyślne. `validators` SHALL być zapisywany jako pusty dict gdy `None`.

#### Scenario: Wywołanie tylko z nazwą

- **WHEN** funkcja jest udekorowana przez `@tool("my_tool")`
- **THEN** `fn._tool_meta["group"]` jest `None`, `fn._tool_meta["validators"]` jest `{}`, `fn._tool_meta["domain"]` jest `None`
