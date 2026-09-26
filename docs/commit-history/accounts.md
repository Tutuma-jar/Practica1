# Accounts

## Vista general

| Elemento | Detalle |
|---|---|
| Módulo / Funcionalidad | Accounts |
| Total de commits | 53 |
| Features | 27 |
| Fixes | 20 |
| Refactors | 2 |
| Configuración | 4 |
| Primer cambio registrado | 2026-08-19 |
| Último cambio registrado | 2026-09-15 |

Alcance enfocado: evolución funcional de cuentas en `develop`, snapshot `516aac4bce5739619f562e7a1bd4e674edfa432f`, dentro del análisis de accounts, auth, orders, kitchen y daily-menu. El dataset contiene 337 commits alcanzables y declara historial no superficial. Este documento incluye cambios directos, persistencia e integraciones externas pertinentes y dos resoluciones propias de merge. Las fechas y el orden de evidencia corresponden al committer en UTC, ordenados por timestamp y hash completo.

Se excluyen del conteo local los cambios exclusivamente documentales, pruebas sin cambio funcional y ajustes de formato o fixtures pertenecientes a otras funcionalidades. No se ejecutaron pruebas ni código del proyecto para esta revisión. Los conteos describen cambios históricos, no resultados de validación en ejecución.

## Estructura

```text
Accounts
├── Features
│   ├── Consumo por mesa o grupo y snapshots de líneas
│   ├── Revisión consolidada, separada y de pedidos TAKEOUT
│   ├── Pagos CASH/QR, pagos parciales y cierre acumulado
│   ├── Divisiones y balances por comensal
│   └── Descuentos, reapertura y sesiones de servicio
├── Fixes
│   ├── Coherencia entre cuentas, órdenes y liberación de mesas
│   ├── Autorización de operaciones sensibles
│   ├── Idempotencia y conservación de pagos y descuentos
│   └── Consultas por fecha operativa y contratos TAKEOUT
├── Refactors
│   ├── Orden explícito de bloqueos
│   └── Separación de validaciones y errores de descuentos
└── Configuration
    ├── Integración directa con turnos, posteriormente retirada
    └── Resoluciones propias de integración de descuentos y reapertura
```

## Descripción

Accounts gestiona el consumo facturable, su revisión y el cobro de cuentas individuales, consolidadas y TAKEOUT. `AccountLine` conserva nombres, cantidades, precios e importes; `AccountOrder` vincula las comandas con su cuenta. Los importes se calculan con `Prisma.Decimal` y se exponen como cadenas con dos decimales.

La API permite consultar cuentas abiertas y cerradas, recuperar el detalle persistido, anticipar qué comandas son elegibles para revisión y registrar o consultar pagos. La revisión admite selección de comandas y modos `CONSOLIDATED` o `SEPARATE`. Para mesas y grupos, la elegibilidad exige ítems facturables entregados. Las cuentas TAKEOUT se vinculan al pedido sin mesa ni sesión de servicio; solicitar su cuenta no cambia el estado operativo del pedido.

Los pagos generales y por comensal admiten CASH y QR. Su registro requiere `x-request-id`; los repositorios cotejan el contenido de un reintento antes de reutilizar un pago. Las divisiones asignan líneas a comensales, calculan balances y protegen las asignaciones que ya tienen pagos. El reparto considera el total neto de la cuenta y ajusta el remanente del redondeo en la última asignación.

El cierre requiere que pagos activos persistidos más pagos nuevos cubran exactamente el total. Comprueba que las líneas estén `DELIVERED` o `CANCELLED`, conserva `firstClosedAt` y cierra los splits abiertos. Cuando existe una sesión identificada sin consumo activo restante, termina la sesión y pasa sus mesas a `PENDING_RELEASE`. La liberación manual pertenece a la operación de mesas. `ServiceSession.operationalAccountId` distingue el consumo que continúa abierto de la cuenta enviada a revisión.

