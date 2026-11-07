"""
modelo.py - Lógica de negocio del juego Pacman (sin ninguna dependencia de la GUI).

Clases:
    Laberinto      -> grilla del mapa (paredes, puntos, posiciones iniciales)
    Entidad (ABC)  -> clase base abstracta de todo lo que se mueve
    Pacman         -> subclase de Entidad (controlada por el jugador)
    Fantasma       -> subclase de Entidad (movimiento autónomo)
    TableroJuego   -> orquesta el ciclo de juego, colisiones, puntaje y vidas
"""
from abc import ABC, abstractmethod
import random

# Direcciones posibles como (dx, dy). El eje y crece hacia abajo.
ARRIBA = (0, -1)
ABAJO = (0, 1)
IZQUIERDA = (-1, 0)
DERECHA = (1, 0)
QUIETO = (0, 0)
DIRECCIONES = (ARRIBA, ABAJO, IZQUIERDA, DERECHA)

# Mapa por defecto: '#' pared, '.' punto, 'o' bolita de poder, ' ' vacío,
# 'P' inicio Pacman, 'F' inicio fantasma
PLANO_POR_DEFECTO = [
    "###################",
    "#o.......#.......o#",
    "#.##.###.#.###.##.#",
    "#.................#",
    "#.##.#.#####.#.##.#",
    "#....#...#...#....#",
    "####.#.F.F.F.#.####",
    "#....#.......#....#",
    "#.##.#.#####.#.##.#",
    "#........P........#",
    "#.##.###.#.###.##.#",
    "#o.......#.......o#",
    "###################",
]


class Dificultad:
    """Parámetros de una dificultad: vidas, duración del poder (en turnos) y
    duración de un turno en milisegundos (menos ms = juego más rápido)."""

    def __init__(self, nombre, vidas, duracion_poder, tick_ms, velocidad):
        self._nombre = nombre
        self._vidas = vidas
        self._duracion_poder = duracion_poder
        self._tick_ms = tick_ms
        self._velocidad = velocidad

    @property
    def nombre(self):
        return self._nombre

    @property
    def vidas(self):
        return self._vidas

    @property
    def duracion_poder(self):
        return self._duracion_poder

    @property
    def tick_ms(self):
        return self._tick_ms

    @property
    def velocidad(self):
        return self._velocidad

    @property
    def segundos_poder(self):
        return self._duracion_poder * self._tick_ms / 1000


DIFICULTADES = (
    Dificultad("Fácil", 5, 60, 260, "lenta"),
    Dificultad("Normal", 3, 40, 200, "normal"),
    Dificultad("Difícil", 2, 25, 140, "rápida"),
)
DIFICULTAD_POR_DEFECTO = DIFICULTADES[1]


class Laberinto:
    """Grilla del mapa. Encapsula paredes y puntos."""

    PARED = "#"
    PUNTO = "."
    PILDORA = "o"
    VACIO = " "

    def __init__(self, plano=None):
        plano = plano if plano is not None else PLANO_POR_DEFECTO
        self._celdas = []
        self._inicio_pacman = None
        self._inicios_fantasmas = []
        self._puntos_restantes = 0

        for y, fila in enumerate(plano):
            nueva = []
            for x, ch in enumerate(fila):
                if ch == "P":
                    self._inicio_pacman = (x, y)
                    ch = self.VACIO
                elif ch == "F":
                    self._inicios_fantasmas.append((x, y))
                    ch = self.VACIO
                elif ch in (self.PUNTO, self.PILDORA):
                    self._puntos_restantes += 1
                nueva.append(ch)
            self._celdas.append(nueva)

        if self._inicio_pacman is None:
            raise ValueError("El plano debe contener la posición inicial 'P' de Pacman")
        self._alto = len(self._celdas)
        self._ancho = len(self._celdas[0])

    @property
    def ancho(self):
        return self._ancho

    @property
    def alto(self):
        return self._alto

    @property
    def inicio_pacman(self):
        return self._inicio_pacman

    @property
    def inicios_fantasmas(self):
        return list(self._inicios_fantasmas)

    @property
    def puntos_restantes(self):
        return self._puntos_restantes

    def celda(self, x, y):
        return self._celdas[y][x]

    def es_pared(self, x, y):
        """Fuera del mapa también cuenta como pared."""
        if not (0 <= x < self._ancho and 0 <= y < self._alto):
            return True
        return self._celdas[y][x] == self.PARED

    def hay_punto(self, x, y):
        return not self.es_pared(x, y) and self._celdas[y][x] == self.PUNTO

    def hay_pildora(self, x, y):
        return not self.es_pared(x, y) and self._celdas[y][x] == self.PILDORA

    def consumir_pildora(self, x, y):
        """Retira la bolita de poder de la celda. Devuelve True si había una."""
        if self.hay_pildora(x, y):
            self._celdas[y][x] = self.VACIO
            self._puntos_restantes -= 1
            return True
        return False

    def consumir_punto(self, x, y):
        """Retira el punto de la celda. Devuelve True si había uno."""
        if self.hay_punto(x, y):
            self._celdas[y][x] = self.VACIO
            self._puntos_restantes -= 1
            return True
        return False


