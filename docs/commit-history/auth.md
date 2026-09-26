# Auth

## Vista general

| Elemento | Detalle |
|---|---|
| Módulo / Funcionalidad | Auth |
| Total de commits | 27 |
| Features | 13 |
| Fixes | 11 |
| Refactors | 0 |
| Configuración | 3 |
| Primer cambio registrado | 2026-08-15 |
| Último cambio registrado | 2026-09-15 |
| Días activos | 13 fechas UTC distintas |
| Estado | Activo |
| Snapshot | `516aac4bce5739619f562e7a1bd4e674edfa432f`, rama `develop` |
| Alcance | Selección funcional de Auth sobre el dataset global de 337 commits; incluye identidad, sesiones, autorización compartida, provisionamiento y configuración de IP pertinente. |

Fuente: `.analysis/history-data.json`, diffs y contenido del snapshot. Las fechas corresponden al committer en UTC; la tabla final sigue el orden ascendente `(timestamp, full_hash)`. Los 27 commits comprenden 26 no merges y un merge con resolución propia documentada en `analysis.merge_reviews`. No representan 27 capacidades nuevas ni cobertura de todo el backend. El historial recopilado no es shallow.

La revisión fue estática: no se ejecutaron el proyecto, migraciones ni pruebas. El dataset registraba árbol limpio; durante la revisión Git mostraba `docs/commit-history/` sin seguimiento y HEAD permanecía igual. Los cambios locales de documentación no se atribuyen al snapshot.

## Estructura

```text
Auth
├── Identificación
│   ├── PIN de cuatro dígitos y hash scrypt
│   └── Email y contraseña bcrypt
├── Sesiones
│   ├── Token opaco, hash persistido y expiración
│   ├── Consulta de identidad y permisos
│   └── Revocación y auditoría
├── Protección de acceso
│   ├── Registro transaccional de fallos y bloqueo
│   ├── Identidad por usuario/terminal; IP como alternativa
│   └── Autorización sensible y desbloqueo gerencial
├── Autorización compartida
│   ├── Guards de identidad y roles
│   └── Permisos para cuentas, pedidos y layouts
└── Provisionamiento e integración
    ├── Seeds de usuarios, roles y credenciales
    ├── Migraciones de identidad y eliminación de fingerprints
    ├── Registro de servicios compartidos
    └── Contratos OpenAPI y confianza en proxies
```

## Descripción

En el snapshot, `src/modules/auth/controllers/auth.controller.ts` expone cinco endpoints bajo `/api/v1/auth`: `pin-login`, `password-login`, `unlock`, `logout` y `me`. `AuthModule` exceptúa los tres primeros del middleware Bearer; `unlock` exige autorización mediante PIN gerencial. El login por contraseña consulta usuarios activos con `passwordHash`: aunque su documentación se refiere al administrador, el servicio no impone por sí mismo un filtro de rol ADMIN.

`AuthService` genera tokens opacos de 48 bytes aleatorios y persiste su SHA-256. `AuthRepository` valida que la sesión no esté revocada, no haya expirado y pertenezca a un usuario activo. El TTL predeterminado es de 720 minutos. Las respuestas incluyen identidad, rol, permisos y datos de sesión; login, logout y desbloqueo generan registros de auditoría.

El login PIN y `ManagerPinAuthorizationService` rechazan coincidencias ambiguas entre usuarios activos. El umbral predeterminado es de tres fallos dentro de quince minutos, con bloqueo de cinco minutos. El registro del fallo, conteo y creación de bloqueo comparten una transacción y un advisory lock PostgreSQL. Los filtros combinan usuario y terminal cuando están presentes y recurren a IP solo si no existe ninguna de esas identidades. El desbloqueo utiliza un ámbito independiente `unlock:<hash del objetivo>`; los roles autorizadores predeterminados son ADMIN, SUPERVISOR y CASHIER.

La migración `20260914100000_remove_pin_fingerprints` elimina `auth_attempts.pinFingerprint`. El modelo mantiene sesiones, intentos, bloqueos, roles y permisos; la incorporación de contraseña permite `pinHash` nulo. `RolesGuard` y `AuthenticatedUserGuard` son infraestructura compartida con consumidores operativos.

