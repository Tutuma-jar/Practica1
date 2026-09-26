# Daily-menu

## Vista general

| Elemento | Detalle |
|---|---|
| Módulo / Funcionalidad | Daily-menu |
| Estado | Activo |
| Total de commits | 51 |
| Features | 21 |
| Fixes | 25 |
| Refactors | 0 |
| Configuración | 5 |
| Primer cambio registrado | 2026-08-18 |
| Último cambio registrado | 2026-09-16 |
| Días activos | 14 |
| Rama y snapshot | develop; 516aac4bce5739619f562e7a1bd4e674edfa432f |
| Alcance | Catálogo, disponibilidad, stock y turnos; incluye impactos directos en pedidos, migraciones, auditoría y seeds. |
| Base histórica | 337 commits recopilados en .analysis/history-data.json; historial local no shallow. |

Las fechas corresponden al committer en UTC. Se documentan 51 commits únicos no merge, seleccionados por diffs y contexto funcional, sin ventanas temporales ni recorrido first-parent. No se asignan cambios propios de merges a este módulo. Los commits compartidos cuentan una vez aquí; los totales globales deben calcularse mediante unión, no sumando módulos.

La revisión fue estática: se inspeccionaron historial, snapshot, migraciones y pruebas sin ejecutar el proyecto. El estado observado durante la revisión solo mostraba `docs/commit-history/` sin seguimiento. Este documento conserva el conjunto acordado; la actualización del bloque `analysis` del dataset corresponde a una etapa posterior.

## Estructura

```text
Daily-menu
├── Catálogo
│   ├── Platos, categorías, precios y baja lógica
│   └── Menús reutilizables: composición, edición y duplicación
├── Turnos
│   ├── Apertura directa o desde menú reutilizable
│   ├── Consulta del turno operativo
│   └── Cierre confirmado y bloqueo por pedidos pendientes
├── Disponibilidad
│   ├── Consulta agrupada por turno
│   ├── Desactivación y reactivación autorizadas desde cocina
│   └── Compatibilidad con la ruta histórica de menú
├── Stock
│   ├── Asignaciones, límites, ajustes y versiones
│   ├── Reservas y liberaciones vinculadas a consumos
│   └── Idempotencia y eventos operativos
└── Persistencia y trazabilidad
    ├── Auditoría transaccional y registros append-only
    ├── Migraciones y restricciones SQL
    └── Seeds básicos, históricos y de turno abierto
```

## Descripción

En el snapshot, `src/modules/daily-menu/daily-menu.module.ts` integra autenticación y cocina, registra los controladores operativo y de administración, y exporta repositorio y servicio para pedidos. El catálogo histórico también se expone desde `src/modules/orders/controllers/menu.controller.ts`.

**Catálogo y menús reutilizables.** `MenuManagementController` administra platos activos y plantillas de menú; sus escrituras están restringidas a `ADMIN`. `MenuManagementRepository` valida componentes existentes y activos, evita duplicados, comprueba turnos abiertos antes de editar una plantilla y conserva componentes referenciados por asignaciones históricas. Los modelos principales son `MenuItem`, `DailyMenu` y `DailyMenuItem`.

**Disponibilidad y stock.** La consulta devuelve `{ shift, items }`, con nombre, categoría, contadores, estado y versión. La disponibilidad se calcula como `max(0, initialLimit + adjustmentQuantity - confirmedQuantity + releasedQuantity)`. Los ajustes utilizan bloqueo de filas, transacción serializable, versión esperada, confirmación de cantidades e idempotencia. Las lecturas admiten los cinco roles operativos; el cambio de disponibilidad corresponde a `KITCHEN`, con autorización PIN de administrador o supervisor. La ruta histórica de actualización delega en el flujo autorizado de daily-menu.

**Turnos.** La apertura puede ser directa o desde una plantilla reutilizable. La primera exige autorización PIN adicional; `openDailyMenu`, desde una plantilla, utiliza el rol autenticado y no contiene esa misma llamada. La selección prioriza un turno abierto. El cierre exige confirmación y PIN, rechaza pedidos `OPEN` o `SENT_TO_KITCHEN` y cierra las asignaciones por `shiftId` en la transacción de cierre.

