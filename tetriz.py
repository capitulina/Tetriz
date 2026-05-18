"""
Tetris didatico — rotacao de peca com matrizes 2D (homogeneas 3x3).

Passo usado ao apertar W (girar):
  1) T(-px, -py)  leva o ponto (e o centro de rotacao) para a origem
  2) R(90°)       gira em torno da origem
  3) T(px, py)    devolve para a posicao do pivô na grade

M_total = T_volta @ R @ T_ida
"""

import pygame
import numpy as np
import math
import random

pygame.init()

COLUNAS = 10
LINHAS = 20
TAMANHO_CELULA = 36
PAINEL_LARGURA = 220
MARGEM = 20
TOPO = 60

LARGURA_GRADE = COLUNAS * TAMANHO_CELULA
LARGURA = LARGURA_GRADE + PAINEL_LARGURA + MARGEM * 3
ALTURA = LINHAS * TAMANHO_CELULA + TOPO + MARGEM * 2

# Paleta de cores refinada
BG_ESCURO      = (10, 10, 14)
BG_PAINEL      = (18, 18, 26)
BG_GRADE       = (14, 14, 20)
LINHA_GRADE    = (28, 28, 42)
BORDA_PAINEL   = (45, 45, 70)
BORDA_GRADE    = (55, 55, 85)
AZUL_ACENTO    = (80, 160, 255)
AZUL_ESCURO    = (20, 40, 80)
TEXTO_PRIMARIO = (220, 220, 235)
TEXTO_SEC      = (120, 120, 155)
TEXTO_DIM      = (60, 60, 85)
VERDE_ACENTO   = (60, 220, 130)
LARANJA_ACENTO = (255, 160, 50)
VERMELHO_ACENTO= (255, 80, 80)
BRANCO_SUAVE   = (200, 200, 215)

# Cores das peças — mais saturadas e vibrantes
CORES_PECAS = [
    (50, 190, 255),   # I — ciano
    (255, 200, 50),   # O — amarelo
    (170, 90, 255),   # T — roxo
    (60, 220, 130),   # S — verde
    (255, 100, 100),  # Z — vermelho
    (255, 150, 50),   # L — laranja
    (80, 130, 255),   # J — azul
]

FORMAS = [
    [(0, 0), (1, 0), (2, 0), (3, 0)],
    [(0, 0), (0, 1), (1, 0), (1, 1)],
    [(0, 0), (1, 0), (2, 0), (1, 1)],
    [(0, 0), (0, 1), (1, 1), (2, 1)],
    [(1, 0), (2, 0), (0, 1), (1, 1)],
    [(0, 0), (0, 1), (0, 2), (1, 2)],
    [(1, 0), (1, 1), (1, 2), (0, 2)],
]

NOMES_PECAS = ["I", "O", "T", "S", "Z", "L", "J"]

tela = pygame.display.set_mode((LARGURA, ALTURA))
pygame.display.set_caption("Tetris — Rotação por Matrizes")
clock = pygame.time.Clock()

fonte_titulo    = pygame.font.SysFont("consolas", 26, bold=True)
fonte_subtitulo = pygame.font.SysFont("consolas", 13)
fonte_secao     = pygame.font.SysFont("consolas", 13, bold=True)
fonte_corpo     = pygame.font.SysFont("consolas", 14)
fonte_mono      = pygame.font.SysFont("consolas", 12)
fonte_pontos    = pygame.font.SysFont("consolas", 38, bold=True)
fonte_menu      = pygame.font.SysFont("consolas", 56, bold=True)
fonte_badge     = pygame.font.SysFont("consolas", 16, bold=True)
fonte_nivel     = pygame.font.SysFont("consolas", 22, bold=True)

grade_fixa = [[None for _ in range(COLUNAS)] for _ in range(LINHAS)]


# ─── Matrizes ────────────────────────────────────────────────────────────────

def matriz_translacao_2d(tx, ty):
    return np.array([[1., 0., tx], [0., 1., ty], [0., 0., 1.]], dtype=float)

