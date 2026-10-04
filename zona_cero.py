
"""
ZONA CERO - Battle Royale (Versión 1)
=====================================
Juego sencillo hecho con Python y Pygame.

Cómo ejecutarlo:
    1) pip install pygame
    2) python zona_cero.py

Datos para iniciar sesión (se cambian en la sección 1):
    Correo:      juego@gmail.com
    Contraseña:  1234

Controles en la partida:
    W A S D ........ moverse
    Mouse .......... apuntar
    Click izquierdo  disparar (se puede mantener apretado)
    R .............. recargar
    ESC ............ abandonar la partida

Organización del código:
    1. Configuración general
    2. Funciones útiles
    3. Clase Boton
    4. Clase Mapa (terrenos, edificios, obstáculos)
    5. Clases del juego: Bala, Entidad, Jugador, Enemigo, Objeto, ZonaSegura
    6. Clase Partida (la lógica de una batalla)
    7. Clase Juego (pantallas: login, menú, mapa, historia, etc.)
"""

import math
import random
import sys

import pygame

# =====================================================================
# 1. CONFIGURACIÓN GENERAL
# =====================================================================
ANCHO, ALTO = 960, 640            # tamaño de la ventana
FPS = 60                          # cuadros por segundo
MUNDO_ANCHO, MUNDO_ALTO = 1800, 1400   # tamaño del mapa completo

# Datos correctos para iniciar sesión
CORREO_CORRECTO = "juego@gmail.com"
CONTRASENA_CORRECTA = "1234"

# Colores (R, G, B)
BLANCO = (255, 255, 255)
NEGRO = (0, 0, 0)
ROJO = (220, 50, 50)
VERDE = (60, 200, 90)
AZUL = (70, 150, 250)
AMARILLO = (250, 210, 60)
NARANJA = (255, 140, 40)
CELESTE = (80, 220, 255)
GRIS = (150, 155, 165)

# Dificultades: (nombre, cantidad de enemigos, daño de cada disparo enemigo)
DIFICULTADES = [
    ("Fácil", 5, 6),
    ("Normal", 8, 8),
    ("Difícil", 12, 10),
]

# Datos del jugador
VIDA_JUGADOR = 100
CARGADOR_MAX = 30
MUNICION_RESERVA_INICIAL = 90
TIEMPO_RECARGA = 1.5              # segundos
DANO_BALA_JUGADOR = 25

# =====================================================================
# 2. FUNCIONES ÚTILES
# =====================================================================
_fuentes = {}


def fuente(tamano, negrita=False):
    """Devuelve una fuente (la guarda para no crearla a cada rato)."""
    clave = (tamano, negrita)
    if clave not in _fuentes:
        _fuentes[clave] = pygame.font.SysFont("arial", tamano, bold=negrita)
    return _fuentes[clave]


def dibujar_texto(pantalla, texto, tamano, color, x, y,
                  centrado=True, negrita=False, sombra=False):
    """Escribe un texto en pantalla. Si centrado=True, (x, y) es el centro."""
    f = fuente(tamano, negrita)
    imagen = f.render(texto, True, color)
    rect = imagen.get_rect()
    if centrado:
        rect.center = (x, y)
    else:
        rect.topleft = (x, y)
    if sombra:
        pantalla.blit(f.render(texto, True, NEGRO), rect.move(2, 2))
    pantalla.blit(imagen, rect)


def dibujar_parrafo(pantalla, texto, tamano, color, x, y, ancho_max):
    """Escribe un párrafo largo cortando las líneas. Devuelve la y final."""
    f = fuente(tamano)
    linea = ""
    for palabra in texto.split(" "):
        prueba = (linea + " " + palabra).strip()
        if f.size(prueba)[0] <= ancho_max:
            linea = prueba
        else:
            pantalla.blit(f.render(linea, True, color), (x, y))
            y += f.get_height() + 4
            linea = palabra
    if linea:
        pantalla.blit(f.render(linea, True, color), (x, y))
        y += f.get_height() + 4
    return y


def formatear_tiempo(segundos):
    """Convierte segundos a formato mm:ss."""
    segundos = int(segundos)
    return f"{segundos // 60:02d}:{segundos % 60:02d}"


