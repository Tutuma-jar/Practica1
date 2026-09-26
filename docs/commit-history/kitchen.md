# Kitchen

## Vista general

| Elemento | Detalle |
|---|---|
| Módulo / Funcionalidad | Kitchen |
| Total de commits | 45 |
| Features | 23 |
| Fixes | 20 |
| Refactors | 1 |
| Configuración | 1 |
| Primer cambio registrado | 2026-08-18 |
| Último cambio registrado | 2026-09-15 |
| Estado | Activo |
| Días activos | 17 |
| Alcance | Kitchen: KDS, preparación, alertas y transporte compartido de eventos; revisión enfocada dentro del alcance global de cinco módulos. |
| Snapshot | Rama `develop`, HEAD `516aac4bce5739619f562e7a1bd4e674edfa432f`; dataset `.analysis/history-data.json`, 337 commits recopilados, historial no shallow. |

Los 45 commits incluyen 44 no merges y una resolución propia de merge. Las fechas son de committer en UTC y el orden procede de `(timestamp, full_hash)` del dataset. Los cambios compartidos se cuentan una sola vez aquí; los totales globales deben calcularse por unión de hashes, no sumando módulos. La revisión inicial observó únicamente `docs/commit-history/` sin seguimiento, frente al árbol limpio registrado al recopilar el dataset. Código y pruebas se inspeccionaron estáticamente; no se ejecutaron proyecto, migraciones ni suites. Este documento no implica validación global del conjunto documental ni actualización de `analysis`.

## Estructura

```text
Kitchen
├── Cola KDS
│   ├── Recepción de pedidos y tickets secuenciados
│   ├── Consulta de trabajo activo
│   └── Orden estable de llegada
├── Preparación y entrega
│   ├── Transiciones individuales y por tiempo
│   ├── Concurrencia e idempotencia
│   ├── Timestamps y tratamiento de cancelados
│   └── Auditoría del actor y del cambio
├── Alertas a meseros
│   ├── Una notificación persistente por tiempo
│   ├── Consulta y recuperación paginada
│   └── Confirmación explícita o asociada a entrega
└── Integración operacional
    ├── Autenticación WebSocket y salas por rol
    ├── Eventos de pedidos, cuentas y operaciones sensibles
    ├── Eventos de mesas, layouts y sesiones
    ├── Disponibilidad y stock del menú
    └── Reinicio de datos operativos relacionados
```

## Descripción

En el snapshot, `KitchenRepository.findTickets` excluye pedidos `CLOSED` y `CANCELLED`; conserva ítems `PENDING`, `IN_PREPARATION` y `READY`, y ordena los tickets por `receivedAt`, `sequenceNumber` e `id`. El filtro opcional de estado selecciona tickets coincidentes, mientras que su contenido conserva los ítems operativos. `KitchenController` expone consulta KDS, modificación de ítems y tiempos, y entrega de un tiempo. Las rutas de preparación requieren KITCHEN, ADMIN o SUPERVISOR; la entrega admite WAITER, ADMIN o SUPERVISOR.

Servicio y repositorio comprueban transiciones y el estado previamente leído antes de persistir. Las modificaciones colectivas omiten cancelados y rechazan tiempos sin ítems activos. Los cambios individuales propagan `startedAt` o `readyAt` al tiempo cuando todos sus ítems activos alcanzan el estado correspondiente y el timestamp agregado sigue vacío. Esa propagación escribe timestamps: no actualiza por sí sola el estado agregado. Cuando se proporciona el actor completo, el repositorio registra la auditoría dentro de la transacción de cambio.

Las notificaciones tienen unicidad por `orderCourseId` y estados `PENDING`, `SENT` y `ACKNOWLEDGED`. La recuperación WebSocket devuelve páginas de hasta 100 notificaciones pendientes o enviadas sin confirmar; REST permite listado y detalle. La entrega puede confirmar la alerta del tiempo, y la confirmación conserva actor y fecha. La condición de completitud ignora cancelados, pero el payload incluye todos los ítems: `test/kitchen-ready-notifications.e2e.ts` verifica explícitamente este contrato para READY + CANCELLED.

El namespace `/kitchen` autentica conexiones y distribuye eventos por salas de cocina, meseros y caja, revalidando las sesiones antes de emitir. Las alertas de meseros se restringen a WAITER. `KitchenGateway` sirve también como transporte para pedidos, cuentas, mesas, layouts, sesiones, menú y auditoría: sus eventos compartidos no deben confundirse con nuevas operaciones de preparación.

