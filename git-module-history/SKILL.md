---
name: git-module-history
description: Analiza el historial Git y genera documentación técnica histórica por módulos o funcionalidades con un dashboard validado. Usar para documentar la evolución de todo un repositorio, analizar un módulo como Teams o Evaluation Summary, o actualizar docs/commit-history/.
compatibility: Python 3.10 o posterior y Git en PATH; Windows, Linux y macOS.
---

# Historial técnico por módulos

Transformar cambios verificables de Git en una explicación de evolución funcional, no en
un listado de commits. Mantener un flujo simple: dos scripts, dos referencias y dos assets.
El agente interpreta; los scripts recopilan hechos y comprueban consistencia.

## Límites obligatorios

Esta skill solo analiza y documenta. **Nunca** modificar código, corregir bugs, eliminar código,
cambiar configuración, ejecutar código del proyecto, hacer commits (ni amend), push, checkout,
switch, merge, rebase, reset, ni modificar el historial. No cambiar de rama ni hacer fetch.
Git solo lectura: status, branch --show-current, rev-parse, log (incluido --follow), show y diff.
Usar `--no-ext-diff --no-textconv` al inspeccionar diffs para evitar herramientas externas.

Solo crear/actualizar documentación en `docs/commit-history/` y temporales en
`docs/commit-history/.analysis/`. El único dataset es `.analysis/history-data.json`.
No escribir en la propia skill durante su uso, ni crear scripts auxiliares, logs o manifests
en el repositorio. No seguir enlaces/junctions que redirijan la salida fuera de esa ubicación.
El agente debe respetar la misma restricción al escribir Markdown o actualizar `analysis`.
La retirada de documentación generada obsoleta se limita a esa salida según las reglas.

## Recursos y responsabilidad

| Recurso | Uso obligatorio |
|---|---|
| `scripts/analyze_repo.py` | Detecta raíz/rama, inspecciona todo el árbol relevante, lee Git y genera hechos JSON. |
| `assets/ignore-patterns.txt` | El recopilador lo lee; el agente revisa las exclusiones y sus límites. |
| `references/analysis-rules.md` | Leer antes de clasificar: evidencia, agrupación, confianza, merges, conteos y contrato JSON/Markdown. |
| `references/module-history-template.md` | Leer y usar como base de cada `<module>.md`. |
| `assets/general-dashboard-template.md` | Leer y usar para `general.md`, con tablas derivadas de la misma unión de commits. |
| `scripts/validate_output.py` | Ejecutar después de escribir; valida realmente cobertura, tablas, hashes, fechas, tipos y estructura. |

El agente comprende el propósito de módulos, clasifica, interpreta diffs, agrupa features
compuestas, identifica patrones/estabilización y redacta. El recopilador no decide tipos,
causas, etapas ni agrupaciones semánticas. Su mapa de módulos es preliminar.

## Ejecución

Resolver `<SKILL_DIR>` como la carpeta que contiene este SKILL.md; no asumir que está
dentro del repositorio. Sustituir las rutas ilustrativas y conservar comillas para espacios.
Usar `python` o el ejecutable Python 3.10+ disponible (`python3` / `py -3`). No copiar
los scripts al proyecto. No pasar una rama: siempre se captura la actualmente activa.

```text
python "<SKILL_DIR>/scripts/analyze_repo.py" --repo "<REPO_DIR>"
python "<SKILL_DIR>/scripts/validate_output.py" --repo "<REPO_DIR>"
```

Ambos aceptan `--debug` para mostrar traceback. Sin debug, errores uniformes y salida
distinta de cero. El validador importa helpers del recopilador sin generar `__pycache__`.
Se puede invocar desde cualquier subdirectorio del repositorio con `--repo`.
Repositorio sin commits o bare: detenerse con error claro; no inicializarlo ni modificarlo.
HEAD separado: se registra `DETACHED_HEAD` y se usa el snapshot alcanzable desde HEAD,
advirtiendo que no hay rama activa; nunca crear/cambiar rama para resolverlo.

## Flujo completo obligatorio

1. **Validar repositorio Git.** Confirmar directorio; leer instrucciones/documentación pertinente
   del proyecto como contexto. Antes de regenerar, leer el dataset previo y recordar en memoria
   qué documentos pertenecen a la skill; detectar conflictos con archivos manuales.
2. **Detectar raíz y rama.** Usar `git rev-parse --show-toplevel` y
   `git branch --show-current`; no modificar el repositorio. El script repite estas comprobaciones.
3. **Ejecutar `scripts/analyze_repo.py`.** Este realiza automáticamente los pasos 4–9.
4. **Leer `assets/ignore-patterns.txt`.** El script carga las exclusiones editables del archivo,
   no una lista hardcodeada; el agente también revisa su alcance. No modificar assets al analizar
   un proyecto. Un ajuste permanente de la skill requiere una petición separada del usuario.
5. **Inspeccionar estructura completa.** Desde raíz, no solo src. Inventario recursivo de carpetas
   y archivos, respetando exclusiones, enlaces y repositorios anidados. Revisar estructuras
   backend/frontend/apps/packages/services/modules/prisma/database/tests/scripts/config/
   infrastructure/docs y manifiestos cuando existan. El árbol del disco no sustituye al snapshot.
6. **Recopilar historial Git.** Todo lo alcanzable desde el HEAD capturado, sin first-parent ni
   ventanas arbitrarias. Guardar hashes, fechas, mensajes, padres y archivos/estados.
