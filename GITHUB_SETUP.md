# Configuración del Repositorio en GitHub

Este documento proporciona los pasos para crear un repositorio en GitHub y subir este proyecto.

## 1. Crear un Repositorio en GitHub

1. Abre tu navegador y accede a [GitHub](https://github.com).
2. Inicia sesión con tu cuenta.
3. Haz clic en el botón "+" en la esquina superior derecha y selecciona "Nuevo repositorio".
4. Completa la información del repositorio:
   - **Nombre del repositorio**: `PoyectoCorte_II_Primera_parte`
   - **Descripción**: Sistema de Control de LEDs mediante UART y Web Serial API
   - **Visibilidad**: Puedes elegir público o privado según tus preferencias
   - **Inicializar con README**: No (ya tenemos nuestro propio README)
   - **Agregar .gitignore**: Selecciona "C++" de la lista desplegable
   - **Licencia**: Opcional, puedes elegir la que prefieras

5. Haz clic en "Crear repositorio".

## 2. Preparar tu Proyecto Local para GitHub

Abre una terminal (Git Bash, CMD o PowerShell) y navega hasta el directorio de tu proyecto:

```bash
cd "c:\Users\julia\OneDrive\Escritorio\U.MILITAR\Semestre V - 2025\Micros\Teo\PoyectoCorte_II_Primera_parte"
```

Inicializa el repositorio Git localmente:

```bash
git init
```

## 3. Crear un archivo .gitignore

Agrega un archivo .gitignore para evitar subir archivos innecesarios:

```bash
echo "# Archivos compilados
*.o
*.obj
*.exe
*.out
*.app

# Archivos temporales
*.tmp
*.log
*.bak

# Archivos específicos de STM32CubeIDE
.settings/
.project
.cproject
Debug/
Release/

# Archivos específicos del sistema
.DS_Store
Thumbs.db
desktop.ini
" > .gitignore
```

## 4. Añadir y Hacer Commit de los Archivos del Proyecto

Agrega los archivos del proyecto al repositorio:

```bash
git add .
```

Realiza el primer commit:

```bash
git commit -m "Versión inicial: Sistema de control de LEDs con UART y Web Serial API"
```

## 5. Conectar y Subir a GitHub

Conecta tu repositorio local con el repositorio remoto en GitHub:

```bash
git remote add origin https://github.com/TU_USUARIO/PoyectoCorte_II_Primera_parte.git
```

Reemplaza `TU_USUARIO` con tu nombre de usuario de GitHub.

Sube el proyecto al repositorio remoto:

```bash
git push -u origin master
```

Si estás usando una rama principal llamada "main" (más común en repositorios nuevos) en lugar de "master", usa este comando:

```bash
git push -u origin main
```

## 6. Estructura de Archivos del Repositorio

Tu repositorio tendrá la siguiente estructura:

```
PoyectoCorte_II_Primera_parte/
├── Back-end/
│   ├── USART_LED.C++     (Código del microcontrolador)
│   └── README            (Explicación detallada del proyecto)
├── index.html            (Interfaz de usuario web)
├── script.js             (Lógica de comunicación web serial)
├── README.md             (Documentación principal, puedes crear uno basado en el README existente)
└── GITHUB_SETUP.md       (Este documento con instrucciones de GitHub)
```

## 7. Verificar la Carga

1. Accede a tu repositorio de GitHub en `https://github.com/TU_USUARIO/PoyectoCorte_II_Primera_parte`
2. Verifica que todos los archivos se hayan cargado correctamente.
3. Puedes editar el README principal para mejorar la presentación del proyecto en GitHub.

## 8. Configuración Adicional (Opcional)

- **GitHub Pages**: Si quieres crear una demostración interactiva, puedes activar GitHub Pages
  1. Ve a "Settings" > "Pages"
  2. Selecciona la rama "main" o "master" y guarda
  3. Después de unos minutos, tu aplicación estará disponible en `https://TU_USUARIO.github.io/PoyectoCorte_II_Primera_parte/`

- **Colaboradores**: Si trabajas en equipo, puedes añadir colaboradores en "Settings" > "Collaborators"

## Solución de Problemas Comunes

- Si te encuentras con errores al hacer push, asegúrate de que:
  - Tienes los permisos adecuados en el repositorio
  - Tu credencial de Git está configurada correctamente
  - No hay conflictos entre el repositorio local y remoto

- Para problemas de autenticación, considera usar el token de acceso personal:
  1. En GitHub: "Settings" > "Developer settings" > "Personal access tokens" > "Tokens (classic)" > "Generate new token"
  2. Usa ese token como contraseña al hacer push