## Evolución del módulo

### 2026-08-18–2026-08-21 — Implementación y ajuste del circuito KDS–meseros

El despacho de Orders crea un ticket único y secuenciado dentro de la transición del pedido a cocina (`d8ca186`). Sobre esa base se incorporan consulta KDS, cambios de estado individuales y colectivos, timestamps persistentes y eventos posteriores a la persistencia (`52086ea`, `2822a6f`, `6322019`). Los pedidos enviados conservan posibilidad de edición mientras sus ítems sigan pendientes; `206796e` comunica esas modificaciones al KDS.

El circuito de meseros añade canal WebSocket, almacenamiento consolidado por tiempo, consulta REST, confirmación y sincronización (`7c3212b`–`7776d03`). Cuatro migraciones específicas crean tickets, timestamps, notificaciones y datos de confirmación. La unicidad de notificaciones evita duplicar el registro ante intentos concurrentes.

Las correcciones posteriores protegen el canal y acotan la cola: guardas REST/socket, validación de conexiones, revalidación de sesiones y autorización coherente para alertas (`fed2434`, `40c2a00`, `05d007b`); `392ec64` retira trabajo inactivo del KDS. La recuperación cambia de estrategia: `0c33ee6` buscaba tiempos completos sin notificación, pero `7282ea7` elimina esa búsqueda y recupera registros ya persistidos mediante cursor, marcándolos enviados tras emitir y evitando confirmaciones duplicadas. HEAD no implementa con este mecanismo un reconciliador general de alertas inexistentes.

`41b3d7a` añade, dentro de un cambio principal de Orders, un reinicio transaccional que elimina explícitamente notificaciones y tickets. Su impacto local documentado es el mantenimiento de datos relacionados, no la validación de categorías de platos. La disponibilidad del menú y las cuentas de caja empiezan a utilizar el mismo canal (`6e389cf`, `f46e02d`).

### 2026-08-27–2026-09-11 — Ampliación del transporte compartido y ajuste de contratos

El gateway incorpora estados y liberación de mesas, grupos, transferencias y consolidación de cuentas (`049b082`, `cf1fad8`, `1f21809`), cierre de menú (`b3ca733`), reaperturas, modificaciones y cancelaciones (`1a3a5a3`, `2c02afe`, `a977f72`). `fb25164`, pese a su mensaje de pruebas, incorpora emisores productivos de descuentos y operaciones sensibles; se clasifica Feature.

La resolución propia del merge `fd86afe` conserva dos definiciones de `ItemCancelledEvent` y duplicados de `emitItemCancelled` e imports en los archivos del gateway. Se cuenta únicamente esa composición técnica como Configuration, confianza media, siguiendo `analysis.merge_reviews`; no se le atribuyen descuentos, reapertura o cancelación ya implementados en sus padres. `0c8cc1c` elimina duplicados y compatibiliza contratos; `e7fd477` precisa las uniones de estados sin añadir comportamiento de ejecución.

Después se añaden divisiones de cuentas, apertura y stock del menú y eventos de layouts y sesiones (`904e2d1`, `f664c3a`, `61822f0`). `45e6b37` conecta un productor externo real: tras crear un pedido, Orders consulta asignaciones y publica `menu:stock_changed` con cantidades y versión mediante el gateway existente. No se cuenta como creación de un segundo emisor.

Hay una revisión observable del payload de mesas: `181ca57` aplica `mapOperationalTable` a todos los métodos de emisión; `8e1b99a` restaura la distinción entre `emitTableUpdated` y los demás métodos, que reciben `response`. Ambos afectan el contrato entregado al transporte compartido, no la cola KDS; el segundo revierte específicamente esa parte del primero. El historial muestra el cambio y su reversión, sin demostrar por el mensaje cuál forma es correcta para todos los consumidores.

### 2026-09-06–2026-09-15 — Preparación parcial, timestamps, entrega y trazabilidad

En paralelo a la ampliación de eventos, `b778e43` excluye cancelados de las transiciones colectivas y rechaza tiempos sin activos. `f30f32d` incorpora propagación de timestamps desde ítems al tiempo; `test/kitchen-timestamps.e2e.ts` comprueba que solo el último ítem activo que alcanza el estado provoca la escritura agregada y que repetir el estado conserva la fecha.

