# ☁️ Guía 11: Configuración del Respaldo en Google Drive — SGI Salud

Esta guía detalla paso a paso cómo configurar la API de Google Drive para permitir el respaldo en la nube del sistema **SGI Salud**, cubriendo tanto las cuentas personales de Gmail (vía OAuth 2.0) como las cuentas institucionales/corporativas (vía Cuenta de Servicio).

---

## 1. Métodos de Autenticación Disponibles

El sistema cuenta con un backend híbrido que detecta automáticamente el tipo de credenciales que proporciones en el archivo `google_credentials.json`:

### Método A: Cliente OAuth 2.0 de Escritorio (Recomendado para cuentas `@gmail.com` personales)
* **Por qué es necesario**: Las cuentas de servicio no tienen cuota de almacenamiento propia (0 bytes). Si intentas usarlas en una cuenta `@gmail.com` personal, Google rechazará la subida por falta de espacio (`storageQuotaExceeded`).
* **Cómo funciona**: La primera vez que realizas un respaldo, el sistema abre tu navegador para que inicies sesión y autorices la aplicación. Una vez hecho esto, guarda un token persistente local (`google_token.json`) para realizar las siguientes copias de fondo de manera **100% silenciosa y automática**.

### Método B: Cuenta de Servicio (Service Account) (Recomendado para Google Workspace / Empresas)
* **Cómo funciona**: Autentica de forma desatendida desde el primer momento.
* **Requisito**: Es obligatorio subir los archivos a una **Unidad Compartida (Shared Drive)** de Google Workspace donde la cuenta de servicio haya sido añadida como colaboradora, ya que las unidades compartidas no consumen cuota individual.

---

## 2. Paso a Paso para la Configuración (Método A: OAuth 2.0 Personal)

Sigue estos pasos detallados para configurar tu cuenta personal de Gmail:

### Paso 1: Crear un Proyecto en Google Cloud
1. Entra a [Google Cloud Console](https://console.cloud.google.com/).
2. Inicia sesión con la cuenta de Google donde guardarás los respaldos.
3. En la barra superior, haz clic en el selector de proyectos y presiona **"Proyecto nuevo"** (New Project).
4. Asigna un nombre (ej. `SGI-Salud-Backups`) y haz clic en **"Crear"**.
5. Selecciónalo en el menú desplegable superior una vez creado.

### Paso 2: Habilitar la API de Google Drive
1. En el menú de navegación izquierdo (icono de tres líneas), ve a **APIs y servicios** > **Biblioteca** (APIs & Services > Library).
2. Busca `Google Drive API`.
3. Haz clic sobre ella y presiona el botón azul **"Habilitar"** (Enable).

### Paso 3: Configurar la Pantalla de Consentimiento (OAuth Consent Screen)
1. En el menú izquierdo, ve a **APIs y servicios** > **Pantalla de consentimiento de OAuth** (OAuth consent screen).
2. Selecciona **External** (Externo) y haz clic en **Crear**.
3. Rellena los datos obligatorios:
   * **Nombre de la aplicación**: `sgi-salud-backup`
   * **Correo de soporte del usuario**: Tu propio correo electrónico.
   * **Información de contacto del desarrollador**: Tu propio correo electrónico.
4. Haz clic en **Guardar y continuar**. No necesitas añadir alcances (scopes), así que en la pantalla de "Alcances" haz clic en **Guardar y continuar**.

### Paso 4: AGREGAR USUARIOS DE PRUEBA (¡CRÍTICO!)
Como tu aplicación de Google Cloud estará en estado de "Pruebas" (Testing) y no verificada por Google, por seguridad Google bloqueará cualquier inicio de sesión excepto de los usuarios aprobados.
1. En la misma configuración de la pantalla de consentimiento, desplázate hasta la sección **"Usuarios de prueba"** (Test users).
2. Haz clic en el botón **"+ ADD USERS"** (o "+ AGREGAR USUARIOS").
3. Escribe tu correo de Gmail exacto (ej. `tu-correo@gmail.com`).
4. Haz clic en **Guardar** / **Save** y luego en **Guardar y continuar** para finalizar.

### Paso 5: Generar y Descargar las Credenciales
1. Ve al menú izquierdo y selecciona **APIs y servicios** > **Credenciales** (Credentials).
2. En la barra superior, haz clic en **"+ Crear credenciales"** (+ Create credentials) y selecciona **"ID de cliente de OAuth"** (OAuth client ID).
3. En "Tipo de aplicación", selecciona **"Aplicación de escritorio"** (Desktop app).
4. Asigna un nombre descriptivo y haz clic en **"Crear"**.
5. Se abrirá un cuadro emergente. Haz clic en **"Descargar JSON"** para descargar el archivo de credenciales a tu ordenador.

### Paso 6: Ubicar el Archivo en SGI Salud
1. Busca el archivo `.json` que descargaste en el paso anterior.
2. Cámbiale el nombre exactamente a: **`google_credentials.json`**.
3. Pégalo dentro de la carpeta **`database/`** de SGI Salud.
   * La ruta del archivo debe ser: `ProyectoComunitario/database/google_credentials.json`
4. El sistema detectará automáticamente el archivo y el indicador pasará a verde: **`google_credentials.json detectado`**.

### Paso 7: Configurar el ID de la Carpeta de Google Drive (Sigue siendo necesario)
El campo de **ID de carpeta** es fundamental para que la aplicación sepa exactamente en qué subcarpeta de tu nube debe alojar los archivos de base de datos.
1. Abre tu Google Drive personal en el navegador.
2. Crea una carpeta (ej. `Copias_SGI_Salud`).
3. Entra en la carpeta y copia el código alfanumérico que aparece al final de la URL en la barra de navegación (después de `/folders/`):
   * URL: `https://drive.google.com/drive/folders/1A2B3C4D5E6F7G8H9I0J...`
   * ID a copiar: `1A2B3C4D5E6F7G8H9I0J...`
4. Inicia **SGI Salud**, ve a **Configuración** ⚙️ y en la sección de Copias de Seguridad, activa **Google Drive** y pega el ID en el campo **ID Carpeta Drive**.
5. Haz clic en **Guardar Configuración**.

### Paso 8: Autorizar la Aplicación por única vez
1. Haz clic en el botón **"Subir Respaldo a Google Drive Ahora"**.
2. Se abrirá automáticamente una pestaña en tu navegador web.
3. Selecciona tu cuenta de Google (debe ser la misma que agregaste como usuario de prueba en el **Paso 4**).
4. Si te aparece un aviso indicando que *"Google no ha verificado esta aplicación"*, haz clic en **Configuración avanzada** y luego en **Ir a sgi-salud-backup (no seguro)**.
5. Concede los permisos de escritura en Google Drive y haz clic en **Continuar**.
6. El navegador te mostrará el mensaje *"¡Autorización exitosa! Ya puedes cerrar esta ventana y regresar a la aplicación"*.
7. En SGI Salud se creará el archivo en la nube, y localmente se guardará **`database/google_token.json`**. A partir de este momento, todos los backups programados y al cerrar la app se ejecutarán en segundo plano sin pedir interacciones ni abrir el navegador.

---

## 3. Resolución de Problemas Comunes

### Error: `Acceso bloqueado: sgi-salud-backup no ha completado el proceso de verificación de Google (Error 403: access_denied)`
* **Causa**: No agregaste tu correo como usuario de prueba en la consola de Google Cloud, o iniciaste sesión con un correo diferente.
* **Solución**: Vuelve al **Paso 4** de esta guía en Google Cloud Console, entra en "Pantalla de consentimiento de OAuth", ve a "Usuarios de prueba" y agrega el correo exacto con el que estás intentando iniciar sesión.

### Error: `Service Accounts do not have storage quota`
* **Causa**: Estás usando una cuenta de servicio de Google Cloud (Método B) para subir archivos a una carpeta personal (`@gmail.com`). Las cuentas personales no admiten que terceros (cuentas de servicio) consuman su espacio.
* **Solución**: Sigue el **Método A** (OAuth 2.0) detallado en esta guía. Borra el archivo `google_credentials.json` viejo y genera uno nuevo de tipo "Aplicación de Escritorio".

### Las dependencias de Google Drive no están instaladas
* **Causa**: Faltan los paquetes requeridos por el script en Python.
* **Solución**: Abre tu terminal en el entorno virtual de tu proyecto y ejecuta:
  ```bash
  pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib
  ```
