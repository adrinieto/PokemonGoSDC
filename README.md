PokemonGoSDC
============

Ya no funciona. Proyecto abandonado.

---

PokemonGOSDC consistía en un bot para Telegram al que le podías consultar datos relativos a Santiago de Compostelalos: gimnasios,
que gimnasios controlaban los entrenadores y qué pokemon tenían en él.

También había una web en pruebas en la que podías ver el estado de los gimnasios en un mapa con notificaciones de los cambios en tiempo real. 

# Instalación

1. Instala las dependencias con `pip install -r requirements.txt`
2. Añade los datos de la cuenta para escanear en `config.py`
3. Ejecutar con `python gyms_scanner.py`

## Bot para Telegram

 Si quieres utilizar un Bot de Telegram debes añadir la API key en `config.py`.
 Los comandos del bot se especifican en `bot_commands.txt`.

 Para lanzar el bot ejecuta `python bot.py`.

Puedes añadir un fichero `cheaters.txt` con un nombre por línea para filtrar y marcar
 a los jugadores que hacen trampas.