`b6940a9` incorpora entrega de tiempos y `61c5180` conecta esa entrega con la confirmación de su alerta. `f5436a3` comparte la condición de completitud entre timestamps y notificaciones, permitiendo avisos READY + CANCELLED, manteniendo la exclusión de tiempos completamente cancelados. La prueba externa de notificaciones contempla recuperación REST tras fallo del emisor, unicidad y concurrencia entre entrega y confirmación; estas pruebas fueron leídas, no ejecutadas.

El mantenimiento de datos vuelve a aparecer en `1623a88`: el reset elimina tickets antes de pedidos, de acuerdo con la relación restrictiva de `kitchen_tickets.orderId`. `61d94e4` conecta el registro de operaciones sensibles con un evento posterior a la transacción. `b5caea1`, Feature global, hace nullable `tableId` en eventos de cuentas para representar cuentas sin mesa. Finalmente, `4d5e640` incorpora auditoría transaccional del actor y antes/después de los estados, y `f804682` completa la descripción OpenAPI de los enums operativos.

## Análisis del historial

### Indicadores observados

- 45 commits únicos asignados: 23 Feature, 20 Fix, 1 Refactor y 1 Configuration; 17 fechas UTC activas entre el 18 de agosto y el 15 de septiembre de 2026.
- 11 commits incluidos en los dos primeros días UTC, frente a 7 en los dos siguientes: la primera ventana concentra implementación KDS/alertas, y la segunda combina correcciones y primeras integraciones.
- 6 commits el 5 de septiembre UTC: tres ampliaciones funcionales, una resolución propia de merge, una corrección y un refactor de contratos; el volumen no mide calidad ni complejidad.
- 4 migraciones iniciales específicas: `20260818130000_add_kitchen_tickets`, `20260818133000_add_kitchen_status_timestamps`, `20260818140000_add_waiter_notifications` y `20260818143000_add_waiter_notification_acknowledgement`.
- 2 pruebas externas específicas inspeccionadas: `test/kitchen-timestamps.e2e.ts` y `test/kitchen-ready-notifications.e2e.ts`; su existencia no acredita ejecución satisfactoria.
- 3 claves de ordenación de tickets y páginas de 100 notificaciones en HEAD; son propiedades del código, no métricas de rendimiento.

### Cierre de los seis pendientes transversales

Los diffs se examinaron con `rtk proxy git show --no-ext-diff --no-textconv`. La asignación sigue el impacto concreto, no la presencia de la palabra kitchen ni el título del commit.

| Commit completo | Decisión local | Evidencia y límite |
|---|---|---|
| 41b3d7a23df1eff471f761cbc60ac2249c55228f | Incluir Fix; confianza media | `prisma/reset-operations.ts` incorpora `waiterNotification.deleteMany()` y `kitchenTicket.deleteMany()` en la transacción de reset; compartido con Orders/Accounts, sin atribuir a Kitchen las categorías de platos. |
| 45e6b37e288c0b8fd0d1065c87abbcbcca9bc1f2 | Incluir Feature; confianza alta | `OrdersService.publishDailyMenuStockChanges` llama a `emitMenuStockChanged` después de crear el pedido y consultar asignaciones; productor externo compartido con Orders/Menu. |
| 181ca5790a14dbdfc00dd9f3b9e080ac3d601155 | Incluir Fix; confianza media | `TablesService` normaliza el payload enviado a los métodos de `KitchenGateway`; impacto limitado a contratos compartidos de mesas. |
| 8e1b99a37bbbc2f7868f8d5071321d9b67751938 | Incluir Fix; confianza media | `TablesService` revierte la normalización universal y diferencia `emitTableUpdated`; seed y pruebas de turno quedan fuera del impacto local. |
| 1623a88d66fe1ff9ef026e990db3e1b680321ed7 | Incluir Fix; confianza alta | `prisma/reset-operations.ts` mueve el borrado de tickets antes de pedidos; corrige orden de limpieza respecto a la FK restrictiva, sin atribuir cambios de layouts o formato a Kitchen. |
| 3a571a7aad671badcfff361dc5bc63291741542c | Excluir localmente | `test/kitchen-timestamps.e2e.ts` cambia import de Supertest, PINs de fixtures y `search_path`; no modifica timestamps ni comportamiento Kitchen, y las remediaciones productivas pertenecen a Auth, Accounts, Menu y tooling. |