def matriz_rotacao_2d(graus):
    rad = math.radians(graus)
    c, s = math.cos(rad), math.sin(rad)
    return np.array([[c, -s, 0.], [s, c, 0.], [0., 0., 1.]], dtype=float)

def aplicar_matriz_3x3(matriz, x, y):
    v = np.array([x, y, 1.], dtype=float)
    r = matriz @ v
    return r[0], r[1]

def matriz_rotacao_ao_redor(px, py, graus=90):
    t_ida   = matriz_translacao_2d(-px, -py)
    rotacao = matriz_rotacao_2d(graus)
    t_volta = matriz_translacao_2d(px, py)
    return t_volta @ rotacao @ t_ida

def rotacionar_celula(x, y, pivo_x, pivo_y, graus=90):
    m = matriz_rotacao_ao_redor(pivo_x, pivo_y, graus)
    xf, yf = aplicar_matriz_3x3(m, x, y)
    return int(round(xf)), int(round(yf))


# ─── Peça ────────────────────────────────────────────────────────────────────

class Peca:
    def __init__(self, forma_idx=None):
        self.forma_idx = forma_idx if forma_idx is not None else random.randrange(len(FORMAS))
        self.offsets = [list(c) for c in FORMAS[self.forma_idx]]
        self.cor = CORES_PECAS[self.forma_idx]
        self.nome = NOMES_PECAS[self.forma_idx]
        self.px = COLUNAS // 2 - 1
        self.py = 0

    def celulas(self):
        return [(self.px + dx, self.py + dy) for dx, dy in self.offsets]

    def rotacionar(self):
        novos = []
        for dx, dy in self.offsets:
            rx, ry = rotacionar_celula(self.px + dx, self.py + dy, self.px, self.py, 90)
            novos.append([rx - self.px, ry - self.py])
        if colide([(self.px + dx, self.py + dy) for dx, dy in novos], grade_fixa):
            return False
        self.offsets = novos
        return True

    def mover(self, dx, dy):
        self.px += dx
        self.py += dy
        if colide(self.celulas(), grade_fixa):
            self.px -= dx
            self.py -= dy
            return False
        return True


# ─── Lógica ──────────────────────────────────────────────────────────────────

def colide(celulas, grade):
    for x, y in celulas:
        if x < 0 or x >= COLUNAS or y >= LINHAS:
            return True
        if y >= 0 and grade[y][x] is not None:
            return True
    return False

def fixar_peca(peca, grade):
    for x, y in peca.celulas():
        if 0 <= y < LINHAS and 0 <= x < COLUNAS:
            grade[y][x] = peca.cor

def limpar_linhas(grade):
    removidas = 0
    y = LINHAS - 1
    while y >= 0:
        if all(grade[y][x] is not None for x in range(COLUNAS)):
            del grade[y]
            grade.insert(0, [None for _ in range(COLUNAS)])
            removidas += 1
        else:
            y -= 1
    return removidas

def nova_peca():
    p = Peca()
    return None if colide(p.celulas(), grade_fixa) else p

def reiniciar_partida():
    global grade_fixa
    grade_fixa = [[None for _ in range(COLUNAS)] for _ in range(LINHAS)]
    prox = Peca(random.randrange(len(FORMAS)))
    return nova_peca(), prox, 0, 0, 0.0

def calcular_sombra(peca):
    """Calcula onde a peça vai cair (ghost piece)."""
    dy = 0
    while not colide([(x, y + dy + 1) for x, y in peca.celulas()], grade_fixa):
        dy += 1
    return dy


# ─── Desenho: utilitários ─────────────────────────────────────────────────────

def cor_clara(cor, fator=0.3):
    return tuple(min(255, int(c + (255 - c) * fator)) for c in cor)

def cor_escura(cor, fator=0.35):
    return tuple(int(c * (1 - fator)) for c in cor)