**Integración y trazabilidad.** Pedidos prioriza una asignación activa sobre el stock genérico, incluso para categorías distintas de `DAILY_MENU`. Las devoluciones siguen el consumo persistido y su asignación original. Los eventos de apertura, stock y cierre se publican después de persistir. La auditoría registra operaciones de catálogo, disponibilidad y turnos; una migración protege `daily_menu_stock_adjustments` y `audit_logs` frente a UPDATE/DELETE.

## Evolución del módulo

### 2026-08-18 a 2026-08-21 — Catálogo persistido y stock integrado con pedidos

El catálogo nace dentro del modelo de pedidos, con precios y disponibilidad. La reserva y devolución de cantidades pasan a ejecutarse en la misma transacción que modifica los pedidos. Después se publica una API con UUID persistidos para sustituir los identificadores demostrativos usados por la integración.

El seed deja de sobrescribir disponibilidad y cantidades operativas al repetirse. Las rutas reciben guardas y la actualización de disponibilidad incorpora publicación de eventos, conectando catálogo y terminales operativas.

Cambios relevantes: modelo `MenuItem` y reserva transaccional (`f9a1405`, `7ddd750`), catálogo con UUID y categorías (`db61259`), preservación del seed (`0d670ee`), permisos y propagación (`f9cf8fd`, `6e389cf`).

### 2026-09-02 a 2026-09-06 — Reconstrucción del modelo diario y consolidación inicial

La primera implementación por fecha y las primeras migraciones de turnos se revierten. La reconstrucción introduce asignaciones y consumos, consulta de disponibilidad, actualización y cierre. Los diffs demuestran el retiro y reemplazo, pero no explican por sí solos el motivo de las reversiones.

La disponibilidad se concentra después en las asignaciones, se elimina el endpoint duplicado y el cierre actualiza turno y asignaciones en una transacción. La inicialización existente se hace repetible con `upsert` y `skipDuplicates`; aparece además una consulta explícita del estado del turno. La auditoría y los reintentos de serialización acompañan esta consolidación.

También cambia el tratamiento del stock genérico: una migración normaliza cantidades a `NULL` y otra posterior vuelve a admitir cantidades no negativas. Son decisiones sucesivas del historial, no restricciones simultáneamente vigentes. La fecha operativa adopta `America/La_Paz` y se introduce un fallback al turno abierto.

Cambios relevantes: reversiones (`34fa21d`, `90dcb4e`), asignaciones y API (`78a8062`, `b09f052`, `dc77fc9`), unificación y cierre atómico (`f937ce4`, `e17c6fe`, `5931b01`), idempotencia de inicialización y estado (`ee08900`, `f084b01`), auditoría y contratos (`f12acbe`, `df58630`), evolución de cantidades (`9104dd8`, `2c02afe`) y fecha operativa (`48bceb6`).

### 2026-09-10 a 2026-09-11 — Menús reutilizables y operación de stock por turno

Se separa la plantilla reutilizable de su ejecución en un turno. Se incorporan administración del catálogo, ajustes de stock, límite de 40 porciones, estados operativos, autorización PIN, historial y eventos para cocina y meseros. Pedidos comienza a consumir y liberar asignaciones, y publica cambios al crear, ampliar, modificar o cancelar ítems.

La consolidación permite turnos secuenciales en una fecha y cambia la identidad de las asignaciones a `(shiftId, menuItemId)`. El seed de turno abierto se adapta a esa identidad. La apertura directa y el cierre incorporan autorización sensible, y la consulta de disponibilidad usa la misma fecha operativa que la apertura.

Cambios relevantes: plantillas y CRUD (`b0c87a8`, `1f2a5cb`), ajustes y autorización (`07cb085`, `bb3a73c`, `e99e9d4`), consulta agrupada y eventos (`69d52d6`, `f664c3a`, `45e6b37`, `870bb9a`), turnos secuenciales y adaptación del seed (`0500082`, `8e1b99a`).

