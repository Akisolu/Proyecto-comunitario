# ☁️ Guía 11: Configuración del Respaldo en Google Drive — SGI Salud

Esta guía detalla paso a paso cómo configurar la API de Google Drive y las credenciales necesarias para que el sistema **SGI Salud** pueda realizar copias de seguridad automáticas y manuales en la nube de forma segura.

---

## 1. Introducción al Método de Respaldo

Para interactuar con Google Drive desde una aplicación de escritorio de forma automatizada y sin requerir que el usuario inicie sesión manualmente en su navegador cada vez, el sistema utiliza una **Cuenta de Servicio (Service Account)** de Google Cloud.

### Ventajas de este enfoque:
* **Autenticación Desatendida**: La aplicación puede subir archivos de fondo (background tasks) sin intervención humana.
* **Seguridad Acotada**: La cuenta de servicio solo tiene acceso a las carpetas de Google Drive que tú compartas explícitamente con ella. No tiene acceso a todo tu Drive personal.
* **Estabilidad**: Las credenciales no expiran como los tokens de usuario (OAuth2 de tres patas), lo que evita que el sistema falle a mitad de un backup programado.

---

## 2. Paso a Paso para la Configuración

Sigue estos 8 pasos detallados para habilitar el servicio de respaldos en la nube.