Los descuentos requieren motivo y autorización mediante `ManagerPinAuthorizationService`, con PIN de administrador o supervisor y contexto de terminal. Registran ajuste, actores, versión e identificador de solicitud. La reapertura vigente requiere rol `ADMIN` o `CASHIER` y permiso `ACCOUNT_REOPEN`; recibe un motivo, conserva los pagos y devuelve la cuenta a `REVIEW_REQUESTED`. En este snapshot no solicita un PIN adicional ni consulta la delegación de caja, aunque ambas condiciones existieron históricamente.

`AccountsModule` conecta Prisma, Auth, Kitchen, Audit y Settings. Sus dos controladores y dos servicios separan cuentas de divisiones. Los eventos de cuentas, mesas y splits se publican mediante `KitchenGateway` después de persistir; los fallos de emisión se registran sin sustituir las garantías de las transacciones. La extracción final de `domain/account-discount.ts` concentra las reglas de descuentos. El modelo actual no contiene los vínculos directos `Account.shiftId` y `Payment.shiftId` del ensayo de integración de turnos retirado.

## Evolución del módulo

### 2026-08-19–2026-08-21 — Del consumo calculado al cierre persistente

El módulo comenzó calculando consumo por mesa con los precios guardados en los ítems de las órdenes. Cinco commits del 19 de agosto construyeron progresivamente snapshots, revisión con bloqueo de órdenes, pagos auditados y listado para caja. La persistencia incorporó transacciones serializables, recuperación ante escrituras concurrentes y enlaces explícitos entre cuentas y comandas.

Cambios relevantes:

- `7e5b523` y `e67ca87` introducen cálculo y persistencia de líneas; las migraciones crean `accounts` y `account_lines`.
- `97ce5d2` añade `request-review`, bloquea la mesa y marca las órdenes como `ACCOUNT_REQUESTED`; orders incorpora el rechazo de cambios mientras la cuenta está en revisión.
- `8711bae` persiste pagos, cierra órdenes y escribe auditoría en la misma transacción. `f744732` completa la consulta de cuentas abiertas.
- `ec5da6b` corrige la integración de caja mediante el detalle persistido por UUID. `ec144d6` corrige la selección del schema en `PrismaService` y añade cobertura E2E del ciclo; no es un cambio exclusivamente de pruebas.
- `f46e02d` publica solicitudes y cierres a terminales de caja y meseros, incorporando la sala de caja al gateway compartido.

### 2026-08-27–2026-08-29 — Cierre financiero, estado de mesa y cuentas grupales

El cierre dejó de equivaler a liberación inmediata. Las mesas pasan a `PENDING_RELEASE`, con auditoría y eventos operacionales; el cambio posterior exige que la mesa esté ocupada antes de efectuar esa transición. Sobre esta base se añadieron cuentas consolidadas y continuidad del vínculo durante traslados de grupos.

Cambios relevantes:

- `049b082` separa cierre financiero y liberación manual. `cab4dc3`, pese a su prefijo de pruebas, endurece la transición y corrige ocupación y backfill de mesas en otras capas.
- `1f21809` publica `table:updated` con información operacional y versión derivada de `updatedAt`.
- `1ec1285` añade `tableGroupId`, consumo consolidado, revisión de grupos y reparto en el cierre. Su integración impide modificar grupos con cuentas asociadas.
- `794171c` actualiza la mesa ancla de la cuenta durante el traslado transaccional del grupo. Más adelante, `5e6e491` y `3b47891` permiten disolver grupos con cuentas cerradas y dejan de mostrarlas como cuentas activas del grupo.

### 2026-09-02–2026-09-03 — Integración directa de turnos retirada

`bc024ca` añade migraciones, índices y relaciones de turno en cuentas y pagos. `34fa21d` retira esa integración junto con el modelo de turno de esa propuesta. Ambos se clasifican globalmente como Configuration: se cuenta la incorporación y su retirada, sin presentar esas relaciones como capacidad vigente ni atribuir una causa de reversión no demostrada por los diffs.

### 2026-09-04–2026-09-06 — Operaciones sensibles y resoluciones de integración