### 2026-09-13 a 2026-09-16 — Preservación histórica y correcciones transversales

Los seeds incorporan escenarios históricos y operativos; posteriormente se ajustan para reutilizar menús y preservar datos existentes. Las remediaciones refuerzan permisos, auditoría, tiempo operativo, idempotencia y relación entre consumos y asignaciones. La selección del turno vuelve a priorizar el abierto y las operaciones dejan de depender exclusivamente de la fecha del calendario.

La secuencia final de pedidos modifica un mismo comportamiento verificable: `f5436a3` introduce consumos persistidos y devolución a la asignación original, pero restringe la reserva de asignaciones a la categoría `DAILY_MENU`; `680138b` corrige esa restricción y devuelve prioridad a cualquier asignación activa, conservando la trazabilidad del consumo. Entre ambos, se extraen reglas compartidas de disponibilidad y se completan contratos de respuesta.

Cambios relevantes: escenarios y preservación (`06e43a5`, `aa11910`, `61c5180`, `028a4ca`), permisos y auditoría (`d3a6f1f`, `61d94e4`), fechas e índices (`e36586a`, `3a571a7`), consumos, idempotencia y categorías (`f5436a3`, `4d5e640`, `f804682`, `680138b`).

## Análisis del historial

### Indicadores observados

- Los 51 commits incluidos se distribuyen en 14 fechas UTC: 21 Feature, 25 Fix y 5 Configuration.
- El 2026-09-10 concentra 11 commits incluidos: 9 Feature, 1 Fix y 1 Configuration; como comparación, el 2026-09-04 registra 9 y el 2026-09-03 registra 6.
- Entre el 14 y el 15 de septiembre UTC se incluyen 8 Fix, seguidos de otro el día 16: afectan seed, permisos, auditoría, tiempo operativo, consumos, idempotencia y contratos.
- Hay dos reversiones explícitas de las implementaciones iniciales: `34fa21d` y `90dcb4e`.
- La selección del turno cambia de fallback al abierto (`48bceb6`) a consulta por fecha (`0500082`) y luego a prioridad al abierto mediante `OR` (`4d5e640`).
- En HEAD existen 8 handlers en `DailyMenuController`, 9 en `MenuManagementController` y 2 en el controlador histórico de menú.
- Los límites observables son stock configurado de 0 a 40, umbral `LOW_STOCK` menor que 8, consulta de los últimos 100 ajustes y hasta 2 intentos en las operaciones con reintento.

Las correcciones específicas y las pruebas asociadas sugieren consolidación funcional. No se infiere calidad, productividad ni ausencia de defectos a partir del volumen o de periodos de inactividad.

### Evidencia externa al directorio del módulo

- `prisma/migrations/`: creación de asignaciones/consumos y turnos; unificación del modelo diario; normalización y restauración del stock genérico; menús reutilizables; estados y ajustes; turnos secuenciales; alineación del índice único; protección append-only.
- `test/daily-menu-availability.e2e.ts`: cálculo de cantidades, rechazo del payload antiguo, deduplicación concurrente, auditoría bajo contención y rollback ante errores.
- `test/daily-menu-close-shift.e2e.ts`: pendientes, roles y exactamente un cierre exitoso entre dos solicitudes concurrentes.
- `test/menu-availability-migration.e2e.ts`: normalización histórica a `NULL` y rollback explícito de esa migración, sin demostrar que su restricción permanezca al final de toda la cadena.
- `test/orders-group-b-remediation.integration.ts`: reserva/liberación para categorías normales y devolución a la asignación original.
- `test/docs-json.spec.ts`: contrato OpenAPI; `prisma/seed*.ts`: preparación del catálogo y escenarios de turno.

Las pruebas se leyeron como evidencia estática; no se atribuye ningún resultado de ejecución.

### Compartidos, confianza y límites

