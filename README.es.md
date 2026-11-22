# Sistema de Fichas Médicas / Medical Records System

*🇺🇸 [Read this in English](README.md)*

> **Qué hace:** Una aplicación de escritorio que reemplaza las fichas de papel de una clínica local por registros digitales seguros y fáciles de consultar, que siguen funcionando incluso si se va la luz.
> **Por qué importa:** Las fichas de papel se extraviaban, se deterioraban y se llenaban mal, lo que causaba errores y demoras en la atención.
> **What it does:** A desktop app that replaces paper patient records at a local clinic with secure, searchable digital records that keep working during power outages.
> **Why it matters:** Paper files were lost, damaged and filled in incorrectly, causing errors and delays in patient care.
>
> 📄 Versión en inglés: [README.md](README.md)

## Descripción general

Aplicación de escritorio para la gestión de fichas médicas de un hospital local en Turén, Venezuela. Digitaliza todo el flujo de trabajo: registrar, almacenar y consultar las fichas de los pacientes desde una computadora, con la información guardada de forma segura y persistente en el propio equipo.

## El problema

Antes de la aplicación, las fichas se llevaban en papel. Se extraviaban o deterioraban con el tiempo, se llenaban incorrectamente a mano y un corte de luz inesperado podía interrumpir el trabajo y poner en riesgo la información. El personal no tenía una forma confiable de encontrar o recuperar rápidamente el historial de un paciente.

## La solución

Aplicación de Python con interfaz Tkinter y base de datos SQLite. Los datos se validan con Pydantic antes de guardarse, de modo que se rechazan los registros incompletos o mal formados. La aplicación maneja errores inesperados de forma controlada y mantiene la información en disco, por lo que puede reanudar su funcionamiento normal tras un reinicio o un corte de luz.

## Características

- Registro, almacenamiento y consulta de fichas médicas desde una ventana de escritorio.
- Validación estricta de datos mediante modelos Pydantic.
- Almacenamiento local persistente y seguro con SQLite.
- Comportamiento resiliente ante errores inesperados y cortes de luz.
- Suite de pruebas automatizadas con 88% de cobertura.
- Desplegada y en uso en un hospital local de Turén.

## Tecnologías utilizadas

- Python 3.12
- Tkinter (interfaz de escritorio)
- SQLite (almacenamiento persistente)
- Pydantic (validación de datos)
- Pytest (pruebas automatizadas)

## Pruebas y calidad

El proyecto cuenta con una suite de pruebas automatizadas. La cobertura alcanzó 88% y la batería de pruebas se amplió en septiembre de 2026 para cubrir escenarios de fallo y errores inesperados.

## Instrucciones para iniciar el proyecto

1. Se necesita Python 3.12.10. Si no se tiene, usar `py install 3.12`.
2. Comprobar si funcionó con `py -3.12 --version`.
3. Iniciar el entorno virtual con `py -3.12 -m venv .venv`.
4. Activar el entorno con `.venv\Scripts\activate`.
5. Instalar las dependencias con `pip install -r requirements.txt`.
6. Comprobar con `pip list`.

## Instrucciones para construir el ejecutable

1. Verificar si está instalado PyInstaller, con `pip freeze`.
2. Si está instalado, ejecutar:

```bash
pyinstaller --noconfirm --onedir --windowed --paths=src --add-data "database;database" main.py
```

3. Acceder a la carpeta `dist` para encontrar el ejecutable.

## Créditos

Desarrollado como proyecto comunitario para un hospital local de Turén. Desarrollo, documentación, pruebas automatizadas y despliegue por [Akisolu](https://github.com/Akisolu).