La persistencia de ajustes y delegaciones permitió introducir reapertura controlada y descuentos. La ampliación convivió con nuevas operaciones de edición y cancelación de pedidos, que respetan el bloqueo de cuentas en revisión o cerradas. Después se corrigieron problemas concretos de integración, autorización y creación de líneas consolidadas.

Cambios relevantes:

- `20ea8ba` crea ajustes de cuenta, delegaciones y registros de operaciones sensibles. `1a3a5a3` implementa reapertura con permiso, delegación/PIN y auditoría.
- `2c02afe` y `a977f72` extienden la protección de cuentas congeladas a edición y cancelación de ítems desde orders.
- `fb25164`, aunque titulado como pruebas de integración, implementa descuentos completos: endpoint, persistencia, autorización, idempotencia y eventos. Se cuenta como Feature.
- El merge `fd86afe` combina descuentos y reapertura con una resolución propia incompleta: pierde el registro HTTP de reapertura, omite dependencias del constructor y errores del repositorio y duplica un import del servicio. Se cuenta solo esa composición técnica como Configuration, con confianza media; no vuelve a contabilizar las capacidades de sus ramas. `0c8cc1c` repara parte de esa integración.
- `4c70d61` explicita comparadores del orden de bloqueos y `e7fd477` separa validación, resolución del autorizador y traducción de errores de descuentos.
- `07e65e9` permite supervisores en reapertura. El merge `12918e3` produce otra resolución propia del controlador: conserva el cuerpo de descuento con metadatos de reapertura y sin registrar la ruta de reapertura. Se cuenta como Configuration de confianza media. `477ef1b` corrige los metadatos y restablece rutas separadas.
- `b778e43` elimina la autorización alternativa cuando falta el servicio sensible, anula pagos al reabrir y exige ítems READY/DELIVERED al cerrar. `8be6aa2` añade búsqueda de cuentas cerradas; `7c59818` distingue los datos de creación y actualización anidada para cuentas consolidadas.

Las dos resoluciones propias están documentadas en `analysis.merge_reviews`. Los merges que adoptan sus árboles no se cuentan otra vez en este documento.

### 2026-09-09–2026-09-10 — Divisiones, pagos parciales y sesiones de servicio

La división por consumo se desarrolló como una capacidad compuesta: esquema, repositorio, reglas de negocio, API y eventos. En paralelo se añadieron pagos parciales generales y cierre acumulado. El modelo de sesión introdujo después una cuenta operativa compartida por varias comandas.

Cambios relevantes:

- `40cca37` crea splits, asignaciones y enlaces de pagos fuera de la carpeta del módulo, en Prisma. `bade082` añade persistencia y balances; `d12643d` exige cuenta en revisión, asignación completa sin duplicados y auditoría.
- `023c8c8` expone consultas, asignaciones y pagos por comensal. `904e2d1` publica `split:created`, `split:updated` y `split:closed` mediante KitchenGateway.
- `37160d6` valida pagos parciales; `00b9820` expone registro y consulta con saldo. `eb2960b` permite cerrar sumando pagos persistidos no anulados y pagos nuevos, incluido `payments: []` cuando el saldo ya está cubierto.
- `af0bedc` vincula cuentas con sesiones, órdenes y mesas. `b9074a7` crea o reutiliza la cuenta operativa al incorporar nuevas comandas de una sesión.

### 2026-09-12–2026-09-15 — Facturación parcial y endurecimiento financiero

La separación entre cuenta en revisión y cuenta operativa permitió cobrar comandas seleccionadas manteniendo otras abiertas. Los ajustes posteriores atendieron convivencia de cuentas, selección de grupos, pagos concurrentes, cierre de sesiones, conservación del historial y compatibilidad TAKEOUT.

Cambios relevantes:

- `2037a1b` introduce opciones de revisión, selección de comandas, facturación separada y `operationalAccountId`. También cambia la condición de cierre a DELIVERED/CANCELLED. Se clasifica como Feature por las nuevas capacidades observables.
- `b6940a9` limita la unicidad a cuentas OPEN, añade `requestId` de pagos, revalida balances bajo bloqueo, prorratea el total neto y valida selecciones contra el grupo completo.
- `61c5180` corrige continuidad de sesiones y completa consultas de caja. `d3a6f1f` vuelve a ajustar roles y delegación. `61d94e4` protege ajustes financieros con triggers append-only; `e36586a` adopta la fecha operativa para consultas de cerradas.
- `b5caea1` introduce cuentas TAKEOUT sin mesa. `3a571a7` unifica la autorización de descuentos mediante el servicio central y corrige su integración con datos TAKEOUT.
- `f5436a3` conserva pagos al reabrir y vuelve a REVIEW_REQUESTED, preserva el primer cierre, comprueba consumo restante de sesión y cierra splits con la cuenta. También exige identificador explícito de pago, coteja payloads y protege asignaciones pagadas.
- `4d5e640` exige un único objetivo de revisión, hace idempotente la creación TAKEOUT sin congelar la orden, preserva descuentos al reconstruir snapshots y corrige rangos de fecha. La reapertura pasa a depender del actor autorizado, sin PIN adicional ni consulta de delegación.
- `f804682` extrae el dominio de descuentos sin cambiar sus reglas locales. Su tipo global es Fix por las correcciones transversales del mismo commit; su efecto específico en accounts es reorganización y pruebas de dominio.

## Análisis del historial

### Implementación compuesta y ajustes verificables

El historial muestra ampliaciones funcionales seguidas de cambios específicos sobre sus contratos e integraciones. Esto permite hablar de ajustes del flujo incorporado, pero no demostrar ausencia de fallos por volumen de commits ni por periodos sin actividad.

Indicadores observados:

- Cinco commits funcionales del 19 de agosto construyen el flujo inicial: `7e5b523`, `e67ca87`, `97ce5d2`, `8711bae` y `f744732`.
- Ocho commits entre el 9 y el 10 de septiembre UTC forman divisiones y pagos parciales: `40cca37`, `bade082`, `d12643d`, `023c8c8`, `904e2d1`, `37160d6`, `00b9820` y `eb2960b`. Son etapas de capacidades relacionadas, no ocho funcionalidades independientes.
- Dos merges incluidos aportan resoluciones técnicas propias: `fd86afe` y `12918e3`. Sus efectos locales se distinguen de los commits que introducen descuentos, reapertura o autorización de supervisores.
- La autorización de reapertura cambia explícitamente en `1a3a5a3`, `07e65e9`, `61c5180`, `d3a6f1f` y `4d5e640`.
- El tratamiento de pagos al reabrir pasa de conservación inicial a anulación en `b778e43` y a conservación en `f5436a3`. Este último cambio no restaura aisladamente el comportamiento original: el cierre acumulado de `eb2960b` ya considera pagos existentes.
- La validación de cierre pasa por READY/DELIVERED en `b778e43` y DELIVERED/CANCELLED en `2037a1b`; el repositorio del snapshot conserva la segunda condición.
- La idempotencia de pagos se desarrolla en dos pasos comprobables: incorporación de `requestId` en `b6940a9` y obligatoriedad del header con comparación de payload en `f5436a3`. `4d5e640` refuerza el cotejo de descuentos y evita repetir eventos de descuentos o altas TAKEOUT reutilizadas.

### Reversiones, alcance local y límites de verificación

La retirada de vínculos con turnos en `34fa21d` sí cambia el modelo histórico de accounts. En cambio, las secuencias `1bd8cbe → 3a082e5 → 028a4ca` y `f042dea → d431971 → 651467f` afectan, dentro de accounts, fixtures y ajustes de pruebas. No se cuentan aquí como retirada y recuperación del ciclo financiero. Sus efectos productivos en otros módulos corresponden a sus documentos respectivos.