7. **Detectar merges y renombres.** Diferencias contra cada padre en merges; similitud de Git
   para renombres, con rutas origen/destino. No contar estos datos como features automáticamente.
8. **Detectar posibles módulos.** Carpetas, nombres y convenciones del framework; conservar
   múltiples asignaciones por commit y candidatos históricos.
9. **Generar `.analysis/history-data.json`.** Un único dataset con hechos y un bloque `analysis`
   vacío. La regeneración lo reemplaza. Confirmar que HEAD/rama no cambiaron al recopilar.
10. **Leer `references/analysis-rules.md` completo.** Obligatorio antes de decidir categorías.
    Leer JSON, código del snapshot y documentación pertinente. Confirmar mapa conceptual y
    alcance completo o enfocado. Advertir dirty tree/shallow/HEAD separado cuando aplique.
11. **Clasificar commits.** Revisar diffs y contexto; Feature, Fix, Refactor o Configuration.
    Registrar evidencia, confianza y razón en `analysis`; justificar exclusiones. Revisar
    explícitamente cada merge sin duplicar trabajo integrado. `git log --follow` si ayuda
    a mantener continuidad de una ruta movida/renombrada. Los hechos no se editan.
12. **Agrupar cambios relacionados.** Por funcionalidad, continuidad, archivos, modelos,
    endpoints y proximidad temporal; no forzar agrupaciones sin evidencia.
13. **Analizar evolución histórica.** Etapas, alta actividad, fixes concentrados, modificaciones
    repetidas, retornos a una feature y estabilización. Separar hechos e interpretación;
    nunca evaluar personas ni diagnosticar bugs a partir de volumen.
14. **Leer `references/module-history-template.md`.** Es la base real de cada documento.
15. **Generar `<module>.md`.** Rellenar dashboard, árbol conceptual, descripción actual,
    evolución agrupada, análisis con indicadores y tabla completa de evidencia al final.
16. **Repetir por módulo.** Slugs kebab-case únicos; impactos específicos de cada módulo.
    Registrar módulos finales y commits en `analysis.documented_modules`. Reconstruir archivos
    existentes, no anexar. Retirar solo documentos generados obsoletos identificados previamente.
17. **Leer `assets/general-dashboard-template.md`.** Usar su estructura real.
18. **Generar `general.md`.** Dashboard sin historial individual; contar unión de commits,
    incluir alcance y limitaciones; tablas consistentes con cada módulo. Omitir sección de
    concentración si no hay evidencia. Guardar decisiones exclusivamente en `analysis` del JSON.
19. **Ejecutar `scripts/validate_output.py`.** Debe terminar con `VALIDATION PASSED` y código 0.
20. **Corregir inconsistencias.** Atender todos los problemas enumerados, tanto JSON interpretativo
    como documentos. Revisar manualmente calidad semántica y evidencias que el script no prueba.
21. **Revalidar.** Repetir hasta coherencia completa. Si cambia HEAD, volver a recopilar y
    reconstruir; no ocultar diferencias ni alterar hechos para superar checks.
22. **Finalizar.** Informar ubicación, alcance, módulos, commits únicos, límites relevantes y
    resultado de validación. Nunca declarar éxito con validación fallida o flujo incompleto.

## Salida y actualización

```text
docs/commit-history/
├── general.md
├── teams.md                  # Nombres reales según mapa conceptual
├── evaluations.md
└── .analysis/
    └── history-data.json
```

«Analiza todo el repositorio y genera la documentación histórica» → alcance completo.
«Analiza el módulo Teams» / «Analiza la evolución histórica de Evaluation Summary» →
recopilar todo para contexto, documentar alcance enfocado según las reglas, dashboard
explícitamente parcial. «Actualiza la documentación histórica del proyecto» → reconstruir
alcance completo desde el snapshot actual. No mezclar documentos de ejecuciones diferentes.
La documentación es del historial local disponible, no de ramas remotas no alcanzables.

## Errores y warnings

Formato uniforme de scripts y de errores que deba reportar el agente:

```text
[ERROR] <ERROR_CODE>

<Descripción>

Entrada recibida:
<valor>

Acción:
<cómo corregirlo>
```

- `INVALID_INPUT`: ruta/argumentos inválidos, sin repositorio de trabajo.
- `GIT_ERROR`: Git ausente, historial vacío, objetos no disponibles o consulta fallida.
- `ANALYSIS_ERROR`: recopilación o generación estructurada imposible/incompleta.
- `OUTPUT_ERROR`: permisos, rutas redirigidas o escritura fallida.
- `VALIDATION_ERROR`: dataset/documentación ausente, malformado o inconsistente.

Warnings no bloqueantes: `[WARNING] LOW_CONFIDENCE`, `[WARNING] AMBIGUOUS_MODULE` y
`[WARNING] CROSS_MODULE_CHANGE`, seguidos de explicación y acción pertinente. El script
advierte asignación preliminar y commits transversales; el agente detalla ambigüedades reales.
No confundir que el script advierta baja confianza inicial con una clasificación automática.

El validador acumula errores documentales en una misma ejecución: secciones, archivos,
placeholders, fechas, orden, hashes desconocidos/duplicados, tablas y conteos, cobertura,
merges sin revisión y dataset obsoleto. Un JSON ilegible puede impedir comprobaciones posteriores.
No hay dependencias externas ni generación automática de prosa: el flujo completo requiere
que el agente realice los pasos interpretativos entre ambos scripts.