El seed principal exige credenciales administrativas y PIN de demostración por entorno, valida cinco PIN distintos de cuatro dígitos y conserva usuarios y contraseña administrativa existentes. Esa preservación no debe generalizarse a todos los scripts: `seed-empty.ts` y `reset-and-seed-users.ts` mantienen rutas que actualizan credenciales existentes. `src/runtime-config.ts` valida `TRUSTED_PROXY_HOPS`, cuyo valor predeterminado es cero.

## Evolución del módulo

### 2026-08-15 a 2026-08-20 — Identidad, sesiones, auditoría y seed repetible

La base inicial reúne persistencia de usuarios, roles, permisos, intentos, bloqueos, sesiones y auditoría con login PIN y middleware Bearer (`f0be303`). El desarrollo posterior incorpora desbloqueo por PIN autorizado, umbral de tres fallos, datos de terminal en las respuestas y revocación limitada a sesiones activas (`d81468d`, `ae24b80`). La auditoría de login y logout completa la trazabilidad del ciclo de sesión (`a37a9b1`).

La protección por roles se introduce junto a Kitchen mediante un decorador y guard reutilizables (`52086ea`). El seed abandona el borrado y recreación global de identidad en favor de upserts dentro de una transacción con advisory lock (`0d670ee`): conserva referencias históricas, aunque en esa etapa todavía actualiza credenciales y levanta determinados bloqueos heredados.

### 2026-09-02 a 2026-09-06 — Contraseña administrativa y autorización sensible reutilizable

El acceso por contraseña atraviesa incorporación, reversión y nueva implementación (`f6b7972`, `ed02c66`, `3901cb9`). La segunda implementación usa `bcryptjs`, permite administradores sin PIN y registra auditoría. El guard de identidad aparece junto a la API de Menu (`b09f052`).

La autorización gerencial se extrae a `ManagerPinAuthorizationService` (`9505901`). Los seeds amplían permisos de reapertura/delegación y cancelación de pedidos (`1a3a5a3`, `a977f72`). `fb25164` exporta `PinHashService`; conserva el tipo global Feature porque la implementación de descuentos domina el commit, aunque su impacto local en Auth es integración técnica.

El merge `fd86afe` importa `ManagerPinAuthorizationService` pero omite registrarlo y exportarlo en `AuthRoutesModule`. Se cuenta exclusivamente esa composición técnica propia, con tipo Configuration y confianza media según `analysis.merge_reviews`; no se atribuyen al merge las capacidades de las ramas integradas. `b778e43` registra el proveedor, elimina el fallback de autorización y extiende los bloqueos al login por contraseña. La secuencia muestra una corrección verificable de integración, no una nueva implementación de autorización gerencial.

### 2026-09-10 a 2026-09-13 — Permisos y variantes de provisionamiento

Los permisos provisionados incorporan `LAYOUT_MANAGE` para ADMIN y SUPERVISOR (`d12121d`). La consolidación operativa devuelve 401 desde `CurrentUser` cuando falta contexto autenticado y añade un script de reset/seed de usuarios (`b6940a9`). La variante de seed vacío reutiliza las especificaciones de identidad y permisos junto al layout inicial (`06e43a5`, Configuration). Estos cambios son compartidos con las funcionalidades operativas; su presencia en un seed no los convierte automáticamente en cambios exclusivos de Auth.

### 2026-09-14 a 2026-09-15 — Bloqueos atómicos, credenciales externas y contrato consumible

La remediación elimina fingerprints de PIN, rechaza PIN duplicados y concentra registro/conteo/bloqueo en una transacción (`028a4ca`). También externaliza credenciales administrativas y preserva las existentes en el seed principal. El conteo transaccional deja de usar el último login exitoso como inicio de ventana: cambia el comportamiento previo, no solo la organización del código.

La revisión siguiente separa el ámbito de bloqueo del desbloqueo gerencial, aplica 423 al alcanzar el umbral de autorización sensible y exige PIN de seed únicos por entorno (`3a571a7`). Después, los filtros evitan que terminales distintas se bloqueen únicamente por compartir IP (`d078d99`).

La confianza en proxies pasa de aceptación general (`48b33eb`) a lista configurada (`f042dea`), se revierte (`d431971`), se restaura (`651467f`) y termina expresada como número validado de saltos (`d078d99`). Es pertinente a Auth porque determina `request.ip`. Finalmente, las interfaces de respuesta se convierten en DTO con metadatos Swagger y referencias explícitas desde el controller (`f804682`), corrigiendo los esquemas publicados de identidad, sesión y desbloqueo.