### Exclusiones locales y cambios compartidos

Se excluye `967cab1` por añadir únicamente una prueba de ordenación. `4c70d61` (Refactor global) solo amplía pruebas del repositorio de notificaciones dentro de Kitchen; `5473f85` solo amplía pruebas de eventos y autenticación. `cf6db70` únicamente adapta `guestCount` en un fixture local y `f0fc160` reformatea una unión de tipos.

`1bd8cbe`, `3a082e5` y `028a4ca` eliminan, restauran y vuelven a eliminar una variable no usada en la prueba del gateway. `f042dea`, `d431971` (Fix global) y `651467f` cambian, revierten y restauran el enum de espacio en ese fixture. Esos cambios no se cuentan como comportamiento de Kitchen aunque tengan efectos productivos en otros dominios. Los reportes QA puramente documentales, como `c0c47f7` y `6420dec`, tampoco se cuentan como implementación ni prueban por sí mismos una corrección.

Las ampliaciones del gateway para pedidos, cuentas, mesas y menú son compartidas; `61d94e4` y `4d5e640` también conectan auditoría. Sus tipos principales respetan las decisiones globales, especialmente Feature para `fb25164` y `b5caea1`, y Fix para `fed2434` y `f804682`. No se trasladan automáticamente otros commits del mismo dominio a Kitchen por dependencia general.

### Interpretación y límites

La repetición de cambios sobre recuperación, cancelados, timestamps y confirmación sugiere estabilización de un flujo incorporado por etapas. Las áreas históricamente recurrentes son consistencia entre estado individual y colectivo, contrato de recuperación persistida y compatibilidad del gateway compartido. No se diagnostican defectos actuales a partir de esa recurrencia.

La confianza es media para la atribución principal de commits transversales amplios y para la resolución propia de `fd86afe79cc29f1e24850aade132e1f395b7a1f9`; la evidencia concreta local se especifica en la narrativa y la tabla. Se usa la revisión de merges registrada en el dataset, contando solo los duplicados exclusivos del gateway para ese merge. Las demás integraciones no se convierten en nuevas funcionalidades locales. El cierre de los seis pendientes no constituye una afirmación de auditoría exhaustiva de todos los productores externos del repositorio ni de todo su historial QA.

## Commits relacionados

