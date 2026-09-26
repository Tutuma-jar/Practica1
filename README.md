# Git Module History

Skill para analizar cómo evolucionan los módulos y funcionalidades de un repositorio Git. Relaciona y agrupa commits, interpreta cambios relevantes y genera documentación por módulo y un dashboard general en `docs/commit-history/`. Incluye validación de la documentación y sus estadísticas.

Está destinada únicamente al análisis y la documentación: consulta el historial sin modificar código ni cambiar de rama. Los scripts recopilan y validan datos; el agente interpreta los cambios y redacta los documentos.

## Instalación global

Necesitas **OpenCode o Claude Code**, **Python 3.10 o posterior** y **Git** instalados y disponibles para el agente.

1. Descarga el ZIP de esta rama desde **Code → Download ZIP** en GitHub y descomprímelo.
2. Copia la carpeta completa **`git-module-history`**, incluidos `SKILL.md`, `scripts`, `references` y `assets`.
3. Pégala en la carpeta global de skills de tu usuario, según la herramienta:

   | Herramienta | Windows | Linux / macOS |
   |---|---|---|
   | OpenCode | `C:\Users\<tu-usuario>\.config\opencode\skills\` | `~/.config/opencode/skills/` |
   | Claude Code | `C:\Users\<tu-usuario>\.claude\skills\` | `~/.claude/skills/` |

   Crea las carpetas que falten. El archivo principal debe quedar, por ejemplo, en `C:\Users\<tu-usuario>\.config\opencode\skills\git-module-history\SKILL.md`. Copia la carpeta una sola vez en la ubicación correspondiente; no copies únicamente `SKILL.md`.

4. Cierra y vuelve a abrir la herramienta para que detecte la skill. Quedará disponible globalmente para tus repositorios.

## Uso

Abre el repositorio que quieras documentar en tu herramienta y pide al agente, en lenguaje natural:

> Usa la skill git-module-history para analizar todo el repositorio y generar la documentación histórica.

También puedes solicitar un módulo o una actualización:

> Usa git-module-history para analizar la evolución del módulo Teams.

> Usa git-module-history para actualizar la documentación histórica del proyecto.

El agente analiza el historial alcanzable desde la rama actual, genera los documentos y ejecuta la validación. No necesitas ejecutar los scripts manualmente.

## Resultado

- **`docs/commit-history/general.md`**: dashboard con módulos, tipos de cambios y actividad.
- **`docs/commit-history/<modulo>.md`**: descripción, evolución agrupada, patrones históricos y commits de evidencia.
- **`docs/commit-history/.analysis/history-data.json`**: dataset único con hechos de Git y decisiones del análisis.

El análisis de un módulo produce un dashboard de alcance enfocado. La generación se considera completa cuando la validación termina correctamente.

## Advertencia sobre el alcance del análisis

El análisis del historial Git puede consumir una cantidad considerable de tokens, especialmente en repositorios grandes o con muchos commits.

Para reducir el consumo y mantener el análisis manejable, se recomienda:

- Analizar un solo módulo por ejecución.
- Si se necesita analizar varios módulos, ejecutar la skill por separado para cada uno.
- Especificar un rango de tiempo cuando el historial sea muy extenso, por ejemplo, los últimos 3 meses, 6 meses o desde una fecha determinada.
- Evitar analizar todo el repositorio y todo su historial salvo que sea realmente necesario.

Ejemplo recomendado:

```text
Usa git-module-history para analizar la evolución del módulo Teams durante los últimas 2 semanas.
```

Limitar el análisis por módulo o período reduce significativamente la cantidad de commits que deben interpretarse y, por tanto, el consumo de tokens.