La tabla utiliza estas marcas: **[O]** pedidos; **[K]** cocina/eventos; **[A]** autenticación/auditoría; **[T]** seeds, infraestructura, cuentas u otras áreas transversales. Indican dependencias e impactos compartidos, no módulos adicionales. La clasificación principal respeta las decisiones globales acordadas, aunque el efecto local sea secundario.

La confianza propuesta es `medium` para `bc024ca`, `34fa21d`, `90dcb4e`, `ee08900`, `df58630`, `0500082`, `06e43a5`, `61c5180`, `028a4ca`, `3a571a7` y `f804682`; es `high` para los restantes commits incluidos. Las reservas se refieren a intención principal en cambios mixtos o reversiones, no a la existencia del diff descrito. En particular, `90dcb4e` conserva Fix con confianza `medium`.

La restricción SQL revisada garantiza un turno abierto por fecha, mientras varias consultas buscan el abierto sin filtrar fecha: no se documenta una garantía de unicidad global. `BUG-TUR-005` cuestionaba el fallback entre fechas, mientras HEAD vuelve a priorizar el turno abierto; es una diferencia histórica de criterio, no un diagnóstico actual. La eliminación de migraciones de Git tampoco demuestra qué sucedió en bases previamente desplegadas.

Los puntos históricos de atención son la identidad fecha/turno, la preservación del consumo original, la equivalencia de contratos de disponibilidad y la repetibilidad de seeds y ajustes. Estas áreas cambiaron de manera recurrente según los diffs citados.

### Exclusiones locales justificadas

Se excluyen de los conteos locales los siguientes cambios revisados; una exclusión local no impide que un commit mixto pertenezca a otro módulo:

- `f08f1a9`: pruebas y documentación del ciclo de vida; `bd14333`: ampliación de pruebas unitarias; `5473f85`: pruebas del gateway, incluidas emisiones de menú y cierre.
- `e7fd477`: formato, tipado y aserciones en pruebas locales; `2b40cba`: prueba de persistencia de clave idempotente y auditoría; `d503ce7`: adaptación de mocks y llamadas al contrato con PIN.
- `1bd8cbe` y `3a082e5`: retirada y restitución de imports en una prueba local.
- `4c70d61`: sustitución local equivalente de `replace` por `replaceAll`, sin impacto funcional demostrado; su tipo global es Refactor, pero no se añade al conjunto local de 51 commits.
- `1623a88`: formato de DTO, repositorio y pruebas de daily-menu.
- `c0c47f7`, `6420dec` y `d529291`: reportes QA de menú/turnos sin implementación; `8e81aa9` y `1c92aa0`: creación y retirada de `BUG-MEN-002`, sin constituir por sí mismas cambios de permisos.

Las referencias incidentales a platos en cuentas, layouts, reportes o infraestructura no bastan para atribuir commits a daily-menu. Tampoco se incorporan merges como cambios propios del módulo.

## Commits relacionados

Fechas y hashes cortos corresponden al dataset; orden ascendente por `(timestamp, full_hash)`. Cada fila representa un commit único y describe su impacto local.

