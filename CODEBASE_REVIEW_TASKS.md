# Revisión del código base: problemas detectados y tareas propuestas

## 1) Tarea para corregir un error tipográfico
**Problema detectado:** En el log de orquestación se imprime `functional Testing` con una capitalización inconsistente respecto al resto de fases y encabezados.

- Evidencia: `print("\n--- Phase 1: functional Testing (Navigator) ---")` en `quantum_main.py`.

**Tarea propuesta:**
- Corregir el texto a `Functional Testing` para mantener consistencia en mensajes de salida y reportes.
- Verificar que no haya otras variaciones de capitalización en encabezados de fase.

## 2) Tarea para corregir una falla
**Problema detectado:** La validación de `SameSite` en cookies es sensible a mayúsculas/minúsculas y puede omitir casos inseguros (`none` en minúsculas).

- Evidencia: `if same_site == 'None' or not same_site:` en `quantum_qe_core/skills/scanner.py`.

**Tarea propuesta:**
- Normalizar `same_site` (`str(...).lower()`) antes de evaluarlo.
- Tratar como débiles todos los valores vacíos o equivalentes a `none` (sin importar el casing).
- Añadir cobertura de prueba para `None`, `none`, `NONE`, cadena vacía y ausencia del campo.

## 3) Tarea para corregir una discrepancia en comentarios/documentación
**Problema detectado:** El README indica comandos con `main.py`, pero el entrypoint real del flujo actual está en `quantum_main.py`.

- Evidencia: Se documenta `python main.py` en `README.md`, mientras el archivo existente es `quantum_main.py`.

**Tarea propuesta:**
- Actualizar el README para usar `python quantum_main.py` en ejemplos de Setup/CLI.
- Revisar la sección de componentes para reflejar la arquitectura actual (`quantum_qe_core/*`) y diferenciar explícitamente el código legado (`legacy_mvp/*`).

## 4) Tarea para mejorar una prueba
**Problema detectado:** No hay pruebas unitarias enfocadas en reglas críticas del escaneo pasivo de cookies/cabeceras (lógica con alto riesgo de regresión).

**Tarea propuesta:**
- Crear `tests/test_scanner.py` con pruebas unitarias de `SecurityAuditor` para:
  - detección de headers faltantes,
  - detección de flags inseguros de cookies,
  - variantes de `SameSite` con distinto casing,
  - y comportamiento acumulativo de `findings` entre ejecuciones (para decidir si debe reiniciarse por corrida).
- Integrar estas pruebas en el comando estándar de CI (por ejemplo, `pytest`).
