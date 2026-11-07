# Pacman 

Trabajo Final Integrador - Metodología de la Programación (UADER FCyT, Ingeniería en Telecomunicaciones, 2026)

## Integrantes
- Juan Ignacio Orcellet
- Tadeo rojkis
- Mateo Lascano  

## Descripción
Juego Pacman en Python con programación orientada a objetos e interfaz gráfica en Tkinter.
Pacman se controla con las flechas, tres fantasmas se mueven de forma autónoma y el puntaje
de cada partida se guarda automáticamente en `puntuaciones.json` (se muestra el Top 5).

- `modelo.py`: lógica del juego (`Laberinto`, `Entidad`, `Pacman`, `Fantasma`, `TableroJuego`).
- `persistencia.py`: `GestorPuntuaciones` (historial en JSON, con id único por registro).
- `main.py`: interfaz gráfica Tkinter.
- `diagrama` 

1. Ingresá tu nombre al iniciar.
2. Movete con las flechas, comé todos los puntos y evitá a los fantasmas (3 vidas).
3. `R` o el botón "Reiniciar" inicia una partida limpia para un nuevo jugador en cualquier momento.
4. El puntaje se guarda al terminar la partida (victoria o Game Over).