def desenhar_rect_borda(surface, cor, rect, borda_cor, raio=4, espessura=1):
    pygame.draw.rect(surface, cor, rect, border_radius=raio)
    pygame.draw.rect(surface, borda_cor, rect, width=espessura, border_radius=raio)

def texto_centralizado(surface, texto, fonte, cor, cx, cy):
    s = fonte.render(texto, True, cor)
    surface.blit(s, s.get_rect(center=(cx, cy)))

def linha_separadora(surface, x1, y, x2, cor=BORDA_PAINEL):
    pygame.draw.line(surface, cor, (x1, y), (x2, y), 1)


# ─── Desenho: grade ───────────────────────────────────────────────────────────

def origem_grade():
    return MARGEM, TOPO + MARGEM // 2

def desenhar_fundo_grade():
    ox, oy = origem_grade()
    bg = pygame.Rect(ox - 1, oy - 1, LARGURA_GRADE + 2, LINHAS * TAMANHO_CELULA + 2)
    pygame.draw.rect(tela, BG_GRADE, bg)
    pygame.draw.rect(tela, BORDA_GRADE, bg, width=1)

    for gx in range(1, COLUNAS):
        x = ox + gx * TAMANHO_CELULA
        pygame.draw.line(tela, LINHA_GRADE, (x, oy), (x, oy + LINHAS * TAMANHO_CELULA))
    for gy in range(1, LINHAS):
        y = oy + gy * TAMANHO_CELULA
        pygame.draw.line(tela, LINHA_GRADE, (ox, y), (ox + LARGURA_GRADE, y))

def desenhar_celula(cx, cy, cor, alpha=255, ghost=False):
    if cy < 0:
        return
    ox, oy = origem_grade()
    tc = TAMANHO_CELULA
    rect = pygame.Rect(ox + cx * tc + 1, oy + cy * tc + 1, tc - 2, tc - 2)

    if ghost:
        surface = pygame.Surface((tc - 2, tc - 2), pygame.SRCALPHA)
        pygame.draw.rect(surface, (*cor, 55), (0, 0, tc - 2, tc - 2), border_radius=2)
        pygame.draw.rect(surface, (*cor, 130), (0, 0, tc - 2, tc - 2), width=1, border_radius=2)
        tela.blit(surface, rect.topleft)
        return

    # Corpo principal
    pygame.draw.rect(tela, cor, rect, border_radius=2)
    # Brilho superior esquerdo
    brilho = cor_clara(cor, 0.25)
    pygame.draw.line(tela, brilho, rect.topleft, (rect.right - 2, rect.top), 1)
    pygame.draw.line(tela, brilho, rect.topleft, (rect.left, rect.bottom - 2), 1)
    # Sombra inferior direita
    sombra = cor_escura(cor, 0.4)
    pygame.draw.line(tela, sombra, (rect.left + 1, rect.bottom - 1), (rect.right - 1, rect.bottom - 1), 1)
    pygame.draw.line(tela, sombra, (rect.right - 1, rect.top + 1), (rect.right - 1, rect.bottom - 1), 1)

def desenhar_peca_miniatura(surface, peca, cx, cy, tamanho=14):
    """Desenha uma peça em miniatura (para próxima peça)."""
    offsets = peca.offsets
    xs = [o[0] for o in offsets]
    ys = [o[1] for o in offsets]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    w = (max_x - min_x + 1) * tamanho
    h = (max_y - min_y + 1) * tamanho
    ox = cx - w // 2
    oy = cy - h // 2

    for dx, dy in offsets:
        x = ox + (dx - min_x) * tamanho
        y = oy + (dy - min_y) * tamanho
        rect = pygame.Rect(x, y, tamanho - 1, tamanho - 1)
        pygame.draw.rect(surface, peca.cor, rect, border_radius=2)
        brilho = cor_clara(peca.cor, 0.2)
        pygame.draw.line(surface, brilho, rect.topleft, (rect.right - 1, rect.top), 1)
        pygame.draw.line(surface, brilho, rect.topleft, (rect.left, rect.bottom - 1), 1)


