"""main.py - Interfaz gráfica (Tkinter). Solo dibuja y captura teclas; la lógica está en modelo.py."""
import os
import tkinter as tk
from tkinter import messagebox, ttk

from modelo import (TableroJuego, Laberinto, DIFICULTADES, DIFICULTAD_POR_DEFECTO,
                    ARRIBA, ABAJO, IZQUIERDA, DERECHA, QUIETO)
from persistencia import GestorPuntuaciones

TAM = 30          # píxeles por celda
COLOR_FONDO = "black"
COLOR_PARED = "#1a3cff"
COLOR_MENU_BG = "#0b0b1e"
# El archivo se guarda junto a main.py, sin importar desde dónde se ejecute
RUTA_PUNTUACIONES = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                 "puntuaciones.json")

AYUDA = (
    "CONTROLES\n"
    "  Flechas: mover a Pacman\n"
    "  P o Espacio: pausa\n"
    "  R: reiniciar la partida\n"
    "  Esc: volver al menú\n\n"
    "OBJETIVO\n"
    "  Comé todos los puntos (10 pts) y evitá a los fantasmas.\n"
    "  Las bolitas grandes (50 pts) asustan a los fantasmas:\n"
    "  mientras están azules podés comerlos (200, 400, 800...).\n"
    "  Si te toca un fantasma normal perdés una vida.\n\n"
    "El puntaje se guarda al terminar (victoria o Game Over)."
)


