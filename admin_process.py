import os
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
import pygame
import sys

ROW_HEIGHT = 40
BTN_WIDTH = 60
BTN_HEIGHT = 30

BTN_COULEUR_RECT = pygame.Rect(50, 250, 300, 40)
BTN_COLLISION_RECT = pygame.Rect(50, 300, 300, 40)
BTN_GAME_TOGGLE_RECT = pygame.Rect(50, 350, 300, 40)

# Classe Slider pour contrôler dynamiquement les vitesses
class Slider:
    def __init__(self, x, y, w, h, min_val, max_val, initial, label):
        self.rect = pygame.Rect(x, y, w, h)
        self.min_val = min_val
        self.max_val = max_val
        self.value = initial
        self.dragging = False
        self.label = label

    def draw(self, surface, font):
        pygame.draw.rect(surface, (100, 100, 100), self.rect)
        fill_width = int((self.value - self.min_val) / (self.max_val - self.min_val) * self.rect.width)
        pygame.draw.rect(surface, (0, 200, 0), (self.rect.x, self.rect.y, fill_width, self.rect.height))
        label_surface = font.render(f"{self.label}: {int(self.value)}", True, (255, 255, 255))
        surface.blit(label_surface, (self.rect.x, self.rect.y - 20))

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and self.rect.collidepoint(event.pos):
            self.dragging = True
        elif event.type == pygame.MOUSEBUTTONUP:
            self.dragging = False
        elif event.type == pygame.MOUSEMOTION and self.dragging:
            rel_x = event.pos[0] - self.rect.x
            ratio = max(0, min(rel_x / self.rect.width, 1))
            self.value = int(self.min_val + ratio * (self.max_val - self.min_val))


