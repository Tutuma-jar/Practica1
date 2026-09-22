# Lista de arreglos

1. **El texto del botón "Agregar" no se veía correctamente**

   Se cambió el color del texto a blanco para generar suficiente contraste con el fondo azul del botón.

2. **El carrito aparecía detrás de las tarjetas de productos**

   Se asignó un `z-index` positivo al panel del carrito para mostrarlo por encima del contenido de la tienda.

3. **La búsqueda distinguía entre mayúsculas y minúsculas**

   Se normalizaron el título del producto y el texto buscado con `toLowerCase()` antes de compararlos.

4. **Los botones `+`, `-` y `x` del carrito no funcionaban correctamente**

   Los productos ahora se identifican mediante su `id` y las cantidades se actualizan usando el estado funcional de React. El botón `x` elimina solamente el producto seleccionado.

5. **Los botones no mostraban una respuesta visual al presionarlos**

   Se agregó un estado CSS `:active` que reduce ligeramente el tamaño y el brillo del botón durante la pulsación.

6. **El contador del carrito no se actualizaba inmediatamente**

   Se reemplazó la mutación directa del arreglo por una actualización inmutable con `setCart`, permitiendo que React detecte el cambio y renderice el contador de inmediato.

7. **Los productos iguales aparecían como líneas duplicadas en el carrito**

   Antes de agregar un producto se comprueba si su `id` ya existe. Si existe, se incrementa su cantidad; de lo contrario, se crea una nueva línea. El contador del encabezado suma todas las unidades.

8. **Un carrito largo no tenía una zona de desplazamiento adecuada**

   El panel se convirtió en una columna limitada a la altura del viewport y la lista de productos recibió desplazamiento vertical propio, manteniendo visibles el total y el botón de pago.

9. **El descuento se calculaba como una cantidad fija**

   Se corrigió la fórmula para aplicar `discountPercentage` como un porcentaje del precio: `price * (1 - discountPercentage / 100)`.

10. **El carrito no se podía cerrar después de abrirlo**

    Se agregó un botón "Cerrar" dentro del panel, conectado a una función que oculta el carrito.

11. **El carrito permitía superar las existencias disponibles**

    Los incrementos ahora están limitados por el valor de `stock`. Los botones "Agregar" y `+` se deshabilitan al alcanzar la cantidad máxima disponible.

12. **Los errores de red dejaban la tienda cargando indefinidamente**

    Se añadió la validación de respuestas HTTP, manejo de errores y finalización del estado de carga. Si la petición falla, se muestra un mensaje accesible al usuario.

13. **Una búsqueda antigua podía reemplazar los resultados actuales**

    Cada búsqueda utiliza un `AbortController`. Al cambiar el texto buscado, la petición anterior se cancela y ya no puede modificar los productos ni el estado de carga.

14. **Solo se podían explorar 30 productos y cuatro categorías**

    La carga inicial solicita el catálogo completo con `limit=0` y las categorías se obtienen desde el endpoint `category-list`. Las categorías originales se conservan como respaldo si esa petición falla.

15. **Las imágenes desbordaban las tarjetas en pantallas pequeñas**

    El ancho fijo de `300px` se reemplazó por `width: 100%`, haciendo que cada imagen se adapte al espacio disponible.

16. **El botón `-` no hacía nada cuando quedaba una unidad**

    La actualización de cantidades ahora elimina la línea del carrito cuando la cantidad llega a cero.

17. **El filtro local eliminaba resultados válidos de la API**

    Se eliminó el segundo filtro por título para conservar todos los productos devueltos por la API. El selector de categoría mantiene su filtro independiente.

18. **Las búsquedas amplias estaban limitadas a 30 productos**

    Se agregó `limit=0` al endpoint de búsqueda para solicitar todas las coincidencias disponibles.

19. **Los espacios alrededor de una búsqueda producían resultados incorrectos**

    Se normaliza la consulta con `trim()` antes de enviarla. Una entrada compuesta solo por espacios se trata como una búsqueda vacía.

20. **Los precios mostrados no correspondían con el total**

    Se centralizó el cálculo del precio descontado y ahora las tarjetas, el carrito y el total utilizan exactamente el mismo valor.

21. **Al comprar productos no se actualizaba el stock mostrado**

    El stock de la tarjeta no reflejaba las unidades agregadas al carrito ni las compradas. Ahora el stock visible se calcula restando las unidades reservadas en el carrito: baja al agregar, sube al quitar, y al pagar se descuenta definitivamente del catálogo. El botón se deshabilita y muestra "Sin stock" cuando no quedan unidades.

# Arreglos pendientes

1. **Durante una búsqueda permanecen productos anteriores en pantalla**

   Estado: pendiente. Al iniciar una petición se activa el indicador de carga, pero los resultados anteriores continúan visibles hasta que llega la nueva respuesta.

2. **Se realiza una petición por cada tecla escrita**

   Estado: pendiente. La búsqueda no tiene debounce. Aunque las peticiones anteriores se cancelan, escribir una palabra genera varias solicitudes innecesarias.

3. **El carrito puede desbordarse horizontalmente en móvil**

   Estado: pendiente. Cada producto coloca imagen, título, precio, cantidad y eliminación en una sola fila que no se adapta correctamente a pantallas estrechas.

4. **El carrito no administra correctamente el foco del teclado**

   Estado: pendiente. El panel no funciona como diálogo, no mueve ni retiene el foco y tampoco puede cerrarse con la tecla `Escape`.

5. **El carrito se pierde al recargar la página**

   Estado: pendiente. Los productos se almacenan únicamente en el estado de React y se eliminan al recargar la página.

6. **Se cargan inmediatamente las imágenes de todo el catálogo**

    Estado: pendiente. Las imágenes no utilizan carga diferida, por lo que el navegador puede solicitar las imágenes de los 194 productos aunque todavía no sean visibles.

7. **Los botones deshabilitados de stock siguen pareciendo interactivos**

    Estado: pendiente. El botón conserva el fondo azul y `cursor: pointer` cuando alcanza el stock máximo, aunque ya no se pueda presionar.

8. **Un error al cargar las categorías queda oculto**

    Estado: pendiente. Si falla el endpoint de categorías, la aplicación vuelve silenciosamente a cuatro categorías y no informa al usuario que el selector está incompleto.
