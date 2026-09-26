# Orders

## Vista general

| Elemento | Detalle |
|---|---|
| Módulo / Funcionalidad | Orders: pedidos, mesas, grupos y traslados |
| Total de commits | 79 |
| Features | 36 |
| Fixes | 38 |
| Refactors | 3 |
| Configuración | 2 |
| Primer cambio registrado | 2026-08-18 |
| Último cambio registrado | 2026-09-16 |

Alcance enfocado sobre `develop`, snapshot `516aac4bce5739619f562e7a1bd4e674edfa432f`, y el dataset `docs/commit-history/.analysis/history-data.json` de 337 commits alcanzables. Se incluyen 78 commits no merge y una resolución propia de merge; las fechas corresponden al committer en UTC. El historial consultado no es shallow y no se aplicó una ventana temporal ni un filtro first-parent. Los layouts se consideran únicamente como dependencia de mesas, grupos y sesiones, no como funcionalidad independiente.

La revisión contrasta diffs con código del snapshot, migraciones y pruebas externas a la carpeta del módulo. No se ejecutó el proyecto ni sus pruebas. El estado local observado contenía `docs/commit-history/` sin seguimiento; esos archivos no se atribuyen al snapshot. Los totales son commits únicos de esta tabla, no cantidades de funcionalidades ni resultados de pruebas.

## Estructura

```text
Orders
├── Comandas
│   ├── Mesa y para llevar
│   ├── Tiempos, categorías y precios persistidos
│   ├── Consulta, reemplazo, agregado y modificación
│   └── Cancelación, permisos y auditoría
├── Integración operativa
│   ├── Disponibilidad, reserva y devolución de stock
│   ├── Despacho a cocina y notificaciones
│   └── Eventos de pedidos, mesas y sesiones
├── Mesas
│   ├── Ocupación, cierre y liberación manual
│   ├── Comensales
│   └── Administración del pool
├── Grupos
│   ├── Membresía e historial
│   ├── Conectividad y límites
│   └── Consulta y disolución
└── Traslados y sesiones
    ├── Traslado individual y grupal
    ├── Bloqueos, reintentos y trazabilidad
    └── Continuidad de sesión y cuenta operacional
```

## Descripción

Orders implementa el ciclo operativo de comandas y mesas mediante cuatro controladores: pedidos, menú, mesas y grupos. `src/modules/orders/routes/orders-routes.module.ts` integra Prisma, autenticación, cocina y menú diario. Los servicios coordinan validaciones y eventos; los repositorios concentran persistencia, bloqueos y auditoría.

Los pedidos pueden ser de mesa o para llevar y contener cursos e ítems. La API permite crear, consultar por ID, reemplazar cursos, agregar o modificar ítems, cancelar y enviar a cocina. Los precios provienen del servidor y el detalle utiliza valores persistidos. La edición depende del estado del pedido, sus ítems y la cuenta vinculada. La cancelación dedicada requiere `ORDER_CANCEL` y exige razón y autorización sensible para ítems preparados. No existe un listado general `GET /orders` en el controlador del snapshot.

La reserva utiliza una asignación activa cuando existe, también para platos de categorías regulares; un plato `DAILY_MENU` sin asignación se rechaza. Los consumos persistidos identifican el origen de las devoluciones. El despacho repetido puede devolver el ticket existente sin duplicar el evento, y la cancelación reevalúa la notificación del curso. La emisión de varios eventos es de mejor esfuerzo después de persistir la operación.

Las mesas exponen estado operativo y derivado, comensales y referencias de pedido/grupo. El cierre de cuenta y la liberación manual son operaciones separadas; cancelar el último ítem no libera automáticamente la mesa en el snapshot. El pool permite creación, edición y activación/desactivación con restricciones de turno y relaciones activas; la creación fija capacidad cuatro, mientras otras operaciones utilizan autorización gerencial.

Los grupos mantienen membresías históricas y validan conectividad sobre el layout asociado. La creación y adición de miembros admiten grupos de dos a cuatro mesas. Las sesiones vinculan pedidos y cuenta operacional para mantener continuidad de atención. Los traslados actualizan pedidos, mesas y membresías de sesión con validaciones transaccionales; los límites concretos de los distintos contratos se distinguen en el análisis.