class Entidad(ABC):
    """Clase base abstracta: cualquier objeto que ocupa una celda y se mueve."""

    def __init__(self, pos_x, pos_y, color):
        self._pos_x = pos_x
        self._pos_y = pos_y
        self._color = color

    @property
    def pos_x(self):
        return self._pos_x

    @property
    def pos_y(self):
        return self._pos_y

    @property
    def posicion(self):
        return (self._pos_x, self._pos_y)

    @property
    def color(self):
        return self._color

    def _establecer_posicion(self, x, y):
        self._pos_x = x
        self._pos_y = y

    def mover(self, dx, dy, laberinto):
        """Intenta desplazar la entidad (dx, dy). Nunca atraviesa paredes.
        Devuelve True si se movió."""
        nx, ny = self._pos_x + dx, self._pos_y + dy
        if laberinto.es_pared(nx, ny):
            return False
        self._establecer_posicion(nx, ny)
        return True

    @abstractmethod
    def actualizar(self, laberinto):
        """Cada subclase define cómo decide su movimiento en cada turno."""


class Pacman(Entidad):
    VIDAS_INICIALES = 3

    def __init__(self, pos_x, pos_y, color="yellow", vidas=VIDAS_INICIALES):
        super().__init__(pos_x, pos_y, color)
        self._pos_inicial = (pos_x, pos_y)
        self._direccion = QUIETO
        self._direccion_deseada = QUIETO
        self._vidas = vidas

    @property
    def direccion(self):
        return self._direccion

    @property
    def vidas(self):
        return self._vidas

    @property
    def esta_vivo(self):
        return self._vidas > 0

    def solicitar_direccion(self, direccion):
        """Registra la dirección pedida por el jugador (se aplica en cuanto sea posible)."""
        if direccion not in DIRECCIONES:
            raise ValueError(f"Dirección inválida: {direccion}")
        self._direccion_deseada = direccion

    def perder_vida(self):
        if self._vidas > 0:
            self._vidas -= 1

    def reiniciar_posicion(self):
        self._establecer_posicion(*self._pos_inicial)
        self._direccion = QUIETO
        self._direccion_deseada = QUIETO

    def actualizar(self, laberinto):
        # 1) intenta girar hacia la dirección pedida
        if self._direccion_deseada != QUIETO and self.mover(*self._direccion_deseada, laberinto):
            self._direccion = self._direccion_deseada
            return
        # 2) si no puede, sigue en la dirección actual hasta chocar con una pared
        if self._direccion != QUIETO and not self.mover(*self._direccion, laberinto):
            self._direccion = QUIETO


class Fantasma(Entidad):
    def __init__(self, nombre, pos_inicial, color="red", rng=None):
        super().__init__(pos_inicial[0], pos_inicial[1], color)
        self._nombre = nombre
        self._pos_inicial = tuple(pos_inicial)
        self._ultima_direccion = QUIETO
        self._rng = rng if rng is not None else random.Random()
        self._asustado = False
        self._por_terminar = False   # True cuando el efecto está por acabar (parpadeo)
        self._salto = False          # asustado: se mueve un turno sí y otro no

    @property
    def esta_asustado(self):
        return self._asustado

    @property
    def por_terminar(self):
        return self._por_terminar

    def asustar(self):
        self._asustado = True
        self._por_terminar = False

    def calmar(self):
        self._asustado = False
        self._por_terminar = False
        self._salto = False

    def avisar_fin(self, valor):
        self._por_terminar = valor

    @property
    def nombre(self):
        return self._nombre

    @property
    def pos_inicial(self):
        return self._pos_inicial

    def reiniciar_posicion(self):
        self._establecer_posicion(*self._pos_inicial)
        self._ultima_direccion = QUIETO
        self.calmar()

    def actualizar(self, laberinto):
        """Movimiento autónomo: elige al azar una salida libre, evitando
        dar la vuelta salvo que sea un callejón sin salida."""
        if self._asustado:  # asustado: más lento (mueve un turno sí, otro no)
            self._salto = not self._salto
            if self._salto:
                return
        libres = [d for d in DIRECCIONES
                  if not laberinto.es_pared(self.pos_x + d[0], self.pos_y + d[1])]
        if not libres:
            return
        reversa = (-self._ultima_direccion[0], -self._ultima_direccion[1])
        opciones = [d for d in libres if d != reversa] or libres
        eleccion = self._rng.choice(opciones)
        self.mover(*eleccion, laberinto)
        self._ultima_direccion = eleccion