### Paso 1: Crear un Proyecto en Google Cloud Console
1. Accede a [Google Cloud Console](https://console.cloud.google.com/).
2. Inicia sesión con una cuenta de Google (Gmail o Google Workspace).
3. En la barra superior, haz clic en el selector de proyectos y selecciona **"Proyecto nuevo"** (New Project).
4. Asigna un nombre descriptivo al proyecto (por ejemplo, `SGI-Salud-Backups`) y haz clic en **"Crear"**.
5. Espera unos segundos a que se cree el proyecto y selecciónalo en el menú desplegable superior.

---

### Paso 2: Habilitar la API de Google Drive
1. Con el proyecto seleccionado, abre el menú de navegación izquierdo (icono de tres líneas horizontales) e ingresa a **"API y servicios"** > **"Biblioteca"** (Library).
2. En la barra de búsqueda, escribe **"Google Drive API"**.
3. Selecciona el resultado **Google Drive API** y haz clic en el botón azul **"Habilitar"** (Enable).

---

### Paso 3: Crear la Cuenta de Servicio
1. Una vez habilitada la API, ve al menú izquierdo y navega a **"API y servicios"** > **"Credenciales"** (Credentials).
2. Haz clic en el botón superior **"+ Crear credenciales"** (+ Create credentials) y selecciona **"Cuenta de servicio"** (Service account).
3. Rellena los datos básicos:
   * **Nombre de la cuenta de servicio**: `sgi-salud-backup-operator` (o similar).
   * **ID de la cuenta de servicio**: Se generará automáticamente (un correo electrónico).
   * **Descripción**: `Operador automatizado de copias de seguridad de SGI Salud`.
4. Haz clic en **"Crear y continuar"** (Create and continue).
5. Los pasos opcionales de otorgar accesos y roles al proyecto los puedes omitir (haz clic en **"Continuar"** y luego en **"Listo"** / **"Done"**).

---

### Paso 4: Descargar la Clave Privada (JSON)
1. En la tabla de **Cuentas de servicio** de la pantalla de Credenciales, busca el correo de la cuenta que acabas de crear y haz clic sobre él (o presiona el lápiz de edición).
2. Ve a la pestaña superior **"Claves"** (Keys).
3. Haz clic en el botón desplegable **"Agregar clave"** > **"Crear clave nueva"** (Add key > Create new key).
4. Selecciona el tipo de clave **"JSON"** y haz clic en **"Crear"**.
5. Se descargará automáticamente a tu computadora un archivo con extensión `.json` (por ejemplo, `mi-proyecto-xxxxxx.json`).
6. **¡IMPORTANTE!** Este archivo contiene la clave privada de tu cuenta de servicio. Guárdalo de forma segura y nunca lo publiques en repositorios como GitHub.

---

### Paso 5: Colocar las Credenciales en SGI Salud
1. Busca el archivo `.json` que descargaste en el paso anterior.
2. Cámbiale el nombre exactamente a: **`google_credentials.json`**.
3. Copia el archivo y pégalo dentro de la carpeta **`database/`** de tu instalación de SGI Salud.
   * La ruta del archivo en el proyecto debe ser:
     `ProyectoComunitario/database/google_credentials.json`
4. El sistema detectará automáticamente el archivo y mostrará el indicador **"Credenciales: Cargadas"** en verde en la pantalla de Configuración.

---

### Paso 6: Crear y Compartir la Carpeta en Google Drive
1. Abre tu Google Drive personal o institucional de manera normal en el navegador.
2. Crea una nueva carpeta en la ubicación que prefieras (por ejemplo, llámala `Respaldos_SGI_Salud`).
3. Abre el archivo `google_credentials.json` con un editor de texto (como el Bloc de Notas) y busca el valor del campo `"client_email"`. Será una dirección de correo parecida a:
   `sgi-salud-backup-operator@nombre-proyecto.iam.gserviceaccount.com`
4. Haz clic derecho sobre tu carpeta de Google Drive recién creada y selecciona **"Compartir"** (Share).
5. Pega el correo de la cuenta de servicio obtenido de la clave JSON.
6. Asegúrate de asignarle el rol de **"Editor"** (es vital para que la app pueda escribir y subir archivos) y desmarca la opción de enviar notificación si lo prefieres.
7. Haz clic en **"Compartir"** / **"Enviar"**.

---

### Paso 7: Obtener el ID de la Carpeta de Drive
1. Haz doble clic en la carpeta compartida en tu Google Drive para entrar en ella.
2. Observa la barra de direcciones de tu navegador web. La URL tendrá un aspecto similar a este:
   `https://drive.google.com/drive/folders/1Xy_2Z-ABcdEFGhIjKlMnOpQrStUvWxYz`
3. El **ID de la carpeta** es la cadena de caracteres aleatorios que va después de `/folders/`. En el ejemplo anterior, sería:
   `1Xy_2Z-ABcdEFGhIjKlMnOpQrStUvWxYz`
4. Copia ese código.

---

### Paso 8: Configurar y Probar la Aplicación
1. Inicia la aplicación **SGI Salud**.
2. Ve al módulo de **Configuración** (icono de engranaje ⚙️) en el panel izquierdo.
3. Desplázate hasta la sección **"💾 Copias de Seguridad"**.
4. Activa la casilla **"Habilitar Respaldo en Google Drive"**.
5. Pega el ID de la carpeta copiado en el campo **"ID Carpeta Google Drive"**.
6. Haz clic en el botón **"Guardar Configuración"**.
7. Para probar que todo funciona, haz clic en el botón **"Subir Respaldo a Google Drive Ahora"**.
8. Si las credenciales y el ID son correctos, verás un mensaje de éxito y la base de datos aparecerá inmediatamente en tu carpeta de Google Drive.

---

## 3. Resolución de Problemas Comunes

### Error: `googleapiclient.errors.HttpError: <HttpError 404...>`
* **Causa**: El ID de la carpeta de Google Drive es incorrecto o la cuenta de servicio no tiene permisos en esa carpeta.
* **Solución**:
  1. Verifica que copiaste el ID completo sin espacios ni caracteres adicionales.
  2. Asegúrate de haber compartido la carpeta de Drive con el correo exacto de la cuenta de servicio (`client_email`) y que tenga permisos de **Editor**.

### Error: `Las dependencias de Google Drive no están instaladas`
* **Causa**: Falta instalar los paquetes de Google API en el entorno de Python.
* **Solución**: Abre tu terminal en la carpeta del proyecto con el entorno virtual activado y ejecuta:
  ```bash
  pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib
  ```

### Error: `No se encontró el archivo de credenciales`
* **Causa**: El archivo JSON no tiene el nombre correcto o no está en la carpeta adecuada.
* **Solución**: Asegúrate de que el archivo se llame exactamente `google_credentials.json` y esté dentro del subdirectorio `database/` de la carpeta principal de la aplicación.