## Evolución del módulo

### 2026-08-18–2026-08-21 — Comandas e integración operativa inicial

El modelo inicial establece pedidos de mesa y para llevar, cursos ordenados e ítems con precio persistido. La API incorpora validación previa y reserva transaccional de existencias. La integración con cocina añade tickets, tiempos operativos y restricciones de edición una vez iniciada la preparación; la revisión y el cierre de cuenta coordinan el bloqueo y finalización de pedidos (`f9a1405`, `07a1a34`, `7ddd750`, `d8ca186`, `97ce5d2`, `8711bae`).

El catálogo con UUID reales y la lectura por ID completan la integración de las terminales. El detalle conserva precios anteriores al modificar platos existentes; las categorías se contrastan con el tiempo solicitado. Autenticación y eventos complementan el circuito operativo (`db61259`, `f9cf8fd`, `cd662cb`, `6e389cf`, `41b3d7a`).

La revisión guardada de `9e7ec66ad0a91a96bb2afc61b99a24d5e0e18fdc` identifica una resolución propia en `orders-routes.module.ts`: al combinar menú y mesas se conserva el registro del menú, pero se pierde el registro del controlador y proveedor de mesas. Se cuenta exclusivamente esa composición técnica como Configuration, con confianza media. La API de mesas y el catálogo pertenecen a commits anteriores; `774c43e` restituye después el registro. No se contabilizan nuevamente las capacidades integradas por el merge.

### 2026-08-27–2026-08-29 — Ciclo de mesas, grupos y traslados

El estado de mesa pasa a persistirse y el cobro deja la mesa pendiente de liberación, con una operación manual auditada para completar el ciclo. El bloqueo de nuevas comandas y la ocupación transaccional cierran la integración entre pedidos y mesas (`2cc3523`, `049b082`, `cf1fad8`, `5a11523`, `cab4dc3`). El último de estos commits contiene producción y backfill SQL pese a su prefijo `test`. Los permisos de liberación cambian durante esta etapa y el contrato posterior la reserva al mesero (`ae858af`, `1f21809`).

El traslado individual incorpora validación de origen/destino, bloqueos ordenados, auditoría, reintentos y eventos de ambas mesas. Los grupos añaden membresías históricas, cuentas consolidadas, disolución y traslado completo con registro de movimientos (`dfacff8`, `92bcf56`, `195cf76`, `1ec1285`, `0b9db00`, `794171c`). La posterior sustitución de mapeos `any` por tipos Prisma reorganiza la implementación sin añadir una capacidad operativa (`6adcb38`).

### 2026-09-04–2026-09-06 — Disponibilidad y mutaciones auditadas

La disponibilidad se integra con menú diario y después se concentra en su repositorio, evitando dos caminos de actualización. El contrato booleano y la atribución del actor completan esa transición; OpenAPI publica el contrato técnico de pedidos y menú (`98b0bc4`, `f937ce4`, `5931b01`, `9104dd8`, `f12acbe`, `df58630`).

Las mutaciones incrementales permiten agregar y modificar ítems, ajustar stock y registrar auditoría. La cancelación dedicada incorpora permisos, autorización de preparados y eventos de cocina (`2c02afe`, `a977f72`). Las extracciones posteriores separan autorización y traducción de errores (`e7fd477`).

La separación de grupos se ajusta en tres puntos distintos: admisión de cuentas cerradas, exclusión de esas cuentas del estado activo y salida de miembros en el trigger SQL (`5e6e491`, `3b47891`, `7a02a23`). En paralelo, `b778e43` incorpora liberación automática al cancelar todos los ítems; esa política será retirada en la remediación de septiembre.

### 2026-09-09–2026-09-13 — Stock por turno, sesiones y continuidad de atención

Se añaden comensales y se conecta la reserva con asignaciones de stock por turno, publicando cambios posteriores a ventas, modificaciones y cancelaciones (`cf6db70`, `07cb085`, `45e6b37`, `870bb9a`). Los eventos del pool reciben ajustes sucesivos de tipo y payload, con recuperación de un tratamiento diferenciado para creación/baja y actualización (`0500082`, `181ca57`, `8e1b99a`).