# ─── Desenho: painel ─────────────────────────────────────────────────────────

def painel_rect():
    ox = MARGEM + LARGURA_GRADE + MARGEM
    oy = TOPO + MARGEM // 2
    return pygame.Rect(ox, oy, PAINEL_LARGURA, LINHAS * TAMANHO_CELULA)

def desenhar_painel(pontos, nivel, linhas, peca, proxima_peca, ultima_rotacao_ok):
    pr = painel_rect()
    px = pr.x
    py = pr.y

    # Card de pontos
    card_pts = pygame.Rect(px, py, pr.width, 80)
    desenhar_rect_borda(tela, BG_PAINEL, card_pts, BORDA_PAINEL, raio=6)
    rotulo = fonte_secao.render("PONTUAÇÃO", True, TEXTO_SEC)
    tela.blit(rotulo, (px + 14, py + 12))
    s_pts = fonte_pontos.render(f"{pontos:,}", True, AZUL_ACENTO)
    tela.blit(s_pts, (px + 14, py + 30))

    # Card nível / linhas
    y_lvl = card_pts.bottom + 10
    card_lvl = pygame.Rect(px, y_lvl, pr.width, 64)
    desenhar_rect_borda(tela, BG_PAINEL, card_lvl, BORDA_PAINEL, raio=6)

    larg_metade = (pr.width - 6) // 2
    # Nível
    cx_n = px + larg_metade // 2
    rot_n = fonte_secao.render("NÍVEL", True, TEXTO_SEC)
    tela.blit(rot_n, rot_n.get_rect(center=(cx_n, y_lvl + 14)))
    s_lvl = fonte_nivel.render(str(nivel), True, VERDE_ACENTO)
    tela.blit(s_lvl, s_lvl.get_rect(center=(cx_n, y_lvl + 42)))
    # Divisor vertical
    pygame.draw.line(tela, BORDA_PAINEL,
                     (px + larg_metade + 3, y_lvl + 10),
                     (px + larg_metade + 3, y_lvl + 54), 1)
    # Linhas
    cx_l = px + larg_metade + 3 + larg_metade // 2 + 3
    rot_l = fonte_secao.render("LINHAS", True, TEXTO_SEC)
    tela.blit(rot_l, rot_l.get_rect(center=(cx_l, y_lvl + 14)))
    s_lin = fonte_nivel.render(str(linhas), True, LARANJA_ACENTO)
    tela.blit(s_lin, s_lin.get_rect(center=(cx_l, y_lvl + 42)))

    # Card próxima peça
    y_prox = card_lvl.bottom + 10
    card_prox = pygame.Rect(px, y_prox, pr.width, 90)
    desenhar_rect_borda(tela, BG_PAINEL, card_prox, BORDA_PAINEL, raio=6)
    rot_pr = fonte_secao.render("PRÓXIMA", True, TEXTO_SEC)
    tela.blit(rot_pr, (px + 14, y_prox + 10))
    if proxima_peca:
        desenhar_peca_miniatura(tela, proxima_peca, px + pr.width // 2, y_prox + 60)

    # Card pivô / rotação
    y_pivo = card_prox.bottom + 10
    card_pivo = pygame.Rect(px, y_pivo, pr.width, 72)
    desenhar_rect_borda(tela, BG_PAINEL, card_pivo, BORDA_PAINEL, raio=6)
    rot_pv = fonte_secao.render("PIVÔ DA ROTAÇÃO", True, TEXTO_SEC)
    tela.blit(rot_pv, (px + 14, y_pivo + 10))
    if peca:
        cor_pivo = VERDE_ACENTO if ultima_rotacao_ok else VERMELHO_ACENTO
        s_px = fonte_corpo.render(f"px = {peca.px}   py = {peca.py}", True, cor_pivo)
        tela.blit(s_px, (px + 14, y_pivo + 30))
        s_pec = fonte_mono.render(f"Peça: {peca.nome}", True, TEXTO_SEC)
        tela.blit(s_pec, (px + 14, y_pivo + 50))

    # Card controles
    y_ctrl = card_pivo.bottom + 10
    ctrl_items = [("W", "Girar"), ("A", "Esquerda"), ("D", "Direita"), ("S", "Descer")]
    altura_ctrl = 18 + len(ctrl_items) * 22 + 10
    card_ctrl = pygame.Rect(px, y_ctrl, pr.width, altura_ctrl)
    if card_ctrl.bottom <= pr.bottom:
        desenhar_rect_borda(tela, BG_PAINEL, card_ctrl, BORDA_PAINEL, raio=6)
        rot_ct = fonte_secao.render("CONTROLES", True, TEXTO_SEC)
        tela.blit(rot_ct, (px + 14, y_ctrl + 8))
        for i, (tecla, desc) in enumerate(ctrl_items):
            y_k = y_ctrl + 26 + i * 22
            badge = pygame.Rect(px + 10, y_k, 22, 18)
            pygame.draw.rect(tela, AZUL_ESCURO, badge, border_radius=3)
            pygame.draw.rect(tela, AZUL_ACENTO, badge, width=1, border_radius=3)
            t_tec = fonte_mono.render(tecla, True, AZUL_ACENTO)
            tela.blit(t_tec, t_tec.get_rect(center=badge.center))
            t_desc = fonte_mono.render(desc, True, TEXTO_SEC)
            tela.blit(t_desc, (px + 38, y_k + 2))


# ─── Desenho: topo ───────────────────────────────────────────────────────────

def desenhar_topo():
    pygame.draw.rect(tela, BG_PAINEL, (0, 0, LARGURA, TOPO))
    pygame.draw.line(tela, BORDA_PAINEL, (0, TOPO - 1), (LARGURA, TOPO - 1), 1)

    titulo = fonte_titulo.render("TETRIS", True, AZUL_ACENTO)
    sub    = fonte_subtitulo.render("rotação por matrizes homogêneas 2D", True, TEXTO_SEC)
    tela.blit(titulo, (MARGEM, 10))
    tela.blit(sub, (MARGEM + 2, 38))

    # Badge M = pausa
    badge_m = pygame.Rect(LARGURA - 110, 14, 80, 26)
    pygame.draw.rect(tela, AZUL_ESCURO, badge_m, border_radius=5)
    pygame.draw.rect(tela, BORDA_PAINEL, badge_m, width=1, border_radius=5)
    t_m = fonte_mono.render("M  pausar", True, TEXTO_DIM)
    tela.blit(t_m, t_m.get_rect(center=badge_m.center))


# ─── Tela inicial ─────────────────────────────────────────────────────────────

def desenhar_tela_inicial():
    tela.fill(BG_ESCURO)

    # Grade de fundo decorativa
    for gx in range(0, LARGURA, 36):
        pygame.draw.line(tela, (20, 20, 30), (gx, 0), (gx, ALTURA))
    for gy in range(0, ALTURA, 36):
        pygame.draw.line(tela, (20, 20, 30), (0, gy), (LARGURA, gy))

    # Logo
    cx = LARGURA // 2
    s_t = fonte_menu.render("TETRIS", True, AZUL_ACENTO)
    tela.blit(s_t, s_t.get_rect(center=(cx, ALTURA // 2 - 185)))

    # Subtítulo
    s_sub = fonte_subtitulo.render("Rotação de peças com matrizes 2D homogêneas", True, TEXTO_SEC)
    tela.blit(s_sub, s_sub.get_rect(center=(cx, ALTURA // 2 - 145)))

    # Card de controles
    larg = 360
    card = pygame.Rect(cx - larg // 2, ALTURA // 2 - 115, larg, 210)
    desenhar_rect_borda(tela, BG_PAINEL, card, BORDA_PAINEL, raio=8)

    rotulo = fonte_secao.render("CONTROLES", True, AZUL_ACENTO)
    tela.blit(rotulo, (card.x + 20, card.y + 16))

    linha_separadora(tela, card.x + 12, card.y + 36, card.right - 12)

    ctrl = [("W", "Girar 90°  —  usa matriz R(90°)"),
            ("A", "Mover para a esquerda"),
            ("D", "Mover para a direita"),
            ("S", "Descer mais rápido")]
    for i, (tecla, desc) in enumerate(ctrl):
        y_k = card.y + 48 + i * 40
        badge = pygame.Rect(card.x + 16, y_k, 30, 26)
        pygame.draw.rect(tela, AZUL_ESCURO, badge, border_radius=5)
        pygame.draw.rect(tela, AZUL_ACENTO, badge, width=1, border_radius=5)
        t_tec = fonte_badge.render(tecla, True, AZUL_ACENTO)
        tela.blit(t_tec, t_tec.get_rect(center=badge.center))
        t_desc = fonte_corpo.render(desc, True, BRANCO_SUAVE)
        tela.blit(t_desc, (card.x + 58, y_k + 5))

    # Botão iniciar
    btn = pygame.Rect(cx - larg // 2, card.bottom + 18, larg, 48)
    pygame.draw.rect(tela, AZUL_ACENTO, btn, border_radius=8)
    t_btn = fonte_secao.render("ENTER  ou  ESPAÇO  —  começar", True, BG_ESCURO)
    tela.blit(t_btn, t_btn.get_rect(center=btn.center))


# ─── Overlay de pausa ─────────────────────────────────────────────────────────

def desenhar_overlay_pausa():
    overlay = pygame.Surface((LARGURA, ALTURA), pygame.SRCALPHA)
    overlay.fill((8, 8, 14, 210))
    tela.blit(overlay, (0, 0))

    cx = LARGURA // 2
    larg = 340
    card = pygame.Rect(cx - larg // 2, ALTURA // 2 - 145, larg, 290)
    desenhar_rect_borda(tela, BG_PAINEL, card, BORDA_PAINEL, raio=10)

    s_p = fonte_titulo.render("PAUSADO", True, LARANJA_ACENTO)
    tela.blit(s_p, s_p.get_rect(center=(cx, card.y + 30)))
    linha_separadora(tela, card.x + 16, card.y + 52, card.right - 16)

    rot_c = fonte_secao.render("CONTROLES", True, TEXTO_SEC)
    tela.blit(rot_c, rot_c.get_rect(center=(cx, card.y + 70)))

    ctrl = [("W", "Girar 90°"), ("A", "Esquerda"), ("D", "Direita"), ("S", "Descer")]
    for i, (tecla, desc) in enumerate(ctrl):
        y_k = card.y + 90 + i * 40
        badge = pygame.Rect(cx - 130, y_k, 30, 26)
        pygame.draw.rect(tela, AZUL_ESCURO, badge, border_radius=5)
        pygame.draw.rect(tela, AZUL_ACENTO, badge, width=1, border_radius=5)
        t_tec = fonte_badge.render(tecla, True, AZUL_ACENTO)
        tela.blit(t_tec, t_tec.get_rect(center=badge.center))
        t_desc = fonte_corpo.render(desc, True, BRANCO_SUAVE)
        tela.blit(t_desc, (cx - 88, y_k + 5))

    linha_separadora(tela, card.x + 16, card.bottom - 48, card.right - 16)
    t_ret = fonte_corpo.render("M  ou  ESC  —  retomar jogo", True, TEXTO_SEC)
    tela.blit(t_ret, t_ret.get_rect(center=(cx, card.bottom - 24)))


# ─── Tela de game over ────────────────────────────────────────────────────────

def desenhar_game_over():
    overlay = pygame.Surface((LARGURA, ALTURA), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 160))
    tela.blit(overlay, (0, 0))
    txt1 = fonte_titulo.render("GAME OVER", True, VERMELHO_ACENTO)
    txt2 = fonte_corpo.render("ENTER — jogar de novo", True, BRANCO_SUAVE)
    tela.blit(txt1, txt1.get_rect(center=(LARGURA // 2, ALTURA // 2 - 20)))
    tela.blit(txt2, txt2.get_rect(center=(LARGURA // 2, ALTURA // 2 + 24)))


# ─── Loop principal ───────────────────────────────────────────────────────────

def main():
    estado = "menu"
    pausado = False
    peca = proxima_peca = None
    pontos = nivel = linhas_total = 0
    tempo_queda = 0.0
    ultima_rotacao_ok = True
    rodando = True

    def intervalo_por_nivel(n):
        return max(0.08, 0.55 - n * 0.045)

    while rodando:
        dt = clock.tick(60) / 1000.0

        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                rodando = False
                continue
            if evento.type != pygame.KEYDOWN:
                continue

            if estado == "menu":
                if evento.key in (pygame.K_RETURN, pygame.K_SPACE):
                    peca, proxima_peca, pontos, nivel, tempo_queda = reiniciar_partida()
                    linhas_total = 0
                    ultima_rotacao_ok = True
                    estado = "jogando"
                continue

            if estado == "game_over":
                if evento.key in (pygame.K_RETURN, pygame.K_SPACE):
                    peca, proxima_peca, pontos, nivel, tempo_queda = reiniciar_partida()
                    linhas_total = 0
                    ultima_rotacao_ok = True
                    estado = "jogando"
                continue

            if evento.key in (pygame.K_m, pygame.K_ESCAPE):
                pausado = not pausado
                continue

            if pausado or peca is None:
                continue

            if evento.key == pygame.K_a:
                peca.mover(-1, 0)
            elif evento.key == pygame.K_d:
                peca.mover(1, 0)
            elif evento.key == pygame.K_s:
                peca.mover(0, 1)
            elif evento.key in (pygame.K_w, pygame.K_x):
                ultima_rotacao_ok = peca.rotacionar()

        if estado == "menu":
            desenhar_tela_inicial()
            pygame.display.flip()
            continue

        if not pausado and estado == "jogando" and peca is not None:
            tempo_queda += dt
            if tempo_queda >= intervalo_por_nivel(nivel):
                tempo_queda = 0.0
                if not peca.mover(0, 1):
                    fixar_peca(peca, grade_fixa)
                    removidas = limpar_linhas(grade_fixa)
                    linhas_total += removidas
                    nivel = linhas_total // 10
                    pontos += removidas * 100 * (nivel + 1)
                    peca = proxima_peca
                    proxima_peca = Peca(random.randrange(len(FORMAS)))
                    if peca is None or colide(peca.celulas(), grade_fixa):
                        estado = "game_over"

        # Renderização
        tela.fill(BG_ESCURO)
        desenhar_topo()
        desenhar_fundo_grade()

        ox, oy = origem_grade()

        # Grade fixa
        for y in range(LINHAS):
            for x in range(COLUNAS):
                if grade_fixa[y][x] is not None:
                    desenhar_celula(x, y, grade_fixa[y][x])

        # Sombra (ghost piece)
        if peca is not None and estado == "jogando":
            dy_sombra = calcular_sombra(peca)
            if dy_sombra > 0:
                for x, y in peca.celulas():
                    desenhar_celula(x, y + dy_sombra, peca.cor, ghost=True)

        # Peça ativa
        if peca is not None:
            for x, y in peca.celulas():
                desenhar_celula(x, y, peca.cor)
            # Pivô
            px_tela = ox + peca.px * TAMANHO_CELULA + TAMANHO_CELULA // 2
            py_tela = oy + peca.py * TAMANHO_CELULA + TAMANHO_CELULA // 2
            pygame.draw.circle(tela, BRANCO_SUAVE, (px_tela, py_tela), 4, 2)

        desenhar_painel(pontos, nivel, linhas_total, peca, proxima_peca, ultima_rotacao_ok)

        if estado == "game_over":
            desenhar_game_over()

        if pausado and estado == "jogando":
            desenhar_overlay_pausa()

        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()