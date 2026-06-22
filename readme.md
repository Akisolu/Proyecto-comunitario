INSTRUCCIONES PARA INICIAR EL PROYECTO

1- Se necesita python 3.12.10
2- Si no se tiene usar "py install 3.12"
3- Comprobar si funciono con "py -3.12 --version"
4- Iniciar el entorno virtual con "py -3.12 -m venv .venv"
5- Activar el entorno con ".venv\Scripts\activate"
6- Instalar las dependencias con "pip install -r requirements.txt"
7- Comprobar con "pip list"

INSTRUCCIONES PARA CONSTRUIR EL EJECUTABLE

1- Verificar si tienes instalado Pyinstaller, puedes usar pip freeze para esto
2- Si esta instalado ejecuta 
pyinstaller --noconfirm --onedir --windowed --paths=src --add-data "database;database" main.py
3- Acceder a la carpeta dist y veras el ejecutable