def admin_main(admin_queue, manager_queue, connected_players, game_started,
               friendly_collisions, calc_couleur, speed_config,game_duration):
    
    WINDOW_HEIGHT = 600
    SCROLL_START = 400  #  où commence la liste des joueurs

    """
    calc_couleur remplace calc_coverage. True => on calcule la couleur (pourcentage).
    """
    if not pygame.get_init():
        pygame.init()
    screen = pygame.display.set_mode((400, 600))
    pygame.display.set_caption("Admin - Paramètres")
    font = pygame.font.SysFont(None, 24)
    clock = pygame.time.Clock()

    # Initialisation des sliders pour les vitesses et chrono
    sliders = [
        Slider(50, 70, 200, 20, 1, 20, speed_config["neutre"], "Vitesse zone neutre"),
        Slider(50, 110, 200, 20, 1, 20, speed_config["allie"], "Vitesse zone alliée"),
        Slider(50, 150, 200, 20, 1, 20, speed_config["ennemi"], "Vitesse zone ennemie"),
        Slider(50, 190, 200, 20, 10, 300, game_duration.value, "Durée (s)")
    ]

    

    running = True
    scroll_offset = 0  # Ajout pour scroller la liste

    try:
        while running:
            for event in pygame.event.get():
                # Fermeture de la fenêtre
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    running = False
                elif event.type == pygame.MOUSEWHEEL:
                    scroll_offset -= event.y * 20  # 20 pixels par cran de molette
                    scroll_offset = max(0, scroll_offset)

                    # Calcul du scroll max pour ne pas remonter au-dessus du bouton "Lancer le jeu"
                    nb_joueurs = len(connected_players)
                    total_height = nb_joueurs * ROW_HEIGHT
                    visible_height = WINDOW_HEIGHT - SCROLL_START  # Hauteur visible pour la liste (400 = point de départ)
                    max_scroll = max(0, total_height - visible_height)
                    scroll_offset = min(scroll_offset, max_scroll)



                # Gestion sliders 
                for slider in sliders:
                    slider.handle_event(event)

                # Clics souris sur les boutons ou changement d'équipe
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    mouse_pos = event.pos

                    # Bouton start/stop
                    if BTN_GAME_TOGGLE_RECT.collidepoint(mouse_pos):
                        if not game_started.value:
                            admin_queue.put("START_GAME")
                        else:
                            game_started.value = False
                            print("[Admin] Le jeu a été arrêté via le bouton STOP")

                    # Bouton "Couleurs"
                    elif BTN_COULEUR_RECT.collidepoint(mouse_pos):
                        calc_couleur.value = not calc_couleur.value
                        print("[Admin] Couleurs toggled:", calc_couleur.value)

                    # Bouton collisions amicales
                    elif BTN_COLLISION_RECT.collidepoint(mouse_pos):
                        friendly_collisions.value = not friendly_collisions.value
                        print("[Admin] Friendly collisions toggled:", friendly_collisions.value)

                    # Changement d'équipe
                    else:
                        for i, (pseudo, d) in enumerate(connected_players.items()):
                            row_y = i * ROW_HEIGHT + SCROLL_START - scroll_offset
                            if row_y >= SCROLL_START:
                                for j in range(3):
                                    btn_rect = pygame.Rect(200 + j*70, row_y, BTN_WIDTH, BTN_HEIGHT)
                                    if btn_rect.collidepoint(mouse_pos):
                                        p = d["player"]

                                        p["team"] = j
                                        d["player"] = p
                                        connected_players[pseudo] = d


            # Affichage
            screen.fill((50,50,50))
            title_surf = font.render("Admin - Collisions / Équipes / Couleurs", True, (255,255,255))
            screen.blit(title_surf, (40, 10))

            # Dessin sliders
            for slider in sliders:
                slider.draw(screen, font)

            # Mise à jour des vitesses dans speed_config
            speed_config["neutre"] = sliders[0].value
            speed_config["allie"] = sliders[1].value
            speed_config["ennemi"] = sliders[2].value
            # Changement de la durée d'une partie
            game_duration.value = sliders[3].value


            # Bouton Lancer/Stop
            if not game_started.value:
                pygame.draw.rect(screen, (0, 200, 0), BTN_GAME_TOGGLE_RECT)
                label = font.render("Lancer le jeu", True, (255, 255, 255))
            else:
                pygame.draw.rect(screen, (200, 0, 0), BTN_GAME_TOGGLE_RECT)
                label = font.render('Arreter le jeu', True, (255, 255, 255))
            screen.blit(label, (BTN_GAME_TOGGLE_RECT.x + 60, BTN_GAME_TOGGLE_RECT.y + 10))

            # Bouton "Couleurs"
            couleur_text = "Couleurs: ON" if calc_couleur.value else "Couleurs: OFF"
            pygame.draw.rect(screen, (128,128,128), BTN_COULEUR_RECT)
            label_coul = font.render(couleur_text, True, (255,255,255))
            screen.blit(label_coul, (BTN_COULEUR_RECT.x+60, BTN_COULEUR_RECT.y+10))

            # Bouton collisions amicales
            col_text = "Collisions amicales: ON" if friendly_collisions.value else "Collisions amicales: OFF"
            pygame.draw.rect(screen, (128,128,128), BTN_COLLISION_RECT)
            label_col = font.render(col_text, True, (255,255,255))
            screen.blit(label_col, (BTN_COLLISION_RECT.x+10, BTN_COLLISION_RECT.y+10))

            # Info nombre de joueurs et joueurs par équipe 
            team_counts = {0: 0, 1: 0, 2: 0}
            for d in connected_players.values():
                p = d["player"]
                team = p.get("team", 0)
                if team in team_counts:
                    team_counts[team] += 1

            info_text = f"{len(connected_players)} joueurs connectés | T0= {team_counts[0]} | T1= {team_counts[1]} | T2= {team_counts[2]}"
            txt_surf = font.render(info_text, True, (255,255,255))
            screen.blit(txt_surf, (20, 220))

            # Liste joueurs + boutons de changement d'équipe
            for i, (pseudo, d) in enumerate(connected_players.items()):
                row_y = i*ROW_HEIGHT + SCROLL_START - scroll_offset
                if row_y >= SCROLL_START:  # Ne dessine le joueur que s'il est sous les boutons
                    p = d["player"]
                    team = p["team"]
                    txt_surf = font.render(f"{pseudo} (team={team})", True, (255,255,255))
                    screen.blit(txt_surf, (20, row_y))

                    btn_colors = [(100,100,100), (200,0,0), (0,0,200)]
                    labels = ["T0","T1","T2"]
                    for j in range(3):
                        btn_rect = pygame.Rect(200 + j*70, row_y, BTN_WIDTH, BTN_HEIGHT)
                        pygame.draw.rect(screen, btn_colors[j], btn_rect)
                        label = font.render(labels[j], True, (255,255,255))
                        screen.blit(label, (btn_rect.x+15, btn_rect.y+5))

            # Envoie du nombre de joueurs au manager
            manager_queue.put(("UPDATE_PLAYERS", len(connected_players)))

            pygame.display.flip()
            clock.tick(30)
    except KeyboardInterrupt:
        print("[Admin] Fermeture propre.")
    finally:
        pygame.quit()
        # Au lieu d'utiliser sys.exit(), on termine simplement la fonction
        manager_queue.put(("ADMIN_CLOSED", None))
        return