class TableroJuego:
    """Coordina laberinto, Pacman y fantasmas: puntaje, vidas y fin de partida."""

    PUNTOS_POR_PUNTO = 10
    PUNTOS_PILDORA = 50
    PUNTOS_FANTASMA = 200        # se duplica por cada fantasma comido seguido (200, 400, 800...)
    TURNOS_AVISO = 10            # últimos turnos: los fantasmas parpadean
    NOMBRES_FANTASMAS = ("Blinky", "Pinky", "Inky", "Clyde")
    COLORES_FANTASMAS = ("red", "pink", "cyan", "orange")

    def __init__(self, plano=None, rng=None, dificultad=None):
        self._dificultad = dificultad if dificultad is not None else DIFICULTAD_POR_DEFECTO
        self._duracion_poder = self._dificultad.duracion_poder
        self._laberinto = Laberinto(plano)
        self._pacman = Pacman(*self._laberinto.inicio_pacman, vidas=self._dificultad.vidas)
        self._fantasmas = [
            Fantasma(self.NOMBRES_FANTASMAS[i % 4], pos,
                     self.COLORES_FANTASMAS[i % 4], rng)
            for i, pos in enumerate(self._laberinto.inicios_fantasmas)
        ]
        self._puntaje = 0
        self._juego_terminado = False
        self._victoria = False
        self._turnos_poder = 0
        self._combo = 0

    # --- propiedades de solo lectura (encapsulamiento) ---
    @property
    def dificultad(self):
        return self._dificultad

    @property
    def laberinto(self):
        return self._laberinto

    @property
    def pacman(self):
        return self._pacman

    @property
    def fantasmas(self):
        return list(self._fantasmas)

    @property
    def puntaje(self):
        return self._puntaje

    @property
    def juego_terminado(self):
        return self._juego_terminado

    @property
    def victoria(self):
        return self._victoria

    @property
    def poder_activo(self):
        return self._turnos_poder > 0

    # --- lógica ---
    def actualizar_ciclo(self):
        """Avanza un turno: mueve entidades, resuelve colisiones, puntos y fin de partida."""
        if self._juego_terminado:
            return

        previa_pacman = self._pacman.posicion
        previas = [f.posicion for f in self._fantasmas]

        self._pacman.actualizar(self._laberinto)
        for f in self._fantasmas:
            f.actualizar(self._laberinto)

        self._avanzar_poder()

        if self._resolver_colisiones(previa_pacman, previas):
            return

        pos = self._pacman.posicion
        if self._laberinto.consumir_pildora(*pos):
            self._puntaje += self.PUNTOS_PILDORA
            self._activar_poder()
        elif self._laberinto.consumir_punto(*pos):
            self._puntaje += self.PUNTOS_POR_PUNTO

        if self._laberinto.puntos_restantes == 0:
            self._juego_terminado = True
            self._victoria = True

    # --- poder de las bolitas ---
    def _activar_poder(self):
        self._turnos_poder = self._duracion_poder
        self._combo = 0
        for f in self._fantasmas:
            f.asustar()

    def _avanzar_poder(self):
        if self._turnos_poder <= 0:
            return
        self._turnos_poder -= 1
        if self._turnos_poder == 0:
            for f in self._fantasmas:
                f.calmar()
        else:
            aviso = self._turnos_poder <= self.TURNOS_AVISO
            for f in self._fantasmas:
                f.avisar_fin(aviso)

    # --- colisiones ---
    def _resolver_colisiones(self, previa_pacman, previas_fantasmas):
        """Devuelve True si Pacman murió en este turno (y ya se resolvió)."""
        chocados = self._fantasmas_en_colision(previa_pacman, previas_fantasmas)
        if any(not f.esta_asustado for f in chocados):
            self._pacman.perder_vida()
            if not self._pacman.esta_vivo:
                self._juego_terminado = True
                self._victoria = False
            else:
                self._reiniciar_posiciones_entidades()
            return True
        for f in chocados:  # todos asustados: Pacman se los come
            self._puntaje += self.PUNTOS_FANTASMA * (2 ** self._combo)
            self._combo += 1
            f.reiniciar_posicion()
        return False

    def _fantasmas_en_colision(self, previa_pacman, previas_fantasmas):
        """Fantasmas que chocan con Pacman: misma celda o cruce frontal."""
        actual = self._pacman.posicion
        res = []
        for f, previa_f in zip(self._fantasmas, previas_fantasmas):
            if f.posicion == actual or (f.posicion == previa_pacman and actual == previa_f):
                res.append(f)
        return res

    def _reiniciar_posiciones_entidades(self):
        self._turnos_poder = 0
        self._combo = 0
        self._pacman.reiniciar_posicion()
        for f in self._fantasmas:
            f.reiniciar_posicion()