## Análisis del historial

### Indicadores observados

- 27 commits únicos asignados: 13 Feature, 11 Fix, 0 Refactor y 3 Configuration; 26 no merges y un merge con cambios propios.
- Actividad en 13 fechas UTC distintas, desde el 15 de agosto hasta el 15 de septiembre de 2026.
- Nueve commits el 14–15 de septiembre UTC: ocho Fix y un Configuration; como comparación, seis commits el 4–5 de septiembre: cinco Feature y un Configuration, incluido el merge propio. La concentración final abarca bloqueos, seeds, proxies y contratos, sin implicar por sí sola calidad o productividad.
- Tres commits del 18 de agosto desarrollan directamente bloqueo/desbloqueo, ciclo de sesión y auditoría; otro de ese día incorpora el guard de roles compartido.
- Tres commits muestran incorporación, retirada y reintroducción de acceso por contraseña; no deben contarse como tres capacidades activas diferentes.
- Cinco commits modifican la confianza en proxies: `48b33eb`, `f042dea`, `d431971`, `651467f` y `d078d99`.
- El snapshot de `test/auth-pin-lockout.e2e.ts` contiene cuatro escenarios: concurrencia de login, concurrencia de autorización sensible, aislamiento terminal/IP y bloqueo explícito de usuario. `test/admin-password-login.e2e.ts` contiene un escenario de login administrativo. Se leyeron como evidencia, sin ejecutarlos.

### Compartidos, exclusiones y confianza

Los cambios de guards, permisos y servicios compartidos conectan Auth con Kitchen, Menu, Accounts, Orders y Layouts. Los seeds y la configuración de proxies son transversales. El dashboard global debe contar la unión de hashes, no sumar totales de módulos. Se conserva un solo tipo global por commit: en particular, `fb25164` es Feature, `06e43a5` es Configuration y `f804682` es Fix.

No se amplía la asignación a `f9cf8fd` y `40c2a00`: las revisiones de acceso de guards/socket en sus consumidores pertenecen a los módulos correspondientes; esta selección no les atribuye cambios del núcleo de Auth sin una revisión propia de sus diffs.

Exclusiones locales revisadas, que no equivalen a excluir esos commits del proyecto completo:

- `68d1858`: anotaciones y ejemplos Swagger del login por contraseña, sin cambio de autenticación; documentación pura del contrato.
- `8f54158`: formato en los archivos de Auth revisados; la configuración Sonar corresponde al ámbito técnico global.
- `4c70d61`: pruebas de repositorio y hashing en Auth, sin comportamiento productivo local; mantiene Refactor en la clasificación global, pero no se asigna aquí.
- `5473f85`: ampliación de pruebas de AuthService.
- `e7fd477`: limpieza de imports, uso de `node:crypto` y ajustes de pruebas, sin reorganización funcional local significativa.
- `dc77fc9` y `0500082`: formato del guard y de AuthService, respectivamente; las capacidades o correcciones operativas pertenecen a otros módulos.
- `1bd8cbe` y `3a082e5`: retirada y restauración de un import de una prueba de repositorio.
- `aa11910`: cambios de grilla, posiciones y publicación en los seeds de layout, sin modificar identidad ni permisos.

Las reversiones `ed02c66` y `d431971` tienen confianza media: la retirada está demostrada, pero su motivación correctiva no se desprende solo del diff. La resolución propia de `fd86afe` tiene confianza media conforme a la revisión de sus padres registrada en el dataset. En los commits transversales, la evidencia local sustenta la asignación a Auth y el tipo principal sigue la conciliación global; no se deduce únicamente del mensaje.

### Posibles puntos de atención y límites

El historial muestra revisiones recurrentes de identidad de bloqueo, integración del proveedor gerencial y preservación de credenciales en seeds. Esto sugiere un proceso de endurecimiento y ajuste de integración, sin demostrar ausencia de fallos actuales. Conviene distinguir el seed principal de las variantes que actualizan usuarios existentes y el bloqueo de login del ámbito de autorización sensible.

Los filtros actuales combinan usuario y terminal cuando ambos existen: describirlos como aislamiento exclusivamente por terminal sería inexacto. Las afirmaciones históricas de pruebas satisfactorias en documentación no son resultados comprobados por esta revisión. La tabla incluye únicamente la resolución propia del merge asignado, sin duplicar trabajo integrado ni declarar revisión individual completa de todos los commits del dataset global.