La agrupación evoluciona desde posiciones consecutivas hacia conectividad del layout y luego adyacencia calculada desde posiciones visibles. La migración del trigger acompaña esa transición y una corrección posterior restituye la excepción de salida de miembros (`52faa41`, `e36be14`, `aa11910`). Estos cambios se documentan por su impacto sobre grupos, sin desarrollar la administración independiente de layouts.

Las sesiones introducen continuidad entre pedidos y cuentas. `2037a1b` se clasifica como Feature por la nueva facturación parcial y cuenta operacional: el pedido nuevo se vincula a esta última y puede continuar la atención de la sesión. Los ajustes vecinos evitan repetir la transición de ocupación y permiten reemplazar sesiones asociadas a cuentas finalizadas (`af0bedc`, `b9074a7`, `2037a1b`, `5ef3661`, `61c5180`). El pool adopta numeración administrada, creación con capacidad cuatro y restricciones de baja (`8edb36e`, `b6940a9`).

### 2026-09-14–2026-09-16 — Remediación de contratos e integridad transaccional

Se especifica el error de layout no disponible, se ajustan permisos y se unifica la fecha operacional usada para stock. Los contratos de espacios y estados ingleses atraviesan introducción, reversión y reposición (`5f98165`, `d3a6f1f`, `e36586a`, `f042dea`, `d431971`, `651467f`). La reversión es un commit no merge con efecto propio; su clasificación principal Fix tiene confianza media y no implica atribuirle la creación de esos contratos.

La remediación posterior preserva IDs al reemplazar ítems, vincula consumos con asignaciones, revalida la cancelación bajo bloqueo y mueve las membresías de sesión en traslados. También retira la liberación automática al cancelar el último ítem y reevalúa las notificaciones de cocina (`f5436a3`). El despacho se vuelve idempotente y la asignación de reserva se selecciona por turno abierto (`4d5e640`).

El cierre de esta etapa limita los grupos a cuatro mesas, migra espacios históricos de grupos y completa contratos OpenAPI. Finalmente, reserva y devolución usan asignaciones activas también para categorías regulares y el reemplazo de cursos publica diferencias de stock (`80d325f`, `f804682`, `680138b`). Esto muestra estabilización de flujos concretos, no una garantía de ausencia de problemas en ejecución.

## Análisis del historial

### Indicadores observados

- La tabla contiene **79 commits únicos**: **36 Feature, 38 Fix, 3 Refactor y 2 Configuration**; incluye **78 no merges y un merge con resolución propia**.
- Hay **18 días activos UTC**, entre el **18 de agosto y el 16 de septiembre de 2026**.
- El **18 de agosto** y el **10 de septiembre** registran **8 commits cada uno**, máximos diarios del conjunto; juntos suman **16/79 (20,3 %)**. Como comparación, el 27 y el 29 de agosto registran siete cada uno.
- Del **14 al 16 de septiembre** se concentran **12 commits**, todos Fix: **12/79 (15,2 %)**. Sus diffs afectan contratos, stock, cancelación, sesiones y traslados.
- El **6 de septiembre** reúne **tres correcciones de disolución/estado de grupo**, distribuidas entre validación de cuentas, consulta de estado y trigger SQL.
- La secuencia **introducción–reversión–reposición** de contratos de espacios comprende **tres commits**: `f042dea`, `d431971` y `651467f`.
- `test/orders-group-b-remediation.integration.ts` declara **ocho casos** y `test/orders-append.e2e.ts` **uno**. Se leyeron sus escenarios de stock, conservación de identidad, cancelación, cuenta bloqueada y traslado de sesión; no se ejecutaron ni se infiere cobertura porcentual.

### Dependencias y cambios compartidos

Los commits no se asignan únicamente por carpeta. Ocho incluidos no modifican `src/modules/orders/`: `f9a1405`, `2822a6f`, `8711bae`, `f46e02d`, `2cc3523`, `049b082`, `7a02a23` y `aa11910`; aportan modelos, migraciones o integración directa de pedidos y mesas.