| Fecha | Commit | Tipo | Descripción |
|---|---|---|---|
| 2026-08-18 | d8ca186 | Feature | Crea ticket único y secuenciado al despachar pedidos y emite `order:created`; compartido con Orders. |
| 2026-08-18 | 52086ea | Feature | Añade consulta KDS y cambios de estado de ítems/tiempos con control de transiciones y roles. |
| 2026-08-18 | 2822a6f | Feature | Persiste y expone `startedAt` y `readyAt` mediante migración y cambios transaccionales. |
| 2026-08-18 | 6322019 | Feature | Emite cambios operativos tras persistencia y contiene fallos WebSocket; compartido con Orders. |
| 2026-08-18 | 206796e | Feature | Comunica modificaciones de pedidos pendientes al KDS y bloquea edición tras preparación. |
| 2026-08-19 | 7c3212b | Feature | Incorpora sala de meseros, suscripción y evento de alerta. |
| 2026-08-19 | c8d49a9 | Feature | Persiste una notificación consolidada por tiempo completo y evita registros duplicados. |
| 2026-08-19 | de4d762 | Feature | Añade consulta REST y confirmación con usuario y fecha persistentes. |
| 2026-08-19 | 7776d03 | Feature | Expone sincronización WebSocket de notificaciones no confirmadas. |
| 2026-08-19 | fed2434 | Fix | Protege REST y suscripción de alertas mediante roles y validación de sesión. |
| 2026-08-19 | 0c33ee6 | Fix | Revalida destinatarios, conserva pendientes sin entrega y añade recuperación y evento de ACK. |
| 2026-08-20 | 392ec64 | Fix | Filtra pedidos e ítems inactivos de KDS y añade desempate estable por identificador. |
| 2026-08-21 | 40c2a00 | Fix | Autentica conexiones y restringe emisión a salas autorizadas, desconectando sesiones inválidas. |
| 2026-08-21 | 6e389cf | Fix | Distribuye cambios de disponibilidad de menú a cocina y meseros. |
| 2026-08-21 | 05d007b | Fix | Unifica la autorización de alertas REST/socket exclusivamente para WAITER. |
| 2026-08-21 | 7282ea7 | Fix | Recupera alertas persistidas mediante cursor y evita emisiones duplicadas de confirmación. |
| 2026-08-21 | 41b3d7a | Fix | Incluye tickets y notificaciones en el reinicio transaccional de datos operativos. |
| 2026-08-21 | f46e02d | Fix | Añade sala de caja y distribución de solicitud/cierre de cuentas; compartido con Accounts. |
| 2026-08-27 | 049b082 | Feature | Transporta cambios de estado de mesa, incluido PENDING_RELEASE, a meseros y caja. |
| 2026-08-27 | cf1fad8 | Feature | Emite liberación de mesa con datos del actor; compartido con Tables. |
| 2026-08-28 | 1f21809 | Feature | Integra contratos y emisores de grupos, transferencias y consolidación de cuentas. |
| 2026-09-03 | b3ca733 | Feature | Notifica cierre del menú diario a cocina y meseros. |
| 2026-09-04 | 1a3a5a3 | Feature | Incorpora contrato y distribución de reapertura controlada de cuentas. |
| 2026-09-05 | 2c02afe | Feature | Versiona eventos de modificación de pedidos y los distribuye a tres salas. |
| 2026-09-05 | a977f72 | Feature | Añade contrato y emisor de cancelación de ítems para cocina, meseros y caja. |
| 2026-09-05 | fb25164 | Feature | Añade emisores productivos de descuentos y operaciones sensibles además de contratos compartidos. |
| 2026-09-05 | fd86afe | Configuration | Resolución propia del merge conserva duplicados de contratos, imports y emisor de cancelación del gateway; confianza media. |
| 2026-09-05 | 0c8cc1c | Fix | Elimina duplicados de cancelación y compatibiliza contratos del gateway. |
| 2026-09-05 | e7fd477 | Refactor | Restringe uniones redundantes de tipos en eventos de cancelación. |
| 2026-09-06 | b778e43 | Fix | Excluye cancelados de cambios colectivos y rechaza tiempos sin ítems activos. |
| 2026-09-09 | 904e2d1 | Feature | Incorpora eventos de creación, modificación y cierre de divisiones para caja y meseros. |
| 2026-09-10 | f664c3a | Feature | Publica apertura de menú y cambios de stock mediante el gateway compartido. |
| 2026-09-10 | 45e6b37 | Feature | Conecta creación de pedidos con eventos de stock de asignaciones hacia el gateway existente. |
| 2026-09-10 | 61822f0 | Feature | Añade emisores de layouts, pool de mesas y sesiones de servicio. |
| 2026-09-11 | f30f32d | Feature | Propaga timestamps individuales al tiempo una sola vez cuando coinciden todos los ítems activos. |
| 2026-09-11 | 181ca57 | Fix | Normaliza el payload de mesa para todos los métodos llamados en el gateway compartido. |
| 2026-09-11 | 8e1b99a | Fix | Restablece payload diferenciado entre actualización y otros eventos de mesa, revirtiendo la normalización universal. |
| 2026-09-12 | 1623a88 | Fix | Elimina tickets antes de pedidos en el reset para respetar su dependencia referencial. |
| 2026-09-12 | b6940a9 | Fix | Completa flujo colectivo con endpoint de entrega y estado DELIVERED en servicio y eventos. |
| 2026-09-13 | 61c5180 | Fix | Confirma la alerta asociada al entregar el tiempo y evita ACK repetido. |
| 2026-09-14 | 61d94e4 | Fix | Conecta operaciones sensibles con emisión posterior a la transacción; compartido con Audit. |
| 2026-09-14 | b5caea1 | Feature | Admite cuentas sin mesa mediante `tableId` nullable en cuatro contratos de eventos. |
| 2026-09-15 | f5436a3 | Fix | Unifica completitud de activos para timestamps y alertas, admitiendo READY + CANCELLED. |
| 2026-09-15 | 4d5e640 | Fix | Registra actor y antes/después de cambios operativos dentro de su transacción. |
| 2026-09-15 | f804682 | Fix | Completa enums de consulta y cambios de estado en el contrato OpenAPI generado. |