La documentación de ACC-011 se incorpora en `8e81aa9` y se actualiza en `1c92aa0` a verificación parcial con re-test bloqueado. Esos commits documentales no incrementan el total funcional. El código de `f5436a3` y el snapshot muestran cierre de splits al cerrar la cuenta; no demuestran cierre automático simplemente por registrar el último pago ni una verificación E2E exitosa. La evidencia documental final tampoco permite afirmar que el ciclo completo quedó validado.

Se excluyen además las pruebas puras de `bcdd91d`, `3cb263e` y `5473f85`, la documentación de `714c0c1`, `c0c47f7`, `6420dec` y `d529291`, y los efectos locales de formato o fixtures de commits transversales. `bd14333` también ajusta exclusiones Sonar: no se presenta como prueba pura ni como mejora funcional de accounts. El porcentaje de cobertura citado por mensajes históricos no se toma como medición de esta revisión.

Posibles puntos de atención históricos:

- Coherencia entre cuenta, comandas vinculadas, sesión operativa y liberación de mesa, modificada de nuevo al incorporar cobro parcial.
- Contratos de autorización de reapertura y descuentos, revisados en varias etapas y afectados por resoluciones de integración.
- Compatibilidad entre pagos generales, pagos por comensal, descuentos y reintentos con el mismo identificador.
- Diferencia entre cierre de cuenta y cierre de división, y entre las expectativas documentales anteriores y el comportamiento del snapshot.

Los commits compartidos mantienen un único tipo global. Por ello, la extracción local de reglas en `f804682` aparece como Fix y las migraciones de turnos como Configuration. Los totales de accounts no deben sumarse sin deduplicación a los de orders, auth, kitchen o daily-menu.

## Commits relacionados

