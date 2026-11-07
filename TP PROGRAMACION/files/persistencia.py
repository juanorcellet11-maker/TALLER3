"""persistencia.py - Guardado y lectura del historial de puntuaciones (JSON)."""
import json
import os
from datetime import datetime


class GestorPuntuaciones:
    def __init__(self, nombre_archivo="puntuaciones.json"):
        self._nombre_archivo = nombre_archivo

    @property
    def nombre_archivo(self):
        return self._nombre_archivo

    def _leer_todo(self):
        if not os.path.exists(self._nombre_archivo):
            return []
        try:
            with open(self._nombre_archivo, "r", encoding="utf-8") as f:
                datos = json.load(f)
            return datos if isinstance(datos, list) else []
        except (json.JSONDecodeError, OSError):
            return []

    def guardar_puntuacion(self, nombre, puntaje, dificultad=None):
        """Agrega un registro nuevo con id único (autoincremental). Devuelve el registro."""
        historial = self._leer_todo()
        siguiente_id = max((r.get("id", 0) for r in historial), default=0) + 1
        registro = {
            "id": siguiente_id,
            "nombre": nombre,
            "puntaje": puntaje,
            "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        if dificultad is not None:
            registro["dificultad"] = dificultad
        historial.append(registro)
        with open(self._nombre_archivo, "w", encoding="utf-8") as f:
            json.dump(historial, f, ensure_ascii=False, indent=2)
        return registro

    def obtener_mejores_puntuaciones(self, cantidad=5, dificultad=None):
        """Top N ordenado por puntaje descendente (desempata el registro más antiguo).
        Si se indica `dificultad`, solo cuenta los registros de esa dificultad."""
        historial = self._leer_todo()
        if dificultad is not None:
            historial = [r for r in historial if r.get("dificultad") == dificultad]
        historial.sort(key=lambda r: (-r.get("puntaje", 0), r.get("id", 0)))
        return historial[:cantidad]