## Commits relacionados

| Fecha | Commit | Tipo | Descripción |
|---|---|---|---|
| 2026-08-15 | f0be303 | Feature | Crea login PIN, sesiones, middleware Bearer y persistencia de usuarios, roles, permisos, intentos y auditoría. |
| 2026-08-18 | d81468d | Feature | Incorpora desbloqueo gerencial, umbral de tres fallos y constraints de identidad y hash PIN. |
| 2026-08-18 | ae24b80 | Feature | Añade terminal y sesión a login/me y limita la revocación a sesiones activas. |
| 2026-08-18 | a37a9b1 | Feature | Registra auditoría de login exitoso y logout con contexto de sesión y terminal. |
| 2026-08-18 | 52086ea | Feature | Incorpora decorador y guard de roles reutilizables junto a la integración de Kitchen. |
| 2026-08-20 | 0d670ee | Fix | Sustituye borrados globales del seed por upserts transaccionales que conservan IDs e historial relacionado. |
| 2026-09-02 | f6b7972 | Feature | Añade email/passwordHash, seed administrativo y login por contraseña bcrypt. |
| 2026-09-03 | ed02c66 | Fix | Revierte endpoint, DTO, migración y seed de la primera incorporación de contraseña administrativa. |
| 2026-09-03 | 3901cb9 | Feature | Restablece login administrativo con bcryptjs, auditoría, seed por email y PIN opcional. |
| 2026-09-03 | b09f052 | Feature | Incorpora guard que exige contexto autenticado, compartido con la API de Menu. |
| 2026-09-04 | 9505901 | Feature | Centraliza autorización por PIN gerencial y roles en un servicio reutilizable para operaciones sensibles. |
| 2026-09-04 | 1a3a5a3 | Feature | Provisiona permisos de reapertura de cuentas y consulta/actualización de delegación. |
| 2026-09-05 | a977f72 | Feature | Amplía ORDER_CANCEL a WAITER, CASHIER y ADMIN en la matriz de permisos del seed. |
| 2026-09-05 | fb25164 | Feature | Exporta PinHashService para consumidores externos; conserva el tipo global de la incorporación de descuentos. |
| 2026-09-05 | fd86afe | Configuration | Resolución propia del merge: importa ManagerPinAuthorizationService pero omite su registro y exportación. |
| 2026-09-06 | b778e43 | Fix | Aplica bloqueos al login por contraseña, registra el proveedor gerencial y elimina el fallback de autorización. |
| 2026-09-10 | d12121d | Feature | Provisiona LAYOUT_MANAGE para ADMIN y SUPERVISOR junto a la administración de layouts. |
| 2026-09-12 | b6940a9 | Fix | Devuelve 401 desde CurrentUser sin identidad y añade provisionamiento de usuarios en la consolidación S4. |
| 2026-09-13 | 06e43a5 | Configuration | Añade seed vacío que reutiliza especificaciones de usuarios, administrador y permisos junto al layout inicial. |
| 2026-09-14 | 48b33eb | Configuration | Activa confianza en proxies y modifica la procedencia de la IP consumida por Auth. |
| 2026-09-14 | 028a4ca | Fix | Hace transaccional el bloqueo, elimina fingerprints, rechaza PIN duplicados y preserva credenciales existentes en el seed principal. |
| 2026-09-14 | f042dea | Fix | Restringe confianza en proxies mediante lista configurada y publica un esquema compartido de errores. |
| 2026-09-15 | d431971 | Fix | Revierte la lista de proxies confiables y el esquema compartido de errores, restaurando temporalmente la confianza general. |
| 2026-09-15 | 651467f | Fix | Restituye la lista de proxies confiables y el esquema compartido de errores tras la reversión. |
| 2026-09-15 | 3a571a7 | Fix | Separa el ámbito de desbloqueo, aplica 423 en autorización sensible y exige PIN únicos de seed por entorno. |
| 2026-09-15 | d078d99 | Fix | Usa IP solo como identidad alternativa, aísla terminales que comparten IP y valida los saltos de proxy confiables. |
| 2026-09-15 | f804682 | Fix | Publica DTO concretos y esquemas OpenAPI de usuario, sesión, login y desbloqueo. |