| Fecha | Commit | Tipo | Descripción |
|---|---|---|---|
| 2026-08-18 | f9a1405 | Feature | [O] La migración de agrupación de pedidos crea menu_items, precio y disponibilidad, estableciendo el catálogo persistido. |
| 2026-08-18 | 7ddd750 | Feature | [O] reserveStock/releaseStock y add_menu_item_stock incorporan cantidades opcionales y reserva/devolución transaccional. |
| 2026-08-20 | db61259 | Fix | [O] MenuController, findMenuItems y seed de 15 platos corrigen la integración con identificadores demostrativos mediante UUID y categorías persistidos. |
| 2026-08-20 | 0d670ee | Fix | [A,T] runSeed deja de sobrescribir isAvailable/availableQuantity de platos existentes, preservando su estado operativo. |
| 2026-08-20 | f9cf8fd | Fix | [O,A] MenuController incorpora RolesGuard y roles permitidos, corrigiendo el acceso operativo sin las guardas previstas. |
| 2026-08-21 | 6e389cf | Fix | [O,K] persistAndPublishAvailability persiste y emite cambios con serialización por plato, corrigiendo la propagación de disponibilidad. |
| 2026-09-02 | 0e36cf4 | Feature | initializeForDate/createForDate y tablas diarias incorporan inicialización por fecha y lectura de platos disponibles. |
| 2026-09-02 | bc024ca | Configuration | [O,T] Migraciones idempotentes preparan turnos y referencias shiftId en pedidos, cuentas y pagos. |
| 2026-09-03 | 34fa21d | Configuration | [O,T] Elimina las primeras migraciones de turnos y relaciones Prisma, retirando esa preparación de despliegue. |
| 2026-09-03 | 90dcb4e | Fix | Revierte servicio, repositorio, registro y migración del primer menú por fecha antes de su reconstrucción. |
| 2026-09-03 | 78a8062 | Feature | [O] create_daily_menu_allocations incorpora asignaciones, contadores, versiones y consumos con clave idempotente. |
| 2026-09-03 | b09f052 | Feature | GET menu-of-day/availability calcula raciones desde asignaciones abiertas y registra el módulo en la aplicación. |
| 2026-09-03 | dc77fc9 | Feature | [K] Añade actualización autenticada de disponibilidad y publicación mediante KitchenGateway. |
| 2026-09-03 | b3ca733 | Feature | [K,O] Crea shifts, POST close, comprobación de pendientes y evento menu-of-day:closed. |
| 2026-09-04 | 98b0bc4 | Feature | [O] Introduce tablas diarias y sincronización desde MenuService, conectando disponibilidad del catálogo y menú diario. |
| 2026-09-04 | ee08900 | Fix | createDailyMenu usa upsert y createMany con skipDuplicates, haciendo repetible la inicialización existente sobre platos disponibles. |
| 2026-09-04 | f937ce4 | Fix | [O] unify_daily_menu_model traslada disponibilidad a asignaciones y elimina tablas redundantes, unificando creación de turno y stock. |
| 2026-09-04 | e17c6fe | Fix | closeShift comprueba pendientes y cierra turno/asignaciones dentro de una transacción, evitando cierres parciales. |
| 2026-09-04 | 5931b01 | Fix | [O] Elimina el PATCH duplicado y utiliza updateAvailability transaccional desde la ruta histórica. |
| 2026-09-04 | f084b01 | Feature | Añade GET status y su DTO con estado y timestamps, exponiendo una nueva consulta del turno. |
| 2026-09-04 | 9104dd8 | Fix | [O] Restringe actualización a un booleano, evita emisiones sin cambio y añade serialización/reintento junto a normalización de cantidades a NULL. |
| 2026-09-04 | f12acbe | Feature | [O,A] updateAvailability bloquea el plato y registra actor y antes/después en auditLog dentro de la transacción. |
| 2026-09-04 | df58630 | Configuration | [T,O] configureOpenApi publica Swagger/JSON y esquemas del menú, incorporando integración técnica del contrato. |
| 2026-09-05 | 2c02afe | Feature | [O] Append/modificación ajustan reservas y restore_quantified_menu_stock vuelve a permitir stock genérico no negativo. |
| 2026-09-05 | a977f72 | Feature | [O] cancelOrderItem libera stock en la transacción de cancelación, incorporando devolución por anulación. |
| 2026-09-06 | 48bceb6 | Fix | getCurrentBusinessDate usa America/La_Paz y el repositorio añade fallback al turno abierto, corrigiendo consultas nocturnas. |
| 2026-09-10 | b0c87a8 | Feature | openDailyMenu y add_reusable_daily_menus separan plantilla y turno, creando asignaciones desde sus componentes. |
| 2026-09-10 | 07cb085 | Feature | [O] adjustStock, restricciones 0–40 y reservas/liberaciones de asignaciones incorporan stock operativo versionado por turno. |
| 2026-09-10 | 1f2a5cb | Feature | MenuManagementController/Repository e isActive incorporan administración, baja lógica y duplicación de menús reutilizables. |
| 2026-09-10 | bb3a73c | Feature | [A] Añade PIN, motivo, confirmaciones, idempotencia y tabla de ajustes, haciendo autorizable y consultable el cambio de stock. |
| 2026-09-10 | f664c3a | Feature | [K] Incorpora menu:opened y menu:stock_changed tras persistencia, distribuidos a cocina y meseros. |
| 2026-09-10 | 69d52d6 | Feature | getAvailability devuelve turno e ítems con nombre, categoría y estado calculado, ampliando el contrato de consulta. |
| 2026-09-10 | e99e9d4 | Feature | [A] availability/change incorpora desactivación/reactivación autorizada y registra el tipo de acción del ajuste. |
| 2026-09-10 | 45e6b37 | Feature | [O,K] publishDailyMenuStockChanges consulta asignaciones y emite cantidades/versiones después de crear pedidos. |
| 2026-09-10 | 870bb9a | Feature | [O,K] Extiende la publicación de stock a append, modificación de cantidad y cancelación de ítems. |
| 2026-09-10 | 3eb07c9 | Fix | AdjustStockDto exige cuatro dígitos mediante Matches, rechazando PINs de longitud válida pero contenido no numérico. |
| 2026-09-10 | 77f6ce5 | Configuration | [T] seed-open-shift prepara menú, turno y 15 asignaciones de 40 porciones para el entorno operativo. |
| 2026-09-11 | 0500082 | Fix | [A,T] Añade PIN a apertura directa/cierre y unicidad por turno, permitiendo turnos secuenciales sin colisión por plato/fecha. |
| 2026-09-11 | 8e1b99a | Fix | [T] El seed busca el turno abierto y usa shiftId_menuItemId, adaptándose a turnos secuenciales. |
| 2026-09-13 | 06e43a5 | Configuration | [T] seed-historical incorpora catálogo, turnos cerrados, asignaciones y consumos deterministas para escenarios históricos. |
| 2026-09-13 | aa11910 | Fix | [T] El seed histórico reutiliza cinco menús y desactiva los anteriores por fecha, corrigiendo proliferación de plantillas. |
| 2026-09-13 | 61c5180 | Fix | [T,O] Añade escenario de turno activo y ordena limpieza de consumos, ajustes y asignaciones, corrigiendo preparación/reset operativo. |
| 2026-09-14 | 028a4ca | Fix | [A,T] El seed básico conserva platos existentes mediante update vacío y endurece configuración/reset, preservando el catálogo editado. |
| 2026-09-14 | d3a6f1f | Fix | [A,O] Restringe escrituras a ADMIN, cambios a KITCHEN y evita borrar componentes con asignaciones históricas. |
| 2026-09-14 | 61d94e4 | Fix | [A,T] La migración append-only protege daily_menu_stock_adjustments y auditoría frente a UPDATE/DELETE. |
| 2026-09-14 | e36586a | Fix | [T] DailyMenuService adopta helpers compartidos de fecha y parsing operativo, eliminando cálculos divergentes. |
| 2026-09-15 | 3a571a7 | Fix | [A,T,O] Alinea índice único con Prisma, fechas del servicio histórico y seed abierto sin reinicializar contadores. |
| 2026-09-15 | f5436a3 | Fix | [O] Persiste consumos y devuelve a su asignación original; preserva stock genérico y evita buscar asignaciones con ID indefinido. |
| 2026-09-15 | 4d5e640 | Fix | [O,A,K] Opera por turno abierto, valida reuso de claves, evita eventos duplicados y hace transaccional la auditoría de catálogo/turnos. |
| 2026-09-15 | f804682 | Fix | [O,T] Extrae reglas de disponibilidad, elimina fallbacks de delegados ausentes y completa esquemas Swagger, con reorganización secundaria. |
| 2026-09-16 | 680138b | Fix | [O,K] Reserva/libera asignaciones activas para categorías normales y publica el delta al reemplazar pedidos. |