class AplicacionPacman:
    def __init__(self, raiz):
        self._raiz = raiz
        self._raiz.title("Pacman POO - UADER FCyT")
        self._raiz.resizable(False, False)
        self._gestor = GestorPuntuaciones(RUTA_PUNTUACIONES)
        self._tablero = None
        self._dificultad = DIFICULTAD_POR_DEFECTO
        self._nombre = ""
        self._puntaje_guardado = False
        self._tarea = None
        self._tic = 0
        self._mirada = DERECHA
        self._en_juego = False
        self._pausado = False

        self._var_nombre = tk.StringVar()
        self._var_dif = tk.StringVar(value=DIFICULTAD_POR_DEFECTO.nombre)

        self._frame_menu = tk.Frame(self._raiz, bg=COLOR_MENU_BG)
        self._frame_juego = tk.Frame(self._raiz)
        self._construir_menu()
        self._construir_juego()

        self._raiz.protocol("WM_DELETE_WINDOW", self._cerrar)
        self._raiz.bind("<Up>", lambda e: self._girar(ARRIBA))
        self._raiz.bind("<Down>", lambda e: self._girar(ABAJO))
        self._raiz.bind("<Left>", lambda e: self._girar(IZQUIERDA))
        self._raiz.bind("<Right>", lambda e: self._girar(DERECHA))
        for tecla in ("<r>", "<R>"):
            self._raiz.bind(tecla, lambda e: self._atajo_reiniciar())
        for tecla in ("<p>", "<P>", "<space>"):
            self._raiz.bind(tecla, lambda e: self._atajo_pausa())
        self._raiz.bind("<Escape>", lambda e: self._atajo_menu())
        self._raiz.bind("<Return>", lambda e: self._atajo_jugar())

        self._mostrar_menu()

    # ---------- menú principal ----------
    def _construir_menu(self):
        f = self._frame_menu
        f.configure(padx=60, pady=30)
        tk.Label(f, text="PACMAN", font=("Arial", 36, "bold"),
                 fg="#ffd800", bg=COLOR_MENU_BG).pack()
        tk.Label(f, text="Metodología de la Programación - UADER FCyT",
                 font=("Arial", 9), fg="#8888aa", bg=COLOR_MENU_BG).pack(pady=(0, 20))

        tk.Label(f, text="Nombre del jugador", font=("Arial", 11, "bold"),
                 fg="white", bg=COLOR_MENU_BG).pack(anchor="w")
        self._entrada = tk.Entry(f, textvariable=self._var_nombre, font=("Arial", 14),
                                 justify="center")
        self._entrada.pack(fill="x", pady=(2, 15))

        tk.Label(f, text="Dificultad", font=("Arial", 11, "bold"),
                 fg="white", bg=COLOR_MENU_BG).pack(anchor="w")
        for d in DIFICULTADES:
            tk.Radiobutton(f, text=d.nombre, value=d.nombre, variable=self._var_dif,
                           font=("Arial", 12), fg="white", bg=COLOR_MENU_BG,
                           selectcolor=COLOR_MENU_BG, activebackground=COLOR_MENU_BG,
                           activeforeground="#ffd800", anchor="w").pack(fill="x")
        self._lbl_detalle = tk.Label(f, text="", font=("Arial", 9), fg="#aab",
                                     bg=COLOR_MENU_BG)
        self._lbl_detalle.pack(pady=(4, 15))
        self._var_dif.trace_add("write", lambda *a: self._actualizar_detalle())
        self._actualizar_detalle()

        tk.Button(f, text="JUGAR", font=("Arial", 14, "bold"),
                  command=self._jugar).pack(fill="x", pady=3)
        tk.Button(f, text="Ranking", command=self._mostrar_ranking).pack(fill="x", pady=3)
        tk.Button(f, text="Cómo jugar", command=self._mostrar_ayuda).pack(fill="x", pady=3)
        tk.Button(f, text="Salir", command=self._cerrar).pack(fill="x", pady=3)

    def _dificultad_elegida(self):
        nombre = self._var_dif.get()
        return next(d for d in DIFICULTADES if d.nombre == nombre)

    def _actualizar_detalle(self):
        d = self._dificultad_elegida()
        self._lbl_detalle.config(
            text=f"{d.vidas} vidas · poder de {d.segundos_poder:.0f} s · velocidad {d.velocidad}")

    def _mostrar_menu(self):
        self._cancelar_tick()
        self._en_juego = False
        self._pausado = False
        self._frame_juego.pack_forget()
        self._frame_menu.pack()
        self._entrada.focus_set()

    def _mostrar_ayuda(self):
        messagebox.showinfo("Cómo jugar", AYUDA, parent=self._raiz)

    def _mostrar_ranking(self):
        ventana = tk.Toplevel(self._raiz)
        ventana.title("Ranking - Top 10")
        ventana.resizable(False, False)
        ventana.transient(self._raiz)
        opciones = ["Todas"] + [d.nombre for d in DIFICULTADES]
        combo = ttk.Combobox(ventana, values=opciones, state="readonly", width=12)
        combo.set(self._var_dif.get())
        combo.pack(padx=15, pady=(15, 5))
        texto = tk.Label(ventana, text="", justify="left", font=("Courier", 11))
        texto.pack(padx=15, pady=10)

        def refrescar(*_):
            filtro = None if combo.get() == "Todas" else combo.get()
            top = self._gestor.obtener_mejores_puntuaciones(10, filtro)
            if not top:
                texto.config(text="(sin registros)")
                return
            texto.config(text="\n".join(
                f"{i:>2}. {r['nombre'][:12]:<12} {r['puntaje']:>5}  {r.get('dificultad', '-')}"
                for i, r in enumerate(top, 1)))

        combo.bind("<<ComboboxSelected>>", refrescar)
        refrescar()
        tk.Button(ventana, text="Cerrar", command=ventana.destroy).pack(pady=(0, 15))

    def _jugar(self):
        nombre = self._var_nombre.get().strip()
        if not nombre:
            messagebox.showwarning("Falta el nombre", "Ingresá tu nombre para jugar.",
                                   parent=self._raiz)
            self._entrada.focus_set()
            return
        self._nombre = nombre[:20]
        self._dificultad = self._dificultad_elegida()
        self._frame_menu.pack_forget()
        self._frame_juego.pack()
        self._en_juego = True
        self._lbl_jugador.config(text=f"Jugador: {self._nombre}")
        self._lbl_dif.config(text=f"Dificultad: {self._dificultad.nombre}")
        self._nueva_partida()

    # ---------- pantalla de juego ----------
    def _construir_juego(self):
        lab = Laberinto()
        ancho, alto = lab.ancho * TAM, lab.alto * TAM
        f = self._frame_juego

        self._canvas = tk.Canvas(f, width=ancho, height=alto,
                                 bg=COLOR_FONDO, highlightthickness=0)
        self._canvas.grid(row=0, column=0, padx=10, pady=10)

        panel = tk.Frame(f)
        panel.grid(row=0, column=1, sticky="n", padx=10, pady=10)
        self._lbl_jugador = tk.Label(panel, text="Jugador: -", font=("Arial", 12, "bold"))
        self._lbl_dif = tk.Label(panel, text="Dificultad: -", font=("Arial", 11))
        self._lbl_puntaje = tk.Label(panel, text="Puntaje: 0", font=("Arial", 12))
        self._lbl_vidas = tk.Label(panel, text="Vidas: -", font=("Arial", 12))
        for lbl in (self._lbl_jugador, self._lbl_dif, self._lbl_puntaje, self._lbl_vidas):
            lbl.pack(anchor="w")
        tk.Button(panel, text="Pausa (P)", command=self._atajo_pausa).pack(pady=(10, 0), fill="x")
        tk.Button(panel, text="Reiniciar (R)", command=self._atajo_reiniciar).pack(pady=3, fill="x")
        tk.Button(panel, text="Menú (Esc)", command=self._atajo_menu).pack(pady=3, fill="x")
        self._lbl_titulo_rank = tk.Label(panel, text="TOP 5", font=("Arial", 12, "bold"))
        self._lbl_titulo_rank.pack(anchor="w", pady=(10, 0))
        self._lbl_ranking = tk.Label(panel, text="", justify="left", font=("Courier", 10))
        self._lbl_ranking.pack(anchor="w")

    # ---------- control de la partida ----------
    def _atajo_jugar(self):
        if not self._en_juego:
            self._jugar()

    def _atajo_reiniciar(self):
        if self._en_juego:
            self._nueva_partida()

    def _atajo_menu(self):
        if self._en_juego:
            self._guardar_partida()
            self._mostrar_menu()

    def _cerrar(self):
        if self._en_juego:
            self._guardar_partida()
        self._raiz.destroy()

    def _guardar_partida(self):
        """Guarda el puntaje de la partida actual (terminada o abandonada con puntos)."""
        t = self._tablero
        if t is None or self._puntaje_guardado:
            return
        if not (t.juego_terminado or t.puntaje > 0):
            return
        try:
            self._gestor.guardar_puntuacion(self._nombre, t.puntaje, self._dificultad.nombre)
        except OSError as e:
            messagebox.showerror(
                "No se pudo guardar",
                f"No se pudo escribir el archivo:\n{self._gestor.nombre_archivo}\n\n{e}",
                parent=self._raiz)
            return
        self._puntaje_guardado = True
        self._actualizar_ranking()

    def _atajo_pausa(self):
        if not self._en_juego or self._tablero is None or self._tablero.juego_terminado:
            return
        if self._pausado:
            self._pausado = False
            self._programar_tick()
        else:
            self._pausado = True
            self._cancelar_tick()
        self._dibujar()

    def _nueva_partida(self):
        """Reinicio limpio con el mismo jugador y la misma dificultad."""
        self._guardar_partida()   # si había una partida en curso, se guarda antes
        self._cancelar_tick()
        self._tablero = TableroJuego(dificultad=self._dificultad)
        self._puntaje_guardado = False
        self._pausado = False
        self._mirada = DERECHA
        self._actualizar_ranking()
        self._dibujar()
        self._programar_tick()

    def _girar(self, direccion):
        if self._en_juego and not self._pausado and not self._tablero.juego_terminado:
            self._tablero.pacman.solicitar_direccion(direccion)

    def _cancelar_tick(self):
        if self._tarea is not None:
            self._raiz.after_cancel(self._tarea)
            self._tarea = None

    def _programar_tick(self):
        self._tarea = self._raiz.after(self._dificultad.tick_ms, self._tick)

    def _tick(self):
        self._tic += 1
        self._tablero.actualizar_ciclo()
        if self._tablero.pacman.direccion != QUIETO:
            self._mirada = self._tablero.pacman.direccion
        if self._tablero.juego_terminado:
            self._guardar_partida()
        self._dibujar()
        if not self._tablero.juego_terminado:
            self._programar_tick()
        else:
            self._tarea = None

    def _actualizar_ranking(self):
        self._lbl_titulo_rank.config(text=f"TOP 5 ({self._dificultad.nombre})")
        top = self._gestor.obtener_mejores_puntuaciones(5, self._dificultad.nombre)
        if not top:
            self._lbl_ranking.config(text="(sin registros)")
            return
        lineas = [f"{i}. {r['nombre'][:12]:<12} {r['puntaje']:>5}"
                  for i, r in enumerate(top, 1)]
        self._lbl_ranking.config(text="\n".join(lineas))

    # ---------- dibujo ----------
    def _dibujar(self):
        c = self._canvas
        c.delete("all")
        t = self._tablero
        lab = t.laberinto

        for y in range(lab.alto):
            for x in range(lab.ancho):
                x0, y0 = x * TAM, y * TAM
                if lab.es_pared(x, y):
                    c.create_rectangle(x0 + 1, y0 + 1, x0 + TAM - 1, y0 + TAM - 1,
                                       fill=COLOR_PARED, outline="")
                elif lab.hay_pildora(x, y):
                    m = TAM // 2
                    r = 7 if self._tic % 2 == 0 else 6   # late suavemente
                    c.create_oval(x0 + m - r, y0 + m - r, x0 + m + r, y0 + m + r,
                                  fill="#ffd9a0", outline="")
                elif lab.hay_punto(x, y):
                    m = TAM // 2
                    c.create_oval(x0 + m - 3, y0 + m - 3, x0 + m + 3, y0 + m + 3,
                                  fill="#ffd9a0", outline="")

        for f in t.fantasmas:
            self._dibujar_fantasma(f)
        self._dibujar_pacman(t.pacman)

        self._lbl_puntaje.config(text=f"Puntaje: {t.puntaje}")
        self._lbl_vidas.config(text="Vidas: " + "♥ " * t.pacman.vidas)

        cx, cy = lab.ancho * TAM // 2, lab.alto * TAM // 2
        if t.juego_terminado:
            texto = "¡VICTORIA!" if t.victoria else "GAME OVER"
            color = "lime" if t.victoria else "red"
            c.create_rectangle(cx - 150, cy - 45, cx + 150, cy + 45, fill="black", outline=color)
            c.create_text(cx, cy - 12, text=texto, fill=color, font=("Arial", 22, "bold"))
            c.create_text(cx, cy + 20, text="R: reiniciar  ·  Esc: menú", fill="white",
                          font=("Arial", 10))
        elif self._pausado:
            c.create_rectangle(cx - 110, cy - 35, cx + 110, cy + 35, fill="black", outline="white")
            c.create_text(cx, cy - 8, text="PAUSA", fill="white", font=("Arial", 20, "bold"))
            c.create_text(cx, cy + 18, text="P o Espacio para seguir", fill="white",
                          font=("Arial", 9))

    def _dibujar_pacman(self, p):
        x0, y0 = p.pos_x * TAM + 2, p.pos_y * TAM + 2
        angulos = {DERECHA: 0, ARRIBA: 90, IZQUIERDA: 180, ABAJO: 270}
        base = angulos[self._mirada]
        boca = 30 if self._tic % 2 == 0 else 5
        self._canvas.create_arc(x0, y0, x0 + TAM - 4, y0 + TAM - 4,
                                start=base + boca, extent=360 - 2 * boca,
                                fill=p.color, outline="")

    def _dibujar_fantasma(self, f):
        x0, y0 = f.pos_x * TAM + 3, f.pos_y * TAM + 3
        w = TAM - 6
        c = self._canvas
        color = f.color
        if f.esta_asustado:
            color = "white" if (f.por_terminar and self._tic % 2 == 0) else "#4d6bff"
        c.create_oval(x0, y0, x0 + w, y0 + w, fill=color, outline="")
        c.create_rectangle(x0, y0 + w // 2, x0 + w, y0 + w, fill=color, outline="")
        for ox in (w // 4, 3 * w // 4):
            c.create_oval(x0 + ox - 3, y0 + w // 3 - 3, x0 + ox + 3, y0 + w // 3 + 3,
                          fill="white", outline="")


def main():
    raiz = tk.Tk()
    AplicacionPacman(raiz)
    raiz.mainloop()


if __name__ == "__main__":
    main()
