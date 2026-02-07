import os
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
import math
import pickle
import random
import time
from math import hypot
from queue import Empty

import pygame

from config import PlayerConfig, TeamConfig, GameConfig
from obstacle import Obstacle

last_positions = {}
player_was_dead = {}


def display_main(
        display_queue,
        lobby_state_queue,
        game_started,
        server_ip,
        calc_couleur,
        to_couleur_queue,
        from_couleur_queue,
        paint_surface_queue,
        prepare_phase,
        prepare_start_time,
        etat_jeu_precedent=False
):
    if not pygame.get_init():
        pygame.init()
    window = pygame.display.set_mode((GameConfig.BASE_WIDTH, GameConfig.BASE_HEIGHT), pygame.RESIZABLE)
    pygame.display.set_caption("Hey c est splatooon eco++")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont(None, 24)

    # Surfaces
    paint_surface = pygame.Surface((GameConfig.BASE_WIDTH, GameConfig.BASE_HEIGHT), pygame.SRCALPHA)
    paint_surface.fill((0, 0, 0, 0))  # transparent au départ

    render_surface = pygame.Surface((GameConfig.BASE_WIDTH, GameConfig.BASE_HEIGHT), pygame.SRCALPHA)

    color_map = TeamConfig.COLOR_MAP
    projectile_color_map = {
        0: (200, 200, 200),
        1: (255, 150, 150),
        2: (150, 150, 255),
    }

    # tentative bricollage pour eviter les lags (spoilers ca fonctionne pas des masses)
    intervalle_couleur = 2.0
    dernier_envoi = time.time()
    ratio_couleur = {0: 0, 1: 0, 2: 0}

    # Intervalle d'envoi de la paint_surface
    intervalle_surface = 0.1  # 100ms
    dernier_envoi_surface = 0

    # QR code pour le lobby
    def generate_qr_code_image(url):
        import pygame
        import qrcode
        from io import BytesIO
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(url)
        qr.make(fit=True)
        img_qr = qr.make_image(fill_color='black', back_color='white').convert('RGB')
        raw_str = BytesIO()
        img_qr.save(raw_str, format='PNG')
        raw_str.seek(0)
        return pygame.image.load(raw_str, 'qr_code.png').convert()

    qr_url = f"http://{server_ip}:8081"
    qr_surf = generate_qr_code_image(qr_url)
    qr_surf = pygame.transform.scale(qr_surf, (200, 200))

    running = True
    last_data = {}
    winner_info = None  # Stocker l'information du gagnant 
    try:
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.VIDEORESIZE:
                    window = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)

            # Récupère l'état (lobby / jeu) si disponible
            try:
                while True:
                    new_data = lobby_state_queue.get_nowait()
                    # Préserver l'information du gagnant si elle existe
                    if "winner" in new_data and new_data.get("show_winner", False):
                        winner_info = new_data["winner"]
                    last_data = new_data
            except Empty:
                pass

            # Récupère le dernier pourcentage de couleurs
            try:
                new_coul = from_couleur_queue.get_nowait()
                ratio_couleur = new_coul
            except Empty:
                pass

            render_surface.fill((0, 0, 0))
            if not game_started.value and etat_jeu_precedent:
                # Affichage du gagnant si présent dans le state
                winner = last_data.get("winner", None)
                if winner:
                    win_font = pygame.font.SysFont(None, 100)
                    txt_win = win_font.render(f"VICTOIRE {winner}", True, (255, 200, 0))
                    txt_rect = txt_win.get_rect(center=(window.get_width() // 2, window.get_height() // 2))
                    render_surface.blit(txt_win, txt_rect)

                print("[Display] Retour en lobby détecté, nettoyage de la peinture.")
                paint_surface.fill((0, 0, 0, 0))  # Surface transparente
                last_positions.clear()
            if game_started.value and not etat_jeu_precedent:
                paint_surface.fill((0, 0, 0, 0))  # Reset début de partie

            etat_jeu_precedent = game_started.value

            # Envoi de la paint_surface au processus de jeu pour détection de couleur
            if game_started.value:
                now = time.time()
                if now - dernier_envoi_surface >= intervalle_surface:
                    try:
                        arr = pygame.surfarray.array3d(paint_surface)
                        paint_surface_queue.put_nowait(arr)
                        dernier_envoi_surface = now
                    except:
                        pass  # Queue pleine, on ignore

            # MODE LOBBY
            if not game_started.value:
                # Affichage du gagnant si présent, même en mode lobby
                if winner_info:
                    win_font = pygame.font.SysFont(None, 100)
                    txt_win = win_font.render(f"VICTOIRE {winner_info}", True, (255, 200, 0))
                    txt_rect = txt_win.get_rect(center=(render_surface.get_width() // 2, render_surface.get_height() // 2 - 150))
                    render_surface.blit(txt_win, txt_rect)
                    
                    # Effacer l'info du gagnant après 5 secondes en mode lobby
                    if time.time() - dernier_envoi_surface > 5:
                        winner_info = None
                # Passez render_surface et window à la fonction render_lobby au lieu de "this"
                render_lobby(window, render_surface, lobby_state_queue, qr_surf, server_ip)

                

            # MODE JEU
            else:

                # Réinitialiser l'info du gagnant quand une nouvelle partie commence
                if not etat_jeu_precedent:
                    winner_info = None

                players_data = last_data.get("players", {})
                # Affichage du décompte centré pendant la phase préparation dans le mode jeu
                if prepare_phase.value:
                    countdown = int(6 - (time.time() - prepare_start_time.value))
                    countdown = max(0, countdown)

                    big_font = pygame.font.SysFont(None, 150)
                    msg = "PREPAREZ VOUS" if countdown > 0 else "GO"
                    msg_surf = big_font.render(msg, True, (255, 200, 0))
                    msg_rect = msg_surf.get_rect(center=(window.get_width() // 2, window.get_height() // 2 - 100))
                    render_surface.blit(msg_surf, msg_rect)

                    if countdown > 0:
                        num_surf = big_font.render(str(countdown), True, (255, 200, 0))
                        num_rect = num_surf.get_rect(center=(window.get_width() // 2, window.get_height() // 2 + 100))
                        render_surface.blit(num_surf, num_rect)

                projectiles_data = last_data.get("projectiles", {})
                obstacles_data = last_data.get("obstacles", [])

                # On colle la paint_surface (traînée) en fond
                render_surface.blit(paint_surface, (0, 0))

                # Mise à jour traînée + joueurs
                for pseudo, info in players_data.items():
                    if not isinstance(info, dict):
                        continue

                    pid = info.get("id", 0)
                    x = int(info.get("x", 0))
                    y = int(info.get("y", 0))
                    r = info.get("radius", PlayerConfig.RADIUS)
                    team = info.get("team", 0)
                    col = color_map.get(team, (255, 255, 255))

                    # Vérifier si le joueur est mort (en respawn)
                    is_dead = info.get("dead", False)
                    respawn_time = info.get("respawn_time", 0)

                    if pseudo in last_positions and not is_dead:
                        # Si le joueur était précédemment mort (marqué dans un dictionnaire)
                        if pseudo in player_was_dead and player_was_dead[pseudo]:
                            # Il vient de réapparaître, on supprime sa dernière position pour éviter la traînée
                            del last_positions[pseudo]
                            player_was_dead[pseudo] = False

                    # Mettre à jour l'état de mort pour le prochain cycle
                    if is_dead:
                        player_was_dead[pseudo] = True

                    if not is_dead:
                        # TRAÎNÉE FLUIDE seulement pour les joueurs vivants
                        if pseudo in last_positions:
                            old_x, old_y = last_positions[pseudo]
                            dist = hypot(x - old_x, y - old_y)
                            steps = int(dist // 6) + 1
                            for i in range(steps):
                                t = i / steps
                                interp_x = old_x + t * (x - old_x)
                                interp_y = old_y + t * (y - old_y)
                                pygame.draw.circle(paint_surface, col, (int(interp_x), int(interp_y)), r)
                        else:
                            pygame.draw.circle(paint_surface, col, (int(x), int(y)), r)

                        last_positions[pseudo] = (x, y)
                        pygame.draw.circle(render_surface, col, (x, y), r)
                        # Contour blanc du joueur
                        pygame.draw.circle(render_surface, (255, 255, 255), (x, y), r, width=2)
                    else:
                        # Si le joueur est en respawn, on dessine une version fantôme semi-transparente
                        ghost_surf = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
                        ghost_col = (col[0], col[1], col[2], 128)  # Version semi-transparente
                        pygame.draw.circle(ghost_surf, ghost_col, (r, r), r)
                        render_surface.blit(ghost_surf, (x - r, y - r))

                        # Afficher le timer de respawn au-dessus
                        time_left = max(0, int(respawn_time - time.time()))
                        if time_left > 0:
                            time_surf = font.render(str(time_left), True, (255, 255, 255))
                            time_rect = time_surf.get_rect(center=(x, y - r - 10))
                            render_surface.blit(time_surf, time_rect)

                    # numéro du joueur centré
                    num_surf = font.render(str(pid), True, (255, 255, 255))
                    num_rect = num_surf.get_rect(center=(x, y))
                    render_surface.blit(num_surf, num_rect)

                    # ---------- BARRE DE VIE ------------------------------------  <<< PATCH HP bar
                    health = info.get("health",0)
                    max_health = PlayerConfig.MAX_HEALTH
                    print(health)

                    if not is_dead:
                        # dimensions
                        bar_w, bar_h = 30, 4
                        # valeur sûre entre 0 et 1
                        try:
                            pct = max(0.0, min(1.0, float(health) / max_health))
                        except Exception:
                            pct = 1.0
                        filled_w = int(bar_w * pct)

                        bx = x - bar_w // 2
                        by = y - r - 12  # 12 px au-dessus du cercle

                        # fond gris
                        pygame.draw.rect(render_surface, (60, 60, 60), (bx, by, bar_w, bar_h))
                        # couleur dynamique vert→rouge
                        col_pv = (int((1 - pct) * 255), int(pct * 255), 0)
                        pygame.draw.rect(render_surface, col_pv, (bx, by, filled_w, bar_h))

                # Projectiles
                for pid, proj in projectiles_data.items():
                    px = proj.get("x", 0)
                    py = proj.get("y", 0)
                    t = proj.get("team", 0)
                    pygame.draw.circle(render_surface, projectile_color_map.get(t, (200, 200, 200)), (int(px), int(py)),
                                       5)

                for obs in obstacles_data:
                    ox = obs.get("x", 0)
                    oy = obs.get("y", 0)
                    ow = obs.get("width", 40)
                    oh = obs.get("height", 40)
                    pygame.draw.rect(render_surface, (100, 100, 100), pygame.Rect(ox, oy, ow, oh))

                # Envoi snapshot pour calcul couleur
                if calc_couleur.value and (time.time() - dernier_envoi) >= intervalle_couleur:
                    arr = pygame.surfarray.array3d(paint_surface)  # Conversion en tableau NumPy
                    to_couleur_queue.put(pickle.dumps(arr))  # Envoi de la surface sérialisée
                    dernier_envoi = time.time()
                   # print("[Display] Snapshot envoyé pour calcul couleur")

                # Barre (en haut) pour afficher le pourcentage
                scoreboard_x, scoreboard_y = 200, 40
                scoreboard_w, scoreboard_h = GameConfig.BASE_WIDTH-400, 20

                fond_barre = pygame.Rect(scoreboard_x - 2, scoreboard_y - 2, scoreboard_w + 4, scoreboard_h + 24)
                pygame.draw.rect(render_surface, (255, 255, 255), fond_barre, border_radius=5)
                pygame.draw.rect(render_surface, (0, 0, 0), fond_barre.inflate(-2, -2), border_radius=5)

                current_x = scoreboard_x
                for tid in sorted(color_map.keys()):
                    ratio = ratio_couleur.get(tid, 0.0)
                    bar_w = int(ratio * scoreboard_w)
                    pygame.draw.rect(render_surface, color_map[tid], (current_x, scoreboard_y, bar_w, scoreboard_h))
                    current_x += bar_w

                info_text = " | ".join([
                    f"T{tid} {int(ratio_couleur[tid] * 100)}%" for tid in sorted(color_map.keys())
                ])
                txt_coul = font.render(info_text, True, (255, 255, 255))
                render_surface.blit(txt_coul, (scoreboard_x + 10, scoreboard_y + scoreboard_h + 2))

                

                titre_jeu = font.render("JEU (traînée + couleurs + projectiles)", True, (0, 255, 0))
                render_surface.blit(titre_jeu, (10, 10))
                # Affichage du gagnant si présent 
                if winner_info:
                    win_font = pygame.font.SysFont(None, 150)
                    txt_win = win_font.render(f"VICTOIRE {winner_info}", True, (255, 200, 0))
                    txt_rect = txt_win.get_rect(center=(window.get_width() // 2, window.get_height() // 2))
                    render_surface.blit(txt_win, txt_rect)

            # Affichage du timer (durée restante) uniquement si le jeu est en cours
            if game_started.value and not prepare_phase.value:
                TEMPS_TOTAL = last_data.get("duration", 60)  # secondes
                start_time = last_data.get("start_time", None)
                if start_time:
                    temps_ecoule = int(time.time() - start_time)
                    temps_restant = max(0, TEMPS_TOTAL - temps_ecoule)
                    minutes = temps_restant // 60
                    secondes = temps_restant % 60

                    # Couleur dynamique du timer (blanc, jaune, rouge)
                    if temps_restant <= 10:
                        couleur_timer = (255, 200, 0)  # orange vif
                    elif temps_restant <= 30:
                        couleur_timer = (255, 255, 0)  # jaune
                    else:
                        couleur_timer = (255, 255, 255)  # blanc

                    # Texte principal du timer
                    txt_timer = font.render(f" Temps : {minutes:02}:{secondes:02}", True, couleur_timer)

                    # Fond noir semi-transparent derrière le timer
                    timer_bg_rect = txt_timer.get_rect()
                    timer_bg_rect.topright = (window.get_width() - 10, 10)
                    timer_bg_rect.inflate_ip(10, 6)
                    s = pygame.Surface(timer_bg_rect.size, pygame.SRCALPHA)
                    s.fill((0, 0, 0, 150))  # Noir transparent
                    render_surface.blit(s, timer_bg_rect.topleft)

                    # Texte du timer
                    render_surface.blit(txt_timer, (timer_bg_rect.x + 5, timer_bg_rect.y + 3))

                    # --- Compte à rebours géant central ---
                    if temps_restant <= 10:
                        # Effet de clignotement pour les 5 dernières secondes
                        clignote = True
                        if temps_restant <= 5:
                            clignote = (int(time.time() * 2) % 2 == 0)  # clignote toutes les 0.5s

                        if clignote:
                            # Taille dynamique (grossit dans les 3 dernières secondes)
                            taille_base = 150
                            taille_zoom = 200
                            taille = taille_base
                            if temps_restant <= 3:
                                taille = taille_zoom

                            grosse_font = pygame.font.SysFont(None, taille)
                            txt_gros = grosse_font.render(str(temps_restant), True, (255, 200, 0))
                            txt_gros.set_alpha(200)  # légère transparence
                            center_x = window.get_width() // 2 - txt_gros.get_width() // 2
                            center_y = window.get_height() // 2 - txt_gros.get_height() // 2
                            render_surface.blit(txt_gros, (center_x, center_y))

            # Scale final
            win_w, win_h = window.get_size()
            scaled_surface = pygame.transform.scale(render_surface, (win_w, win_h))
            window.blit(scaled_surface, (0, 0))

            pygame.display.flip()
            clock.tick(60)
    except KeyboardInterrupt:
        print("[Display] Fermeture propre.")
        pygame.quit()


def render_lobby(window, surface, lobby_state_queue, qr_img, local_ip):
    """
    Fonction de rendu du lobby.

    Args:
        window: Fenêtre Pygame
        surface: Surface sur laquelle dessiner
        lobby_state_queue: Queue pour recevoir l'état du lobby
        qr_img: Image QR code pour rejoindre la partie
        local_ip: Adresse IP locale pour affichage
    """
    # Effacer l'écran avec une couleur de fond
    surface.fill((20, 20, 30))  # Bleu très foncé

    # Polices pour le texte
    title_font = pygame.font.SysFont(None, 72)
    info_font = pygame.font.SysFont(None, 36)
    player_font = pygame.font.SysFont(None, 24)

    # Titre du jeu
    title_text = title_font.render(GameConfig.TITLE, True, (255, 255, 255))
    title_rect = title_text.get_rect(centerx=surface.get_width() // 2, y=30)
    surface.blit(title_text, title_rect)

    # Instruction pour rejoindre
    join_text = info_font.render("Scannez le QR code ou visitez:", True, (220, 220, 220))
    url_text = info_font.render(f"http://{local_ip}:8081", True, (100, 200, 255))

    join_rect = join_text.get_rect(centerx=surface.get_width() // 2, y=100)
    url_rect = url_text.get_rect(centerx=surface.get_width() // 2, y=140)

    surface.blit(join_text, join_rect)
    surface.blit(url_text, url_rect)

    # Récupérer l'état du lobby
    # Utilisation d'un état local persistant
    if not hasattr(render_lobby, "last_players"):
        render_lobby.last_players = {}

    # Mise à jour uniquement si de nouvelles données sont disponibles
    if not lobby_state_queue.empty():
        try:
            render_lobby.last_players = lobby_state_queue.get_nowait()
        except:
            pass

    # Si on reçoit un état de jeu (avec clé "players"), on ne garde que la partie lobby
    raw = render_lobby.last_players

    players = raw["players"] if isinstance(raw, dict) and "players" in raw else raw

    # Calcul dynamique des marges et zones utile
    w,h = surface.get_width(), surface.get_height()
    margin_x      = int(w * 0.05)
    margin_y      = int(h * 0.10)
    usable_width  = w - 2 * margin_x
    usable_height = h - 2 * margin_y

    # Regrouper les joueurs par équipe
    teams = {}
    for pseudo, p_data in players.items():
        if not isinstance(p_data, dict):
            continue
        team = p_data.get("team", 0)
        teams.setdefault(team, []).append((p_data))

    # Dessiner chaque équipe sur une ligne
    team_count = len(teams)
    if team_count != 0:
        block_height = usable_height // team_count

    # Dessiner chaque groupe en grille carrée
    for idx, team in enumerate(sorted(teams.keys())):
        group = teams[team]
        if not group:
            continue

        top = margin_y + idx * block_height
        n = len(group)
        cols = math.ceil(math.sqrt(n))
        rows = math.ceil(n / cols)
        cell_width = usable_width // cols
        cell_height = block_height // rows
        r = int(min(cell_width, cell_height) * 0.3)
        color = TeamConfig.COLOR_MAP.get(team, (255, 255, 255))

        # Dessiner chaque joueurs de l'équipe
        for i, p_data in enumerate(group):
            pid = p_data.get("id", 0)
            cx = margin_x + int((i % cols + 0.5) * cell_width)
            cy = int(top + (i // cols + 0.5) * cell_height)

            # Cercle plein + contour
            pygame.draw.circle(surface, color, (cx, cy), PlayerConfig.RADIUS)
            pygame.draw.circle(surface, (255,255,255), (cx, cy), PlayerConfig.RADIUS, width=2)

            # ID centré
            id_surf = player_font.render(str(pid), True, (255,255,255))
            id_rect = id_surf.get_rect(center=(cx, cy))
            surface.blit(id_surf, id_rect)

    # Compteur de joueurs par équipe
    team_counts = {0: 0, 1: 0, 2: 0}
    for p_data in players.values():
        if not isinstance(p_data, dict):
            continue
        team = p_data.get("team", 0)
        if team in team_counts:
            team_counts[team] += 1

    # Afficher QR code au milieu de l'écran
    if qr_img:
        qr_rect = qr_img.get_rect(centerx=surface.get_width() // 2,
                                  centery=surface.get_height() // 4.5)
        surface.blit(qr_img, qr_rect)

    # Afficher le nombre de joueurs connectés
    players_text = info_font.render(f"Joueurs connectés: {len(players)}", True, (220, 220, 220))
    players_rect = players_text.get_rect(centerx=surface.get_width() // 2, y=460)
    surface.blit(players_text, players_rect)

    # Afficher les équipes
    team_colors = [(180, 180, 180), (237, 28, 36), (0, 162, 232)]  # Gris, Rouge, Bleu
    team_names = ["Équipe Grise", "Équipe Rouge", "Équipe Bleue"]

    # Titre des équipes
    teams_title = info_font.render("Équipes", True, (255, 255, 255))
    teams_title_rect = teams_title.get_rect(centerx=surface.get_width() // 2, y=480)
    surface.blit(teams_title, teams_title_rect)

    # Section équipes
    teams_section_height = 160
    teams_section_y = 510
    pygame.draw.rect(surface, (30, 30, 40),
                     (surface.get_width() // 2 - 200, teams_section_y,
                      400, teams_section_height), 0, 10)

    for i, team_id in enumerate([0, 1, 2]):
        y_pos = teams_section_y + 20 + i * 40
        team_text = info_font.render(f"{team_names[team_id]}: {team_counts[team_id]} joueurs",
                                     True, team_colors[team_id])
        team_rect = team_text.get_rect(centerx=surface.get_width() // 2, y=y_pos)
        surface.blit(team_text, team_rect)


    # Instruction "En attente"
    if len(players) > 0:
        wait_text = info_font.render("En attente du démarrage via panneau admin...", True, (255, 255, 100))
        wait_rect = wait_text.get_rect(centerx=surface.get_width() // 2, y=710)
        surface.blit(wait_text, wait_rect)