La integración con **cuentas** comprende bloqueo/cierre, cuenta consolidada, facturación parcial y continuidad de sesión; con **cocina**, despacho, tiempos y eventos; con **menú**, asignaciones, consumos y disponibilidad; con **autenticación/auditoría**, permisos y autorización sensible. Los commits transversales de remediación conservan un único tipo principal global aunque tengan efectos locales distintos. La unión global debe deduplicarlos, no sumar los totales de los documentos.

Las clasificaciones principales de `92bcf56`, `4c70d61`, `d431971` y `9e7ec66` tienen confianza media por mezcla de efectos o naturaleza de integración/reversión; el impacto local descrito procede de evidencia concreta. En particular, `9e7ec66` se incorpora según `analysis.merge_reviews` y se limita a la pérdida de registro de mesas, sin contar otra vez catálogo, API ni seed.

### Límites de interpretación y posibles puntos de atención

El historial muestra revisiones recurrentes de autorización, stock, estado de mesa y continuidad de sesión. Conviene describir por separado sus contratos y capas, evitando equiparar una intención histórica con una capacidad irrestricta del snapshot:

- **Multiorden:** `b9074a7` introduce continuidad por sesión, mientras la migración inicial conserva el índice parcial `orders_one_open_order_per_table` para `OPEN`; no se encontró su retirada en las migraciones consultadas. La descripción no presupone pedidos abiertos simultáneos ilimitados.
- **Tamaño de grupo y traslado:** creación/adición valida de dos a cuatro mesas, pero `TransferOrderRequestDto.toTableIds` mantiene máximo tres. Son límites estáticos distintos, no un resultado de prueba de ejecución.
- **Cantidad cero:** el DTO de modificación admite cero y el repositorio contempla cancelación por ese valor, mientras la migración inicial exige cantidad positiva. La revisión no comprueba el estado de una base desplegada.
- **Retiro y disolución:** `rejectIfAccountExists()` considera cuentas históricas al modificar membresías; la disolución completa filtra cuentas no cerradas. La prosa distingue ambas operaciones.
- **Documentación histórica:** reportes QA y READMEs describen ramas o estados anteriores; no prueban por sí solos defectos actuales, causas ni resultados de este HEAD.

### Exclusiones justificadas

De los candidatos que tocan la carpeta de Orders se excluyen ocho del conteo local; los cambios productivos ajenos pueden pertenecer a otros módulos:

- `c1b25308a739fbb44bbc9102809a8bc9ee334a07`: prueba contractual de detalle multitiempo, sin cambio productivo.
- `8f5415893a02399b42ab383a0180078febab07ad`: elimina un `as any` de una prueba local; producción/tooling cambia fuera de Orders.
- `5473f851fd897320098ddba4f177fa555963ee75`: ampliación de pruebas unitarias, sin implementación local nueva.
- `3eb07c9322b020cffe060d9c03216d701bc9dc6e`: adaptación del fixture de catálogo con `isActive` en Orders.
- `1623a88d66fe1ff9ef026e990db3e1b680321ed7`: formato del repositorio de grupos; el mapping de layout y orden del reset operativo se mantienen fuera del comportamiento runtime aquí contado.
- `1bd8cbe5bbf50dad6fb6d01ad4be49ce9e94af5d`: comentario ESLint de una prueba y verificaciones generales.
- `3a082e5ea9a47a0c4c6c9e0ee87fae034a8e34ba`: reversión de esa limpieza/tooling, sin cambio funcional local demostrado.
- `028a4ca5c599e3ed22fddd084b0e50b71131c43c`: cambios locales de pruebas/configuración de ejecución; las correcciones productivas pertenecen principalmente a autenticación/bootstrap.

También se excluye documentación pura: `714c0c1d14df248141b0360d3318f4f95bf3816f` explica sincronización de liberación; `fe4ea49329432e1a74bd30a7a6477b2b52a283bb` documenta el bloqueo previo del traslado grupal; `c0c47f7f1bdf074782ed7a9af85dedb77c4918c6`, `6420dec362b77097539125466c630e44638b9bc8` y `d52929131d106717d8ef3629705c8df7c3fcea97` añaden reportes QA; `a1aaf13fbbbebd757eb1eb6256fa7dc0262bc295` renumera/retira reportes. Ninguno implementa las correcciones que describe.

