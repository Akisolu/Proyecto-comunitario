# Sistema de Fichas Médicas / Medical Records System

**What it does:** A desktop app that replaces paper patient records at a local clinic with secure, searchable digital records that stay intact if the power goes out while data is being read or written.
**Why it matters:** Paper files were lost, damaged and filled in incorrectly, causing errors and delays in patient care.  

**Qué hace:** Una aplicación de escritorio que reemplaza las fichas de papel de una clínica local por registros digitales seguros y fáciles de consultar, protegidos contra daños si se corta la luz mientras se leen o escriben datos.  
**Por qué importa:** Las fichas de papel se extraviaban, se deterioraban y se llenaban mal, lo que causaba errores y demoras en la atención.  
> 📄 Versión completa en español: [README.es.md](README.es.md)

## Overview

A desktop application for managing patient medical records in a local hospital in Turén, Venezuela. It digitises the whole workflow: registering, storing and consulting patient records from a computer, with data saved safely and persistently on the machine itself.

## The problem

Before the app, medical records were kept on paper. Files were misplaced or deteriorated over time, entries were filled in incorrectly by hand, and an unexpected power cut could interrupt work and put information at risk. Staff had no reliable way to find or recover a patient's history quickly.

## The solution

A Python desktop app with a Tkinter interface and a SQLite database. Records are validated with Pydantic before being saved, so incomplete or malformed data is rejected. The app handles unexpected errors gracefully and keeps information on disk, so it can resume normal work after a restart or a power outage.

## Features

- Patient record registration, storage and consultation from a desktop window.
- Strict validation of data through Pydantic models.
- Persistent and secure local storage with SQLite.
- Resilient behaviour against unexpected errors and power cuts.
- Automated test suite covering 88% of the code.
- Deployed and used at a local hospital in Turén.

## Tech stack

- Python 3.12
- Tkinter (desktop interface)
- SQLite (persistent storage)
- Pydantic (data validation)
- Pytest (automated tests)

## Tests and quality

The project includes an automated test suite. Coverage reached 88%, and the suite was expanded in September 2026 to cover failure scenarios and unexpected errors.

## Getting started

1. Install Python 3.12.10. If you do not have it, install it with `py install 3.12`.
2. Check the installation with `py -3.12 --version`.
3. Create a virtual environment with `py -3.12 -m venv .venv`.
4. Activate it with `.venv\Scripts\activate`.
5. Install dependencies with `pip install -r requirements.txt`.
6. Verify with `pip list`.

## Building the executable

1. Check whether PyInstaller is installed with `pip freeze`.
2. If it is installed, run:

```bash
pyinstaller --noconfirm --onedir --windowed --paths=src --add-data "database;database" main.py
```

3. Open the `dist` folder to find the executable.

## Credits

Developed as a community project for a local hospital in Turén. Development, documentation, automated testing and deployment by [Akisolu](https://github.com/Akisolu).