| Fecha | Commit | Tipo | Descripción |
|---|---|---|---|
| 2026-08-19 | 7e5b523 | Feature | Incorpora cálculo de consumo por mesa con precios históricos. |
| 2026-08-19 | e67ca87 | Feature | Persiste cuentas y snapshots de líneas de consumo. |
| 2026-08-19 | 97ce5d2 | Feature | Solicita revisión y congela las órdenes asociadas. |
| 2026-08-19 | 8711bae | Feature | Añade pagos CASH/QR y cierre transaccional auditado. |
| 2026-08-19 | f744732 | Feature | Lista cuentas abiertas para caja. |
| 2026-08-20 | ec5da6b | Fix | Corrige la consulta del detalle persistido para el cobro. |
| 2026-08-21 | ec144d6 | Fix | Corrige el schema de conexión y verifica el ciclo completo de cuentas. |
| 2026-08-21 | f46e02d | Fix | Sincroniza solicitudes y cierres con caja y meseros. |
| 2026-08-27 | 049b082 | Feature | Separa el cierre financiero de la liberación manual de mesa. |
| 2026-08-27 | cab4dc3 | Fix | Endurece la transición de mesas al cerrar cuentas. |
| 2026-08-28 | 1f21809 | Feature | Publica el contrato operacional versionado de mesas tras el cierre. |
| 2026-08-29 | 1ec1285 | Feature | Incorpora cuentas consolidadas para grupos de mesas. |
| 2026-08-29 | 794171c | Feature | Mantiene la mesa ancla de la cuenta al trasladar un grupo. |
| 2026-09-02 | bc024ca | Configuration | Introduce vínculos de cuentas y pagos con turnos, posteriormente retirados. |
| 2026-09-03 | 34fa21d | Configuration | Retira la integración directa de cuentas y pagos con turnos. |
| 2026-09-04 | 20ea8ba | Feature | Añade persistencia de ajustes y autorización de reaperturas. |
| 2026-09-04 | 1a3a5a3 | Feature | Implementa reapertura controlada y auditada de cuentas. |
| 2026-09-05 | 2c02afe | Feature | Extiende el bloqueo financiero a nuevas operaciones de edición de pedidos. |
| 2026-09-05 | a977f72 | Feature | Protege cuentas en revisión o cerradas frente a cancelaciones de ítems. |
| 2026-09-05 | fb25164 | Feature | Añade descuentos autorizados, auditados e idempotentes. |
| 2026-09-05 | fd86afe | Configuration | Combina descuentos y reapertura con pérdidas de ruta, dependencias y errores en la resolución. |
| 2026-09-05 | 0c8cc1c | Fix | Repara integración de reapertura y descuentos después de cambios concurrentes. |
| 2026-09-05 | 4c70d61 | Refactor | Explicita el orden de bloqueos de cuentas, órdenes y mesas. |
| 2026-09-05 | e7fd477 | Refactor | Descompone la lógica de descuentos y sus errores. |
| 2026-09-05 | 07e65e9 | Fix | Habilita la reapertura para supervisores en el contrato de ese momento. |
| 2026-09-05 | 12918e3 | Configuration | Mezcla metadatos de reapertura con descuento y omite la ruta de reapertura en la resolución. |
| 2026-09-05 | 477ef1b | Fix | Restablece la ruta HTTP de reapertura. |
| 2026-09-06 | b778e43 | Fix | Endurece autorización, estados de ítems y tratamiento de pagos al reabrir. |
| 2026-09-06 | 8be6aa2 | Feature | Lista cuentas cerradas para seleccionar reaperturas. |
| 2026-09-06 | 7c59818 | Fix | Corrige la creación de cuentas consolidadas en revisión. |
| 2026-09-06 | 5e6e491 | Fix | Permite disolver grupos después de cerrar sus cuentas. |
| 2026-09-06 | 3b47891 | Fix | Retira cuentas cerradas del estado activo del grupo. |
| 2026-09-09 | 40cca37 | Feature | Crea el modelo persistente de divisiones por comensal. |
| 2026-09-09 | bade082 | Feature | Implementa persistencia y balances de divisiones. |
| 2026-09-09 | d12643d | Feature | Añade reglas y auditoría de divisiones por consumo. |
| 2026-09-09 | 023c8c8 | Feature | Expone la API de divisiones, balances y pagos individuales. |
| 2026-09-09 | 904e2d1 | Feature | Sincroniza divisiones y pagos mediante eventos. |
| 2026-09-09 | 37160d6 | Feature | Incorpora validación de pagos parciales de cuenta. |
| 2026-09-09 | 00b9820 | Feature | Expone registro y consulta de pagos parciales. |
| 2026-09-10 | eb2960b | Feature | Permite cierre acumulado con pagos registrados previamente. |
| 2026-09-10 | af0bedc | Feature | Vincula cuentas con sesiones de servicio y layouts. |
| 2026-09-10 | b9074a7 | Feature | Reutiliza una cuenta operativa para múltiples comandas de sesión. |
| 2026-09-12 | 2037a1b | Feature | Añade facturación parcial o separada manteniendo continuidad de sesión. |
| 2026-09-12 | b6940a9 | Fix | Corrige convivencia de cuentas, selección grupal e idempotencia de pagos. |
| 2026-09-13 | 61c5180 | Fix | Corrige continuidad del ciclo y completa consultas de caja. |
| 2026-09-14 | d3a6f1f | Fix | Reajusta roles y delegación de operaciones sensibles. |
| 2026-09-14 | 61d94e4 | Fix | Protege el historial de ajustes financieros contra modificaciones. |
| 2026-09-14 | e36586a | Fix | Alinea las consultas de cuentas cerradas con la fecha operativa. |
| 2026-09-14 | b5caea1 | Feature | Introduce cuentas y cobro de pedidos TAKEOUT sin mesa. |
| 2026-09-15 | 3a571a7 | Fix | Unifica autorización de descuentos y corrige integración TAKEOUT. |
| 2026-09-15 | f5436a3 | Fix | Endurece reapertura, cierre de sesión, splits e idempotencia financiera. |
| 2026-09-15 | 4d5e640 | Fix | Alinea contratos finales de revisión, descuentos, TAKEOUT y reapertura. |
| 2026-09-15 | f804682 | Fix | Extrae las reglas de descuentos a un dominio reutilizable y probado. |