def hay_linea_de_vision(bloques, x1, y1, x2, y2):
    """True si no hay ningún obstáculo entre dos puntos."""
    distancia = math.hypot(x2 - x1, y2 - y1)
    pasos = max(int(distancia // 16), 1)
    for i in range(1, pasos + 1):
        t = i / pasos
        px = int(x1 + (x2 - x1) * t)
        py = int(y1 + (y2 - y1) * t)
        for bloque in bloques:
            if bloque.collidepoint(px, py):
                return False
    return True


def posicion_libre(zona_rect, bloques, margen=30):
    """Busca un punto dentro de zona_rect que no esté tapado por obstáculos."""
    for _ in range(200):
        x = random.randint(zona_rect.left + 40, zona_rect.right - 40)
        y = random.randint(zona_rect.top + 40, zona_rect.bottom - 40)
        prueba = pygame.Rect(x - margen, y - margen, margen * 2, margen * 2)
        if prueba.collidelist(bloques) == -1:
            return x, y
    return zona_rect.center


def crear_fondo():
    """Fondo oscuro con cuadrícula para las pantallas de menú."""
    fondo = pygame.Surface((ANCHO, ALTO))
    fondo.fill((14, 17, 24))
    for x in range(0, ANCHO, 40):
        pygame.draw.line(fondo, (22, 27, 38), (x, 0), (x, ALTO))
    for y in range(0, ALTO, 40):
        pygame.draw.line(fondo, (22, 27, 38), (0, y), (ANCHO, y))
    return fondo


# =====================================================================
# 3. BOTÓN
# =====================================================================
class Boton:
    """Un botón rectangular con texto."""

    def __init__(self, texto, x, y, ancho, alto,
                 color=(40, 52, 78), color_hover=(80, 105, 160)):
        self.texto = texto
        self.rect = pygame.Rect(0, 0, ancho, alto)
        self.rect.center = (x, y)
        self.color = color
        self.color_hover = color_hover

    def dibujar(self, pantalla):
        encima = self.rect.collidepoint(pygame.mouse.get_pos())
        color = self.color_hover if encima else self.color
        pygame.draw.rect(pantalla, color, self.rect, border_radius=8)
        pygame.draw.rect(pantalla, BLANCO, self.rect, 2, border_radius=8)
        dibujar_texto(pantalla, self.texto, 24, BLANCO,
                      self.rect.centerx, self.rect.centery, negrita=True)

    def fue_clickeado(self, evento):
        return (evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1
                and self.rect.collidepoint(evento.pos))


# =====================================================================
# 4. MAPA
# =====================================================================
class Mapa:
    """
    El mapa de Nova-7. Se dibuja UNA sola vez en una imagen grande
    (self.superficie) y después solo se muestra el pedazo que ve la cámara.

    - self.zonas: lista de (nombre, rectángulo, color)
    - self.obstaculos: lista de (rectángulo, tipo, color)
    - self.bloques: los rectángulos con los que se choca
    """

    def __init__(self):
        # (nombre, rectángulo de la zona, color del suelo)
        self.zonas = [
            ("Ciudad Central", pygame.Rect(600, 400, 700, 600), (78, 82, 92)),
            ("Fábrica 09", pygame.Rect(0, 500, 600, 500), (112, 98, 84)),
            ("Bosque Rojo", pygame.Rect(0, 0, 600, 500), (92, 52, 46)),
            ("Estación Norte", pygame.Rect(600, 0, 700, 400), (72, 92, 112)),
            ("Zona Desértica", pygame.Rect(1300, 500, 500, 500), (214, 186, 120)),
            ("Laboratorio X", pygame.Rect(1300, 0, 500, 500), (60, 112, 104)),
            ("Base Sur", pygame.Rect(0, 1000, 1800, 400), (70, 100, 66)),
        ]
        self.obstaculos = []
        self._crear_obstaculos()
        self.bloques = [o[0] for o in self.obstaculos]
        self.superficie = self._dibujar_mundo()
        # Versión chiquita para el minimapa
        self.mini = pygame.transform.smoothscale(self.superficie, (180, 140))

    # ---------- Obstáculos ----------
    def _agregar(self, x, y, ancho, alto, tipo, color):
        self.obstaculos.append((pygame.Rect(x, y, ancho, alto), tipo, color))

    def _agregar_circular(self, x, y, radio, tipo, color):
        lado = int(radio * 1.4)
        self.obstaculos.append(
            (pygame.Rect(x - lado // 2, y - lado // 2, lado, lado), tipo, color))

    def _crear_obstaculos(self):
        rng = random.Random(7)   # semilla fija: el mapa siempre es igual

        # --- Ciudad Central: edificios en cuatro manzanas ---
        color = (125, 130, 146)
        for x0 in (650, 990):
            for y0 in (440, 790):
                for dx in (0, 120):
                    for dy in (0, 130):
                        self._agregar(x0 + dx, y0 + dy, 80, 90, "edificio", color)

        # --- Fábrica 09 ---
        color = (150, 112, 90)
        self._agregar(60, 540, 220, 120, "edificio", color)
        self._agregar(340, 540, 200, 120, "edificio", color)
        self._agregar(60, 740, 140, 200, "edificio", color)
        for x, y, w, h in [(300, 880, 60, 30), (380, 880, 60, 30),
                           (300, 930, 60, 30), (480, 900, 30, 60)]:
            self._agregar(x, y, w, h, "caja", (200, 110, 50))

        # --- Bosque Rojo: árboles al azar ---
        arboles = []
        intentos = 0
        while len(arboles) < 40 and intentos < 3000:
            intentos += 1
            r = rng.randint(16, 24)
            x = rng.randint(40, 560)
            y = rng.randint(40, 460)
            # que no queden pegados (así el jugador puede pasar)
            if any(math.hypot(x - ax, y - ay) < ar + r + 36 for ax, ay, ar in arboles):
                continue
            arboles.append((x, y, r))
            tono = rng.choice([(170, 50, 50), (140, 35, 40), (185, 70, 55)])
            self._agregar_circular(x, y, r, "arbol", tono)

        # --- Estación Norte ---
        color = (100, 122, 152)
        self._agregar(640, 50, 200, 90, "edificio", color)
        self._agregar(960, 60, 120, 80, "edificio", color)
        self._agregar(1100, 310, 100, 60, "edificio", color)
        self._agregar(660, 222, 100, 26, "vagon", (150, 70, 70))
        self._agregar(770, 222, 90, 26, "vagon", (150, 70, 70))
        self._agregar(960, 262, 100, 26, "vagon", (70, 100, 150))
        self._agregar(1070, 262, 110, 26, "vagon", (70, 100, 150))

        # --- Laboratorio X ---
        color = (175, 205, 205)
        self._agregar(1400, 60, 300, 160, "edificio", color)
        self._agregar(1340, 290, 120, 120, "edificio", color)
        self._agregar(1600, 290, 140, 140, "edificio", color)

        # --- Zona Desértica: rocas ---
        rocas = []
        intentos = 0
        while len(rocas) < 14 and intentos < 2000:
            intentos += 1
            r = rng.randint(18, 30)
            x = rng.randint(1340, 1760)
            y = rng.randint(540, 960)
            if any(math.hypot(x - ax, y - ay) < ar + r + 40 for ax, ay, ar in rocas):
                continue
            rocas.append((x, y, r))
            self._agregar_circular(x, y, r, "roca", (150, 125, 95))

        # --- Base Sur: búnkeres y sacos de arena ---
        color = (92, 124, 92)
        for x, y, w, h in [(150, 1080, 140, 90), (500, 1150, 120, 90),
                           (700, 1100, 120, 80), (1000, 1120, 120, 80),
                           (1250, 1080, 140, 90), (1500, 1200, 140, 100)]:
            self._agregar(x, y, w, h, "edificio", color)
        self._agregar(700, 1250, 100, 20, "saco", (190, 170, 120))
        self._agregar(1000, 1250, 100, 20, "saco", (190, 170, 120))

    def zona_en(self, x, y):
        """Nombre de la zona donde está el punto (x, y)."""
        for nombre, rect, _ in self.zonas:
            if rect.collidepoint(int(x), int(y)):
                return nombre
        return "Nova-7"

    # ---------- Dibujo ----------
    def _dibujar_mundo(self):
        sup = pygame.Surface((MUNDO_ANCHO, MUNDO_ALTO))
        rng = random.Random(3)

        # 1) Suelo de cada zona, con puntitos para darle textura
        for nombre, rect, color in self.zonas:
            sup.fill(color, rect)
            for _ in range(rect.w * rect.h // 900):
                x = rng.randint(rect.left, rect.right - 5)
                y = rng.randint(rect.top, rect.bottom - 5)
                tono = rng.randint(-12, 12)
                c = tuple(max(0, min(255, v + tono)) for v in color)
                sup.fill(c, (x, y, 4, 4))

        # 2) Decoraciones propias de cada zona
        for _ in range(9):                                   # dunas
            x = rng.randint(1320, 1660)
            y = rng.randint(520, 900)
            pygame.draw.ellipse(sup, (228, 202, 146), (x, y, rng.randint(80, 160), 50))
        for _ in range(10):                                  # manchas del bosque
            x = rng.randint(10, 500)
            y = rng.randint(10, 400)
            pygame.draw.ellipse(sup, (72, 38, 36), (x, y, rng.randint(60, 120), 50))
        for x in range(1300, 1800, 50):                      # baldosas del laboratorio
            pygame.draw.line(sup, (72, 128, 118), (x, 0), (x, 500))
        for y in range(0, 500, 50):
            pygame.draw.line(sup, (72, 128, 118), (1300, y), (1800, y))
        pygame.draw.line(sup, (150, 160, 170), (1300, 250), (1800, 250), 6)  # tubería

        # Vías del tren (Estación Norte)
        for y in (220, 262):
            pygame.draw.rect(sup, (60, 60, 66), (600, y, 700, 28))
            for x in range(600, 1300, 20):
                pygame.draw.line(sup, (100, 80, 60), (x, y), (x, y + 27), 3)
            pygame.draw.line(sup, (190, 190, 200), (600, y + 6), (1300, y + 6), 2)
            pygame.draw.line(sup, (190, 190, 200), (600, y + 21), (1300, y + 21), 2)

        # Caminos (calle vertical y calle horizontal)
        camino = (52, 55, 63)
        pygame.draw.rect(sup, camino, (870, 0, 60, MUNDO_ALTO))
        pygame.draw.rect(sup, camino, (0, 690, MUNDO_ANCHO, 60))
        for y in range(0, MUNDO_ALTO, 50):
            pygame.draw.line(sup, (200, 190, 80), (900, y), (900, y + 25), 3)
        for x in range(0, MUNDO_ANCHO, 50):
            pygame.draw.line(sup, (200, 190, 80), (x, 720), (x + 25, 720), 3)

        # Zona de aterrizaje del jugador
        pygame.draw.circle(sup, (55, 75, 55), (900, 1300), 55)
        pygame.draw.circle(sup, BLANCO, (900, 1300), 55, 3)
        texto_h = fuente(50, True).render("H", True, BLANCO)
        sup.blit(texto_h, texto_h.get_rect(center=(900, 1300)))

        # 3) Obstáculos
        for rect, tipo, color in self.obstaculos:
            self._dibujar_obstaculo(sup, rect, tipo, color)

        # 4) Bordes de zonas y nombres
        for nombre, rect, _ in self.zonas:
            pygame.draw.rect(sup, (20, 20, 25), rect, 3)
            etiqueta = fuente(34, True).render(nombre, True, BLANCO)
            sombra = fuente(34, True).render(nombre, True, NEGRO)
            etiqueta.set_alpha(170)
            sombra.set_alpha(120)
            sup.blit(sombra, (rect.left + 18, rect.top + 14))
            sup.blit(etiqueta, (rect.left + 16, rect.top + 12))
        pygame.draw.rect(sup, NEGRO, (0, 0, MUNDO_ANCHO, MUNDO_ALTO), 6)
        return sup

    def _dibujar_obstaculo(self, sup, rect, tipo, color):
        oscuro = tuple(int(v * 0.6) for v in color)
        claro = tuple(min(255, int(v * 1.2)) for v in color)
        if tipo == "edificio":
            pygame.draw.rect(sup, (0, 0, 0), rect.move(5, 5))           # sombra
            pygame.draw.rect(sup, color, rect)
            pygame.draw.rect(sup, oscuro, rect, 3)
            for wx in range(rect.left + 10, rect.right - 14, 22):       # ventanas
                for wy in range(rect.top + 10, rect.bottom - 14, 22):
                    pygame.draw.rect(sup, claro, (wx, wy, 10, 10))
        elif tipo == "arbol":
            radio = int(rect.w * 0.72)
            centro = rect.center
            pygame.draw.circle(sup, (0, 0, 0), (centro[0] + 4, centro[1] + 5), radio)
            pygame.draw.circle(sup, color, centro, radio)
            pygame.draw.circle(sup, oscuro, centro, radio, 3)
            pygame.draw.circle(sup, claro, (centro[0] - 4, centro[1] - 4), radio // 3)
        elif tipo == "roca":
            radio = int(rect.w * 0.72)
            pygame.draw.circle(sup, color, rect.center, radio)
            pygame.draw.circle(sup, oscuro, rect.center, radio, 3)
            pygame.draw.circle(sup, claro, (rect.centerx - 5, rect.centery - 5), radio // 3)
        elif tipo == "vagon":
            pygame.draw.rect(sup, color, rect, border_radius=4)
            pygame.draw.rect(sup, oscuro, rect, 2, border_radius=4)
            for wx in range(rect.left + 8, rect.right - 10, 16):
                pygame.draw.rect(sup, (220, 230, 240), (wx, rect.top + 7, 8, 10))
        elif tipo == "caja":
            pygame.draw.rect(sup, color, rect)
            pygame.draw.rect(sup, oscuro, rect, 2)
            for lx in range(rect.left + 6, rect.right - 3, 8):
                pygame.draw.line(sup, oscuro, (lx, rect.top), (lx, rect.bottom), 1)
        else:  # saco
            pygame.draw.rect(sup, color, rect, border_radius=8)
            pygame.draw.rect(sup, oscuro, rect, 2, border_radius=8)


# =====================================================================
# 5. CLASES DEL JUEGO
# =====================================================================
class Bala:
    """Un disparo. 'dueno' puede ser 'jugador' o 'enemigo'."""

    def __init__(self, x, y, angulo, dueno, dano, velocidad=700, alcance=650):
        self.x = x
        self.y = y
        self.vx = math.cos(angulo) * velocidad
        self.vy = math.sin(angulo) * velocidad
        self.dueno = dueno
        self.dano = dano
        self.vida = alcance / velocidad      # segundos que dura en el aire

    def actualizar(self, dt, bloques):
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.vida -= dt
        if not (0 <= self.x <= MUNDO_ANCHO and 0 <= self.y <= MUNDO_ALTO):
            self.vida = 0
        for bloque in bloques:                # choca con edificios, árboles...
            if bloque.collidepoint(int(self.x), int(self.y)):
                self.vida = 0
                break

    def dibujar(self, pantalla, cam_x, cam_y):
        color = AMARILLO if self.dueno == "jugador" else NARANJA
        largo = 10
        norma = math.hypot(self.vx, self.vy)
        ux, uy = self.vx / norma, self.vy / norma
        inicio = (self.x - cam_x, self.y - cam_y)
        fin = (inicio[0] - ux * largo, inicio[1] - uy * largo)
        pygame.draw.line(pantalla, color, inicio, fin, 3)


class Entidad:
    """Base para todo lo que se mueve y tiene vida (jugador y enemigos)."""

    def __init__(self, x, y, radio, vida):
        self.x = float(x)
        self.y = float(y)
        self.radio = radio
        self.vida = vida
        self.vida_max = vida
        self.angulo = 0.0
        self.rect = pygame.Rect(0, 0, radio * 2, radio * 2)
        self.rect.center = (x, y)

    def mover(self, dx, dy, bloques):
        """Mueve la entidad chocando con los obstáculos (eje X y luego eje Y)."""
        self.x += dx
        self.rect.centerx = round(self.x)
        for b in bloques:
            if self.rect.colliderect(b):
                if dx > 0:
                    self.rect.right = b.left
                elif dx < 0:
                    self.rect.left = b.right
                self.x = self.rect.centerx
        self.x = max(self.radio, min(MUNDO_ANCHO - self.radio, self.x))
        self.rect.centerx = round(self.x)

        self.y += dy
        self.rect.centery = round(self.y)
        for b in bloques:
            if self.rect.colliderect(b):
                if dy > 0:
                    self.rect.bottom = b.top
                elif dy < 0:
                    self.rect.top = b.bottom
                self.y = self.rect.centery
        self.y = max(self.radio, min(MUNDO_ALTO - self.radio, self.y))
        self.rect.centery = round(self.y)


class Jugador(Entidad):
    VELOCIDAD = 230

    def __init__(self, x, y):
        super().__init__(x, y, 14, VIDA_JUGADOR)
        self.cargador = CARGADOR_MAX
        self.reserva = MUNICION_RESERVA_INICIAL
        self.recargando = False
        self.t_recarga = 0.0
        self.cadencia = 0.0      # tiempo de espera entre disparos
        self.golpe = 0.0         # para mostrar el destello rojo al ser herido

    def actualizar(self, dt, teclas, bloques):
        dx = (teclas[pygame.K_d] or teclas[pygame.K_RIGHT]) - (teclas[pygame.K_a] or teclas[pygame.K_LEFT])
        dy = (teclas[pygame.K_s] or teclas[pygame.K_DOWN]) - (teclas[pygame.K_w] or teclas[pygame.K_UP])
        if dx != 0 and dy != 0:                      # en diagonal no va más rápido
            dx *= 0.7071
            dy *= 0.7071
        self.mover(dx * self.VELOCIDAD * dt, dy * self.VELOCIDAD * dt, bloques)

        self.cadencia -= dt
        self.golpe -= dt
        if self.recargando:
            self.t_recarga -= dt
            if self.t_recarga <= 0:
                necesita = CARGADOR_MAX - self.cargador
                carga = min(necesita, self.reserva)
                self.cargador += carga
                self.reserva -= carga
                self.recargando = False

    def iniciar_recarga(self):
        if (not self.recargando and self.cargador < CARGADOR_MAX
                and self.reserva > 0):
            self.recargando = True
            self.t_recarga = TIEMPO_RECARGA

    def disparar(self, multiplicador_dano=1.0):
        """Devuelve una Bala si pudo disparar, o None."""
        if self.recargando or self.cadencia > 0:
            return None
        if self.cargador <= 0:
            self.iniciar_recarga()                   # recarga automática
            return None
        self.cargador -= 1
        self.cadencia = 0.14
        ang = self.angulo + random.uniform(-0.03, 0.03)
        return Bala(self.x + math.cos(ang) * 22, self.y + math.sin(ang) * 22,
                    ang, "jugador", DANO_BALA_JUGADOR * multiplicador_dano)

    def recibir_dano(self, cantidad):
        self.vida -= cantidad
        self.golpe = 0.2

    def dibujar(self, pantalla, cam_x, cam_y):
        pos = (int(self.x - cam_x), int(self.y - cam_y))
        fin_arma = (pos[0] + math.cos(self.angulo) * 26,
                    pos[1] + math.sin(self.angulo) * 26)
        pygame.draw.line(pantalla, (40, 40, 45), pos, fin_arma, 6)
        pygame.draw.circle(pantalla, AZUL, pos, self.radio)
        pygame.draw.circle(pantalla, BLANCO, pos, self.radio, 2)


class Enemigo(Entidad):
    VELOCIDAD = 95
    DETECCION = 380          # a qué distancia ve al jugador

    def __init__(self, x, y, dano):
        super().__init__(x, y, 14, 60)
        self.dano = dano
        self.destino = None
        self.t_destino = 0.0
        self.t_disparo = random.uniform(0.6, 1.6)
        self.t_bloqueado = 0.0
        self.t_vagar = 0.0
        self.sentido_giro = random.choice([-1, 1])

    def elegir_destino(self, zona):
        """Elige un punto al azar dentro de la zona segura."""
        ang = random.uniform(0, math.tau)
        dist = random.uniform(0, max(zona.radio * 0.7, 30))
        self.destino = (zona.cx + math.cos(ang) * dist, zona.cy + math.sin(ang) * dist)
        self.t_destino = random.uniform(3, 6)

    def actualizar(self, dt, jugador, bloques, zona):
        """Mueve al enemigo. Devuelve una Bala si dispara."""
        self.t_disparo -= dt
        self.t_destino -= dt
        dx_j = jugador.x - self.x
        dy_j = jugador.y - self.y
        dist = math.hypot(dx_j, dy_j) or 1
        ux, uy = dx_j / dist, dy_j / dist
        self.angulo = math.atan2(dy_j, dx_j)
        fuera = not zona.contiene(self.x, self.y)

        vx = vy = 0.0
        velocidad = self.VELOCIDAD
        if self.t_vagar > 0:
            self.t_vagar -= dt

        if fuera or self.t_vagar > 0 or dist >= self.DETECCION:
            # --- Patrullar ---
            if fuera:
                self.destino = (zona.cx, zona.cy)        # volver a la zona segura
            elif (self.destino is None or self.t_destino <= 0 or
                  math.hypot(self.destino[0] - self.x, self.destino[1] - self.y) < 25):
                self.elegir_destino(zona)
            ddx = self.destino[0] - self.x
            ddy = self.destino[1] - self.y
            d = math.hypot(ddx, ddy)
            if d > 1:
                vx, vy = ddx / d, ddy / d
        else:
            # --- Combatir ---
            velocidad *= 0.85
            if dist > 230:
                vx, vy = ux, uy                          # acercarse
            elif dist < 140:
                vx, vy = -ux, -uy                        # alejarse
            else:
                vx, vy = -uy * self.sentido_giro, ux * self.sentido_giro  # dar vueltas

        antes = (self.x, self.y)
        self.mover(vx * velocidad * dt, vy * velocidad * dt, bloques)
        avanzo = math.hypot(self.x - antes[0], self.y - antes[1])
        if (vx or vy) and avanzo < velocidad * dt * 0.3:
            self.t_bloqueado += dt                       # se trabó con una pared
        else:
            self.t_bloqueado = 0
        if self.t_bloqueado > 0.5:
            self.t_bloqueado = 0
            self.t_vagar = 1.5
            self.sentido_giro *= -1
            self.elegir_destino(zona)

        # --- Disparar ---
        if dist < self.DETECCION and self.t_disparo <= 0:
            if hay_linea_de_vision(bloques, self.x, self.y, jugador.x, jugador.y):
                self.t_disparo = random.uniform(0.7, 1.3)
                ang = self.angulo + random.uniform(-0.15, 0.15)
                return Bala(self.x + math.cos(ang) * 20, self.y + math.sin(ang) * 20,
                            ang, "enemigo", self.dano, velocidad=450, alcance=450)
            self.t_disparo = 0.3
        return None

    def dibujar(self, pantalla, cam_x, cam_y):
        pos = (int(self.x - cam_x), int(self.y - cam_y))
        if not (-40 < pos[0] < ANCHO + 40 and -40 < pos[1] < ALTO + 40):
            return
        fin_arma = (pos[0] + math.cos(self.angulo) * 24,
                    pos[1] + math.sin(self.angulo) * 24)
        pygame.draw.line(pantalla, (40, 40, 45), pos, fin_arma, 6)
        pygame.draw.circle(pantalla, ROJO, pos, self.radio)
        pygame.draw.circle(pantalla, (90, 10, 10), pos, self.radio, 2)
        # barra de vida
        ancho = 34
        pygame.draw.rect(pantalla, (60, 0, 0), (pos[0] - ancho // 2, pos[1] - 26, ancho, 5))
        llena = max(0, int(ancho * self.vida / self.vida_max))
        pygame.draw.rect(pantalla, VERDE, (pos[0] - ancho // 2, pos[1] - 26, llena, 5))


class Objeto:
    """Cosas que se recogen: 'botiquin', 'municion' o 'fragmento' del Núcleo."""

    def __init__(self, x, y, tipo):
        self.x = x
        self.y = y
        self.tipo = tipo

    def dibujar(self, pantalla, cam_x, cam_y, tiempo):
        x = int(self.x - cam_x)
        y = int(self.y - cam_y)
        if not (-30 < x < ANCHO + 30 and -30 < y < ALTO + 30):
            return
        if self.tipo == "botiquin":
            pygame.draw.rect(pantalla, BLANCO, (x - 11, y - 11, 22, 22), border_radius=4)
            pygame.draw.rect(pantalla, ROJO, (x - 3, y - 8, 6, 16))
            pygame.draw.rect(pantalla, ROJO, (x - 8, y - 3, 16, 6))
        elif self.tipo == "municion":
            pygame.draw.rect(pantalla, (170, 130, 30), (x - 12, y - 9, 24, 18), border_radius=3)
            for bx in (-7, -1, 5):
                pygame.draw.rect(pantalla, AMARILLO, (x + bx, y - 6, 4, 12))
        else:  # fragmento del Núcleo
            brillo = 14 + int(3 * math.sin(tiempo * 6))
            pygame.draw.circle(pantalla, (20, 90, 110), (x, y), brillo + 4)
            puntos = [(x, y - 13), (x + 9, y), (x, y + 13), (x - 9, y)]
            pygame.draw.polygon(pantalla, CELESTE, puntos)
            pygame.draw.polygon(pantalla, BLANCO, puntos, 2)


class ZonaSegura:
    """
    Círculo seguro que se va achicando por fases.
    Cada fase: (segundos de espera, radio final, segundos que tarda en achicarse)
    """
    FASES = [(20, 800, 30), (15, 500, 30), (15, 280, 30), (10, 100, 30)]

    def __init__(self):
        self.cx = MUNDO_ANCHO / 2
        self.cy = MUNDO_ALTO / 2
        self.radio = 1200.0
        self.fase = 0
        self.estado = "espera"               # 'espera' o 'reduciendo'
        self.timer = self.FASES[0][0]
        self.radio_inicio = self.radio

    def actualizar(self, dt):
        if self.fase >= len(self.FASES):
            return
        _, objetivo, duracion = self.FASES[self.fase]
        self.timer -= dt
        if self.estado == "espera":
            if self.timer <= 0:
                self.estado = "reduciendo"
                self.timer = duracion
                self.radio_inicio = self.radio
        else:
            avance = 1 - max(self.timer, 0) / duracion
            self.radio = self.radio_inicio + (objetivo - self.radio_inicio) * avance
            if self.timer <= 0:
                self.radio = objetivo
                self.fase += 1
                self.estado = "espera"
                if self.fase < len(self.FASES):
                    self.timer = self.FASES[self.fase][0]

    def contiene(self, x, y):
        return math.hypot(x - self.cx, y - self.cy) <= self.radio

    def dano_por_segundo(self):
        """Fuera de la zona el daño aumenta con cada fase."""
        return 4 + 2 * self.fase

    def texto_estado(self):
        if self.fase >= len(self.FASES):
            return "ZONA FINAL - ¡Quedate adentro!"
        if self.estado == "espera":
            return f"La zona se reduce en {int(self.timer) + 1} s"
        return "¡LA ZONA SE ESTÁ REDUCIENDO!"


# =====================================================================
# 6. PARTIDA
# =====================================================================
class Partida:
    """Toda la lógica de una batalla: jugador, enemigos, balas, zona, HUD."""

    def __init__(self, mapa, cantidad_enemigos, dano_enemigo):
        self.mapa = mapa
        self.jugador = Jugador(900, 1300)
        self.zona = ZonaSegura()
        self.balas = []
        self.tiempo = 0.0
        self.eliminaciones = 0
        self.dano_realizado = 0
        self.fragmentos = 0
        self.resultado = None                # None, 'victoria' o 'derrota'
        self.cam_x = 0
        self.cam_y = 0
        self.capa_zona = pygame.Surface((ANCHO, ALTO), pygame.SRCALPHA)
        self.enemigos = self._crear_enemigos(cantidad_enemigos, dano_enemigo)
        self.objetos = self._crear_objetos()
        self._actualizar_camara()

    # ---------- Creación ----------
    def _crear_enemigos(self, cantidad, dano):
        enemigos = []
        zonas = [z for z in self.mapa.zonas if z[0] != "Base Sur"]
        for _ in range(cantidad):
            for _ in range(30):                          # lejos del jugador
                _, rect, _ = random.choice(zonas)
                x, y = posicion_libre(rect, self.mapa.bloques)
                if math.hypot(x - self.jugador.x, y - self.jugador.y) > 500:
                    break
            enemigos.append(Enemigo(x, y, dano))
        return enemigos

    def _crear_objetos(self):
        objetos = []
        for nombre, rect, _ in self.mapa.zonas:
            x, y = posicion_libre(rect, self.mapa.bloques)
            objetos.append(Objeto(x, y, "botiquin"))
            for _ in range(2):
                x, y = posicion_libre(rect, self.mapa.bloques)
                objetos.append(Objeto(x, y, "municion"))
        for nombre in ("Ciudad Central", "Fábrica 09", "Laboratorio X",
                       "Estación Norte", "Bosque Rojo"):
            rect = next(z[1] for z in self.mapa.zonas if z[0] == nombre)
            x, y = posicion_libre(rect, self.mapa.bloques)
            objetos.append(Objeto(x, y, "fragmento"))
        return objetos

    # ---------- Eventos ----------
    def manejar_evento(self, evento):
        """Devuelve 'abandonar' si el jugador apretó ESC."""
        if evento.type == pygame.KEYDOWN:
            if evento.key == pygame.K_r:
                self.jugador.iniciar_recarga()
            elif evento.key == pygame.K_ESCAPE:
                return "abandonar"
        return None

    # ---------- Actualización ----------
    def _actualizar_camara(self):
        self.cam_x = max(0, min(MUNDO_ANCHO - ANCHO, self.jugador.x - ANCHO / 2))
        self.cam_y = max(0, min(MUNDO_ALTO - ALTO, self.jugador.y - ALTO / 2))

    def actualizar(self, dt):
        if self.resultado:
            return
        self.tiempo += dt
        j = self.jugador
        bloques = self.mapa.bloques

        # Jugador
        j.actualizar(dt, pygame.key.get_pressed(), bloques)
        self._actualizar_camara()
        mx, my = pygame.mouse.get_pos()
        j.angulo = math.atan2(my - (j.y - self.cam_y), mx - (j.x - self.cam_x))
        if pygame.mouse.get_pressed()[0]:
            bala = j.disparar(1 + 0.1 * self.fragmentos)
            if bala:
                self.balas.append(bala)

        # Zona segura y su daño
        self.zona.actualizar(dt)
        dano_zona = self.zona.dano_por_segundo() * dt
        if not self.zona.contiene(j.x, j.y):
            j.vida -= dano_zona

        # Enemigos
        for e in self.enemigos:
            bala = e.actualizar(dt, j, bloques, self.zona)
            if bala:
                self.balas.append(bala)
            if not self.zona.contiene(e.x, e.y):
                e.vida -= dano_zona

        # Balas
        for b in self.balas:
            b.actualizar(dt, bloques)
            if b.vida <= 0:
                continue
            if b.dueno == "jugador":
                for e in self.enemigos:
                    if math.hypot(b.x - e.x, b.y - e.y) < e.radio + 3 and e.vida > 0:
                        self.dano_realizado += min(b.dano, e.vida)
                        e.vida -= b.dano
                        b.vida = 0
                        if e.vida <= 0:
                            self.eliminaciones += 1
                        break
            else:
                if math.hypot(b.x - j.x, b.y - j.y) < j.radio + 3:
                    j.recibir_dano(b.dano)
                    b.vida = 0
        self.balas = [b for b in self.balas if b.vida > 0]

        # Enemigos eliminados (a veces sueltan munición)
        vivos = []
        for e in self.enemigos:
            if e.vida > 0:
                vivos.append(e)
            elif random.random() < 0.5:
                self.objetos.append(Objeto(e.x, e.y, "municion"))
        self.enemigos = vivos

        # Recoger objetos
        for o in self.objetos[:]:
            if math.hypot(o.x - j.x, o.y - j.y) < 26:
                if o.tipo == "botiquin":
                    if j.vida >= VIDA_JUGADOR:
                        continue                              # no lo gastes con la vida llena
                    j.vida = min(VIDA_JUGADOR, j.vida + 35)
                elif o.tipo == "municion":
                    j.reserva += 30
                else:
                    self.fragmentos += 1                      # +10% de daño
                self.objetos.remove(o)

        # ¿Terminó la partida?
        if j.vida <= 0:
            j.vida = 0
            self.resultado = "derrota"
        elif not self.enemigos:
            self.resultado = "victoria"

    # ---------- Dibujo ----------
    def dibujar(self, pantalla):
        cam_x, cam_y = int(self.cam_x), int(self.cam_y)
        pantalla.blit(self.mapa.superficie, (0, 0),
                      pygame.Rect(cam_x, cam_y, ANCHO, ALTO))

        for o in self.objetos:
            o.dibujar(pantalla, cam_x, cam_y, self.tiempo)
        for e in self.enemigos:
            e.dibujar(pantalla, cam_x, cam_y)
        self.jugador.dibujar(pantalla, cam_x, cam_y)
        for b in self.balas:
            b.dibujar(pantalla, cam_x, cam_y)

        self._dibujar_zona(pantalla, cam_x, cam_y)
        self._dibujar_hud(pantalla)

    def _dibujar_zona(self, pantalla, cam_x, cam_y):
        centro = (int(self.zona.cx - cam_x), int(self.zona.cy - cam_y))
        radio = int(self.zona.radio)
        self.capa_zona.fill((200, 30, 30, 90))                # todo rojo...
        pygame.draw.circle(self.capa_zona, (0, 0, 0, 0), centro, radio)  # ...menos el círculo
        pantalla.blit(self.capa_zona, (0, 0))
        pygame.draw.circle(pantalla, CELESTE, centro, radio, 3)

    def _dibujar_hud(self, pantalla):
        j = self.jugador
        # Destello rojo al recibir un disparo
        if j.golpe > 0:
            pygame.draw.rect(pantalla, ROJO, (0, 0, ANCHO, ALTO), 10)

        # Información arriba a la izquierda
        zona_actual = self.mapa.zona_en(j.x, j.y)
        lineas = [f"Enemigos: {len(self.enemigos)}",
                  f"Eliminaciones: {self.eliminaciones}",
                  f"Tiempo: {formatear_tiempo(self.tiempo)}",
                  f"Zona: {zona_actual}",
                  f"Fragmentos: {self.fragmentos}"]
        for i, texto in enumerate(lineas):
            dibujar_texto(pantalla, texto, 18, BLANCO, 12, 10 + i * 22,
                          centrado=False, sombra=True, negrita=True)

        # Estado de la zona segura (arriba al centro)
        color = ROJO if self.zona.estado == "reduciendo" else AMARILLO
        dibujar_texto(pantalla, self.zona.texto_estado(), 20, color,
                      ANCHO // 2 - 60, 22, sombra=True, negrita=True)
        if not self.zona.contiene(j.x, j.y):
            dibujar_texto(pantalla, "¡ESTÁS FUERA DE LA ZONA SEGURA!", 24, ROJO,
                          ANCHO // 2 - 60, 52, sombra=True, negrita=True)

        # Barra de vida (abajo a la izquierda)
        pygame.draw.rect(pantalla, (50, 0, 0), (12, ALTO - 38, 240, 24), border_radius=5)
        ancho = int(240 * max(j.vida, 0) / VIDA_JUGADOR)
        color_vida = VERDE if j.vida > 35 else ROJO
        pygame.draw.rect(pantalla, color_vida, (12, ALTO - 38, ancho, 24), border_radius=5)
        pygame.draw.rect(pantalla, BLANCO, (12, ALTO - 38, 240, 24), 2, border_radius=5)
        dibujar_texto(pantalla, f"VIDA {int(j.vida)}", 16, BLANCO, 132, ALTO - 26, negrita=True)

        # Munición (abajo a la derecha)
        texto_municion = f"{j.cargador} / {j.reserva}"
        ancho_texto = fuente(34, True).size(texto_municion)[0]
        dibujar_texto(pantalla, texto_municion, 34, BLANCO,
                      ANCHO - 20 - ancho_texto, ALTO - 52, centrado=False,
                      sombra=True, negrita=True)
        if j.recargando:
            avance = 1 - j.t_recarga / TIEMPO_RECARGA
            dibujar_texto(pantalla, "RECARGANDO...", 18, AMARILLO,
                          ANCHO - 100, ALTO - 75, sombra=True, negrita=True)
            pygame.draw.rect(pantalla, (60, 60, 60), (ANCHO - 200, ALTO - 62, 180, 6))
            pygame.draw.rect(pantalla, AMARILLO, (ANCHO - 200, ALTO - 62, int(180 * avance), 6))
        elif j.cargador == 0 and j.reserva == 0:
            dibujar_texto(pantalla, "¡SIN MUNICIÓN!", 18, ROJO,
                          ANCHO - 100, ALTO - 75, sombra=True, negrita=True)

        self._dibujar_minimapa(pantalla)

        # Mira
        mx, my = pygame.mouse.get_pos()
        pygame.draw.circle(pantalla, BLANCO, (mx, my), 10, 2)
        pygame.draw.line(pantalla, BLANCO, (mx - 15, my), (mx - 5, my), 2)
        pygame.draw.line(pantalla, BLANCO, (mx + 5, my), (mx + 15, my), 2)
        pygame.draw.line(pantalla, BLANCO, (mx, my - 15), (mx, my - 5), 2)
        pygame.draw.line(pantalla, BLANCO, (mx, my + 5), (mx, my + 15), 2)

    def _dibujar_minimapa(self, pantalla):
        ancho, alto = self.mapa.mini.get_size()
        x0, y0 = ANCHO - ancho - 10, 10
        esc = ancho / MUNDO_ANCHO
        pantalla.blit(self.mapa.mini, (x0, y0))
        pantalla.set_clip(pygame.Rect(x0, y0, ancho, alto))      # no dibujar afuera
        centro = (x0 + int(self.zona.cx * esc), y0 + int(self.zona.cy * esc))
        pygame.draw.circle(pantalla, CELESTE, centro, max(2, int(self.zona.radio * esc)), 2)
        pygame.draw.circle(pantalla, AZUL,
                           (x0 + int(self.jugador.x * esc), y0 + int(self.jugador.y * esc)), 4)
        pygame.draw.circle(pantalla, BLANCO,
                           (x0 + int(self.jugador.x * esc), y0 + int(self.jugador.y * esc)), 4, 1)
        pantalla.set_clip(None)
        pygame.draw.rect(pantalla, BLANCO, (x0, y0, ancho, alto), 2)


# =====================================================================
# 7. JUEGO (pantallas y menús)
# =====================================================================
HISTORIA = [
    "Año 2045. Nova-7, una de las ciudades más avanzadas del mundo, creó una "
    "fuente de energía llamada Núcleo, capaz de cambiar el futuro de la humanidad.",
    "Una falla provocó una catástrofe y Nova-7 quedó destruida. El Núcleo se "
    "dividió en fragmentos que quedaron esparcidos por toda la ciudad.",
    "Distintos grupos comenzaron a entrar en Nova-7 para conseguirlos, y la "
    "ciudad se convirtió en una zona de batalla.",
    "Tu misión: sobrevivir, conseguir recursos y enfrentarte a los demás para "
    "convertirte en el último en pie.",
]


class Juego:
    """Controla en qué pantalla estamos: login, menú, mapa, historia, etc."""

    def __init__(self):
        pygame.init()
        pygame.display.set_caption("ZONA CERO - Battle Royale")
        self.pantalla = pygame.display.set_mode((ANCHO, ALTO))
        self.reloj = pygame.time.Clock()
        self.fondo = crear_fondo()
        self.mapa = Mapa()
        self.partida = None
        self.resumen = {}
        self.ajustes = {"dificultad": 1, "mostrar_fps": False}
        self.estado = "login"
        self.tiempo = 0.0

        self._crear_pantalla_login()
        self._crear_botones()

    # ---------- Preparación de pantallas ----------
    def _crear_pantalla_login(self):
        self.campos = ["", ""]                       # correo, contraseña
        self.campo_activo = 0
        self.mensaje_login = ""
        self.rect_correo = pygame.Rect(0, 0, 400, 44)
        self.rect_correo.center = (ANCHO // 2, 280)
        self.rect_clave = pygame.Rect(0, 0, 400, 44)
        self.rect_clave.center = (ANCHO // 2, 370)
        self.boton_login = Boton("Iniciar sesión", ANCHO // 2, 460, 260, 50,
                                 (30, 100, 60), (50, 150, 90))

    def _crear_botones(self):
        # Menú principal
        nombres = ["JUGAR", "MAPA", "HISTORIA", "CONFIGURACIÓN", "SALIR"]
        self.botones_menu = {
            n: Boton(n, ANCHO // 2, 270 + i * 62, 300, 50)
            for i, n in enumerate(nombres)
        }
        # Botón para volver (mapa, historia, configuración)
        self.boton_volver = Boton("VOLVER", ANCHO // 2, ALTO - 50, 220, 46)
        self.boton_volver_mapa = Boton("VOLVER", 850, ALTO - 50, 170, 46)
        # Configuración
        self.boton_dificultad = Boton("", ANCHO // 2, 270, 420, 54)
        self.boton_fps = Boton("", ANCHO // 2, 350, 420, 54)
        # Victoria / derrota
        self.boton_lobby = Boton("VOLVER AL LOBBY", ANCHO // 2, ALTO - 70, 320, 54,
                                 (30, 100, 60), (50, 150, 90))

    def cambiar_estado(self, nuevo):
        self.estado = nuevo
        pygame.mouse.set_visible(nuevo != "partida")     # en la partida hay una mira propia

    # ---------- Bucle principal ----------
    def ejecutar(self):
        while True:
            dt = min(self.reloj.tick(FPS) / 1000, 0.05)
            self.tiempo += dt
            for evento in pygame.event.get():
                if evento.type == pygame.QUIT:
                    self.salir()
                self.manejar_evento(evento)
            self.actualizar(dt)
            self.dibujar()
            pygame.display.flip()

    def salir(self):
        pygame.quit()
        sys.exit()

    # ---------- Eventos ----------
    def manejar_evento(self, e):
        if self.estado == "login":
            self._evento_login(e)
        elif self.estado == "menu":
            self._evento_menu(e)
        elif self.estado == "mapa":
            if self.boton_volver_mapa.fue_clickeado(e):
                self.cambiar_estado("menu")
        elif self.estado == "historia":
            if self.boton_volver.fue_clickeado(e):
                self.cambiar_estado("menu")
        elif self.estado == "config":
            self._evento_config(e)
        elif self.estado == "partida":
            if self.partida.manejar_evento(e) == "abandonar":
                self.partida = None
                self.cambiar_estado("menu")
        elif self.estado in ("victoria", "derrota"):
            if self.boton_lobby.fue_clickeado(e):
                self.cambiar_estado("menu")

    def _evento_login(self, e):
        if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            if self.rect_correo.collidepoint(e.pos):
                self.campo_activo = 0
            elif self.rect_clave.collidepoint(e.pos):
                self.campo_activo = 1
        if self.boton_login.fue_clickeado(e):
            self.intentar_login()
        if e.type == pygame.KEYDOWN:
            if e.key == pygame.K_TAB:
                self.campo_activo = 1 - self.campo_activo
            elif e.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                if self.campo_activo == 0:
                    self.campo_activo = 1
                else:
                    self.intentar_login()
            elif e.key == pygame.K_BACKSPACE:
                self.campos[self.campo_activo] = self.campos[self.campo_activo][:-1]
            elif e.unicode and e.unicode.isprintable() and len(self.campos[self.campo_activo]) < 30:
                self.campos[self.campo_activo] += e.unicode

    def intentar_login(self):
        """Compara lo escrito con los datos correctos."""
        correo, clave = self.campos[0].strip(), self.campos[1]
        if correo == CORREO_CORRECTO and clave == CONTRASENA_CORRECTA:
            self.mensaje_login = ""
            self.cambiar_estado("menu")
        else:
            self.mensaje_login = "Correo o contraseña incorrectos"
            self.campos[1] = ""
            self.campo_activo = 1

    def _evento_menu(self, e):
        if self.botones_menu["JUGAR"].fue_clickeado(e):
            self.iniciar_partida()
        elif self.botones_menu["MAPA"].fue_clickeado(e):
            self.cambiar_estado("mapa")
        elif self.botones_menu["HISTORIA"].fue_clickeado(e):
            self.cambiar_estado("historia")
        elif self.botones_menu["CONFIGURACIÓN"].fue_clickeado(e):
            self.cambiar_estado("config")
        elif self.botones_menu["SALIR"].fue_clickeado(e):
            self.salir()

    def _evento_config(self, e):
        if self.boton_dificultad.fue_clickeado(e):
            self.ajustes["dificultad"] = (self.ajustes["dificultad"] + 1) % len(DIFICULTADES)
        elif self.boton_fps.fue_clickeado(e):
            self.ajustes["mostrar_fps"] = not self.ajustes["mostrar_fps"]
        elif self.boton_volver.fue_clickeado(e):
            self.cambiar_estado("menu")

    # ---------- Partida ----------
    def iniciar_partida(self):
        _, enemigos, dano = DIFICULTADES[self.ajustes["dificultad"]]
        self.partida = Partida(self.mapa, enemigos, dano)
        self.cambiar_estado("partida")

    def actualizar(self, dt):
        if self.estado == "partida":
            self.partida.actualizar(dt)
            if self.partida.resultado:
                p = self.partida
                self.resumen = {
                    "eliminaciones": p.eliminaciones,
                    "dano": int(p.dano_realizado),
                    "tiempo": p.tiempo,
                }
                resultado = p.resultado
                self.partida = None
                self.cambiar_estado(resultado)

    # ---------- Dibujo ----------
    def dibujar(self):
        if self.estado == "partida":
            self.partida.dibujar(self.pantalla)
            if self.ajustes["mostrar_fps"]:
                dibujar_texto(self.pantalla, f"FPS: {int(self.reloj.get_fps())}", 16,
                              BLANCO, ANCHO // 2, ALTO - 14, sombra=True)
            return
        self.pantalla.blit(self.fondo, (0, 0))
        if self.estado == "login":
            self._dibujar_login()
        elif self.estado == "menu":
            self._dibujar_menu()
        elif self.estado == "mapa":
            self._dibujar_mapa()
        elif self.estado == "historia":
            self._dibujar_historia()
        elif self.estado == "config":
            self._dibujar_config()
        elif self.estado == "victoria":
            self._dibujar_victoria()
        elif self.estado == "derrota":
            self._dibujar_derrota()

    def _dibujar_titulo(self, y=110):
        dibujar_texto(self.pantalla, "ZONA CERO", 84, NARANJA, ANCHO // 2, y,
                      negrita=True, sombra=True)
        dibujar_texto(self.pantalla, "BATTLE ROYALE", 28, BLANCO, ANCHO // 2, y + 60,
                      negrita=True)

    def _dibujar_login(self):
        p = self.pantalla
        self._dibujar_titulo(90)
        dibujar_texto(p, "Correo", 20, GRIS, self.rect_correo.left, self.rect_correo.top - 16,
                      centrado=False)
        dibujar_texto(p, "Contraseña", 20, GRIS, self.rect_clave.left, self.rect_clave.top - 16,
                      centrado=False)
        for i, rect in enumerate((self.rect_correo, self.rect_clave)):
            pygame.draw.rect(p, (25, 30, 42), rect, border_radius=6)
            color_borde = CELESTE if i == self.campo_activo else GRIS
            pygame.draw.rect(p, color_borde, rect, 2, border_radius=6)
            texto = self.campos[i] if i == 0 else "*" * len(self.campos[i])
            if i == self.campo_activo and int(self.tiempo * 2) % 2 == 0:
                texto += "|"
            dibujar_texto(p, texto, 24, BLANCO, rect.left + 12, rect.centery - 14,
                          centrado=False)
        self.boton_login.dibujar(p)
        if self.mensaje_login:
            dibujar_texto(p, self.mensaje_login, 22, ROJO, ANCHO // 2, 525, negrita=True)
        dibujar_texto(p, "TAB: cambiar de campo   ENTER: continuar", 16, GRIS,
                      ANCHO // 2, ALTO - 25)

    def _dibujar_menu(self):
        self._dibujar_titulo(110)
        for boton in self.botones_menu.values():
            boton.dibujar(self.pantalla)

    def _dibujar_mapa(self):
        p = self.pantalla
        dibujar_texto(p, "MAPA DE NOVA-7", 34, NARANJA, 380, 32, negrita=True)
        imagen = pygame.transform.smoothscale(self.mapa.superficie, (720, 560))
        p.blit(imagen, (20, 62))
        pygame.draw.rect(p, BLANCO, (20, 62, 720, 560), 2)
        dibujar_texto(p, "ZONAS", 24, BLANCO, 850, 90, negrita=True)
        for i, (nombre, _, color) in enumerate(self.mapa.zonas):
            y = 135 + i * 44
            pygame.draw.rect(p, color, (765, y - 12, 24, 24))
            pygame.draw.rect(p, BLANCO, (765, y - 12, 24, 24), 2)
            dibujar_texto(p, f"{i + 1}. {nombre}", 17, BLANCO, 798, y - 10, centrado=False)
        self.boton_volver_mapa.dibujar(p)

    def _dibujar_historia(self):
        p = self.pantalla
        dibujar_texto(p, "HISTORIA", 50, NARANJA, ANCHO // 2, 60, negrita=True, sombra=True)
        y = 120
        for parrafo in HISTORIA:
            y = dibujar_parrafo(p, parrafo, 22, BLANCO, 90, y, ANCHO - 180) + 14
        dibujar_texto(p, "Controles: W A S D moverse · Mouse apuntar · Click disparar · "
                         "R recargar · ESC salir", 17, CELESTE, ANCHO // 2, ALTO - 110)
        self.boton_volver.dibujar(p)

    def _dibujar_config(self):
        p = self.pantalla
        dibujar_texto(p, "CONFIGURACIÓN", 50, NARANJA, ANCHO // 2, 80, negrita=True, sombra=True)
        nombre_dif = DIFICULTADES[self.ajustes["dificultad"]][0]
        cantidad = DIFICULTADES[self.ajustes["dificultad"]][1]
        self.boton_dificultad.texto = f"Dificultad: {nombre_dif}"
        self.boton_fps.texto = "Mostrar FPS: " + ("SÍ" if self.ajustes["mostrar_fps"] else "NO")
        self.boton_dificultad.dibujar(p)
        self.boton_fps.dibujar(p)
        dibujar_texto(p, f"Con esta dificultad habrá {cantidad} enemigos en la partida.",
                      18, GRIS, ANCHO // 2, 405)
        self.boton_volver.dibujar(p)

    def _dibujar_victoria(self):
        p = self.pantalla
        dibujar_texto(p, "¡VICTORIA!", 110, AMARILLO, ANCHO // 2, 130, negrita=True, sombra=True)
        dibujar_texto(p, "EL ÚLTIMO EN PIE", 44, BLANCO, ANCHO // 2, 215, negrita=True)
        datos = [f"Eliminaciones: {self.resumen['eliminaciones']}",
                 f"Tiempo de partida: {formatear_tiempo(self.resumen['tiempo'])}",
                 "Jugadores restantes: 1"]
        for i, texto in enumerate(datos):
            dibujar_texto(p, texto, 30, BLANCO, ANCHO // 2, 315 + i * 50)
        self.boton_lobby.dibujar(p)

    def _dibujar_derrota(self):
        p = self.pantalla
        dibujar_texto(p, "DERROTA", 110, ROJO, ANCHO // 2, 130, negrita=True, sombra=True)
        dibujar_texto(p, "Eliminado. Inténtalo de nuevo.", 34, BLANCO, ANCHO // 2, 215)
        datos = [f"Eliminaciones: {self.resumen['eliminaciones']}",
                 f"Daño realizado: {self.resumen['dano']}",
                 f"Tiempo de partida: {formatear_tiempo(self.resumen['tiempo'])}"]
        for i, texto in enumerate(datos):
            dibujar_texto(p, texto, 30, BLANCO, ANCHO // 2, 315 + i * 50)
        self.boton_lobby.dibujar(p)


# =====================================================================
# PUNTO DE ENTRADA
# =====================================================================
if __name__ == "__main__":
    Juego().ejecutar()