Los cambios exclusivos de administración de layouts, seeds generales, infraestructura y capacidades internas de otros módulos quedan como contexto. Los merges sin cambios propios de Orders no se suman; la excepción contada es la resolución técnica identificada en `9e7ec66`.

## Commits relacionados

Fechas UTC y hashes cortos del dataset; orden ascendente por `(timestamp, full_hash)`. Cada fila describe únicamente el impacto local, incluidos los commits compartidos.

| Fecha | Commit | Tipo | Descripción |
|---|---|---|---|
| 2026-08-18 | f9a1405 | Feature | La migración de agrupación crea mesas, pedidos, cursos e ítems con restricciones de persistencia. |
| 2026-08-18 | 07a1a34 | Feature | Controller, servicio y repositorio incorporan creación/reemplazo y validación de destino y cursos. |
| 2026-08-18 | 7ddd750 | Feature | Reserva y devolución de stock pasan a transacciones para impedir persistir pedidos sin existencias. |
| 2026-08-18 | 53f452f | Feature | El DTO rechaza price y unitPrice del cliente y obliga a usar precios del servidor. |
| 2026-08-18 | d8ca186 | Feature | El despacho cambia el estado y crea un ticket transaccional para integrar la comanda con KDS. |
| 2026-08-18 | 2822a6f | Feature | La migración añade startedAt y readyAt a cursos e ítems para conservar tiempos operativos de cocina. |
| 2026-08-18 | 6322019 | Feature | Incorpora eventos operativos y captura fallos de emisión para desacoplar el despacho persistido del socket. |
| 2026-08-18 | 206796e | Feature | Bloquea recursos y revalida ítems pendientes antes de editar pedidos enviados a cocina. |
| 2026-08-19 | 97ce5d2 | Feature | Coordina bloqueos de mesa y transición ACCOUNT_REQUESTED para congelar pedidos durante revisión de cuenta. |
| 2026-08-19 | 8711bae | Feature | La relación account_orders y el cierre transaccional finalizan los pedidos vinculados al cobro. |
| 2026-08-20 | db61259 | Fix | Expone catálogo con UUID reales, categorías y seed estable para crear pedidos con platos persistidos. |
| 2026-08-20 | cf67edc | Feature | La API de mesas expone mesas activas, estado y pedido actual para selección operativa. |
| 2026-08-20 | 9e7ec66 | Configuration | La resolución propia del merge combina menú y mesas perdiendo el registro de TablesController y TablesService. |
| 2026-08-20 | 774c43e | Fix | Restituye TablesController y TablesService en OrdersRoutesModule tras la pérdida de registro. |
| 2026-08-20 | f9cf8fd | Fix | Middleware, guardas y validación de actor restringen operaciones; caja queda limitada a pedidos para llevar. |
| 2026-08-21 | 40c2a00 | Fix | Espera emisiones asíncronas del gateway autenticado para capturar correctamente fallos de notificación. |
| 2026-08-21 | cd662cb | Fix | Añade consulta por ID y conserva precios persistidos al reemplazar platos existentes. |
| 2026-08-21 | 6e389cf | Fix | Serializa actualizaciones y publica cambios de disponibilidad, con errores de stock identificables. |
| 2026-08-21 | 41b3d7a | Fix | Valida categorías por secuencia de curso y rechaza platos incompatibles con el tiempo solicitado. |
| 2026-08-21 | f46e02d | Fix | Los eventos de revisión/cierre de cuenta llegan a terminales de meseros para actualizar la vista operativa. |
| 2026-08-27 | da0eaab | Feature | DTO y mapper incorporan dishName y timeLabel para el resumen por tiempos. |
| 2026-08-27 | 2cc3523 | Feature | Persiste el estado operativo de mesa con FREE, OCCUPIED y PENDING_RELEASE. |
| 2026-08-27 | 049b082 | Feature | El cierre de cuenta deja mesas pendientes de liberación con auditoría y eventos. |
| 2026-08-27 | cf1fad8 | Feature | Añade liberación manual desde estado pendiente mediante transacción serializable y auditoría. |
| 2026-08-27 | 5a11523 | Feature | Rechaza pedidos en mesas pendientes y expone estado derivado para el ciclo de liberación. |
| 2026-08-27 | cab4dc3 | Fix | Ocupa mesas atómicamente, reintenta liberaciones y hace backfill SQL de ocupación preexistente. |
| 2026-08-27 | ae858af | Fix | Ajusta temporalmente roles de liberación a caja, administrador y supervisor. |
| 2026-08-28 | 1f21809 | Feature | Añade contratos, requestId, versiones y auditoría homogénea; reserva la liberación al mesero. |
| 2026-08-29 | dfacff8 | Feature | Habilita traslado individual con bloqueo de pedido/mesas, reasignación y auditoría. |
| 2026-08-29 | 92bcf56 | Fix | Añade reintento P2034 y eventos de ambas mesas para endurecer el traslado existente. |
| 2026-08-29 | 195cf76 | Feature | Persiste grupos y membresías históricas con API y validación inicial de contigüidad. |
| 2026-08-29 | 1ec1285 | Feature | Expone la cuenta consolidada del grupo y restringe cambios de membresía después de crearla. |
| 2026-08-29 | 0b9db00 | Feature | Añade disolución atómica con bloqueo de miembros, validación de cuentas, auditoría y evento. |
| 2026-08-29 | 794171c | Feature | Traslada pedidos, miembros y referencia de cuenta del grupo y registra historial de movimientos. |
| 2026-08-29 | 6adcb38 | Refactor | Extrae relaciones tipadas de Prisma y sustituye mapeos any del estado de grupo. |
| 2026-09-04 | 98b0bc4 | Feature | Integra MenuService con menú diario y sincroniza disponibilidad del catálogo operativo. |
| 2026-09-04 | f937ce4 | Fix | Adapta la sincronización a asignaciones del modelo unificado de menú diario. |
| 2026-09-04 | 5931b01 | Fix | Elimina actualización directa en OrdersRepository y concentra disponibilidad en DailyMenuRepository. |
| 2026-09-04 | 9104dd8 | Fix | Ajusta disponibilidad a contrato booleano, corrige roles y evita eventos cuando no hay cambios. |
| 2026-09-04 | f12acbe | Feature | Propaga actorUserId para atribuir cambios de disponibilidad a su ejecutor. |
| 2026-09-04 | df58630 | Configuration | Registra Swagger/JSON y anotaciones de errores para publicar el contrato técnico de pedidos y menú. |
| 2026-09-05 | 2c02afe | Feature | Añade agregado y modificación incremental de ítems con precios del catálogo, stock y auditoría. |
| 2026-09-05 | a977f72 | Feature | Incorpora cancelación dedicada con permiso ORDER_CANCEL, autorización de preparados y eventos. |
| 2026-09-05 | 4c70d61 | Refactor | Sustituye ordenamientos implícitos por comparadores explícitos en recursos de persistencia. |
| 2026-09-05 | e7fd477 | Refactor | Extrae autorización y traducción de errores de cancelación para separar responsabilidades. |
| 2026-09-06 | b778e43 | Fix | Introduce liberación automática de mesa al cancelar todos los ítems y publica la transición. |
| 2026-09-06 | 5e6e491 | Fix | La disolución considera solo cuentas no cerradas y permite separar grupos después del cobro. |
| 2026-09-06 | 3b47891 | Fix | Excluye cuentas CLOSED del estado activo del grupo sin borrar su historial. |
| 2026-09-06 | 7a02a23 | Fix | El trigger permite leftAt no nulo para retirar miembros durante disolución. |
| 2026-09-09 | cf6db70 | Feature | Persiste comensales con límites, auditoría, eventos y reinicio al liberar la mesa. |
| 2026-09-10 | 07cb085 | Feature | Integra reserva/devolución con asignaciones bloqueadas y contadores/versiones de stock por turno. |
| 2026-09-10 | 45e6b37 | Feature | Publica disponibilidad de asignaciones después de crear pedidos y consumir stock. |
| 2026-09-10 | 870bb9a | Feature | Extiende eventos de stock a agregado, modificación y cancelación de ítems. |
| 2026-09-10 | af0bedc | Feature | Crea sesiones de atención, membresías de mesas y la referencia serviceSessionId de pedidos. |
| 2026-09-10 | 52faa41 | Feature | Sustituye contigüidad física por conectividad del layout y guarda su referencia en el grupo. |
| 2026-09-10 | b9074a7 | Feature | Reutiliza sesión y cuenta al crear pedidos y elimina el rechazo previo por pedido abierto en servicio. |
| 2026-09-10 | 61822f0 | Feature | Añade contexto y eventos de grupo/sesión para propagar cambios operativos a terminales. |
| 2026-09-10 | 8edb36e | Feature | Administra el pool con autorización gerencial, auditoría y restricciones por turno y relaciones activas. |
| 2026-09-11 | 0500082 | Fix | Alinea TablePoolEvent con RestaurantTableResponseDto dentro de la remediación transversal. |
| 2026-09-11 | 181ca57 | Fix | Convierte los eventos del pool mediante mapOperationalTable para uniformar temporalmente sus payloads. |
| 2026-09-11 | 8e1b99a | Fix | Recupera payloads diferenciados de actualización y creación/baja de mesas del pool. |
| 2026-09-12 | e36be14 | Fix | Calcula adyacencia desde placements y adapta el trigger SQL al criterio de agrupación por layout. |
| 2026-09-12 | 2037a1b | Feature | Introduce cuenta operacional para nueva facturación parcial y vincula pedidos manteniendo continuidad de sesión. |
| 2026-09-12 | 5ef3661 | Fix | Solo ocupa la mesa si estaba FREE, evitando repetir la transición en sesiones ya ocupadas. |
| 2026-09-12 | b6940a9 | Fix | Renumera el pool, limita la baja a la última mesa y ajusta creación a capacidad cuatro sin PIN adicional. |
| 2026-09-13 | aa11910 | Fix | Restituye en el trigger la salida de miembros durante la disolución de un grupo. |
| 2026-09-13 | 61c5180 | Fix | Cierra sesiones de cuentas finalizadas y permite iniciar otra sin bloquear por ciclos anteriores. |
| 2026-09-14 | 5f98165 | Fix | Traduce ausencia de layout publicado a 422 con código de dominio estable al crear pedidos. |
| 2026-09-14 | d3a6f1f | Fix | Restringe disponibilidad a cocina y explicita roles autorizados para lectura de grupos. |
| 2026-09-14 | e36586a | Fix | Usa fecha operacional en la consulta de stock destinada a eventos de pedidos. |
| 2026-09-14 | f042dea | Fix | Adopta espacios y estados ingleses en DTO, mappers y migración de mesas. |
| 2026-09-15 | d431971 | Fix | Revierte temporalmente contratos, mappers y migración de espacios al estado anterior. |
| 2026-09-15 | 651467f | Fix | Repone los contratos ingleses de mesas y grupos tras su reversión. |
| 2026-09-15 | 3a571a7 | Fix | Aplica fecha operacional a disponibilidad y publica respuesta 423 de autorización sensible en cancelación. |
| 2026-09-15 | f5436a3 | Fix | Conserva IDs y consumos, revalida cancelaciones, mueve membresías de sesión y retira liberación automática de mesa. |
| 2026-09-15 | 4d5e640 | Fix | Hace idempotente el despacho y selecciona asignaciones por turno abierto para corregir disponibilidad. |
| 2026-09-15 | 80d325f | Fix | Valida grupos de dos a cuatro mesas y bloquea el grupo al agregar miembros. |
| 2026-09-15 | f804682 | Fix | Migra espacios históricos de grupos, completa OpenAPI y elimina fallbacks de persistencia en pedidos. |
| 2026-09-16 | 680138b | Fix | Consume/devuelve asignaciones activas de categorías regulares y publica variaciones de stock al reemplazar cursos. |
