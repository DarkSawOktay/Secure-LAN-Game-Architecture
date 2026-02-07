import os
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
import signal
import random
import sys
import time
import math
import pygame
from config import PlayerConfig, TeamConfig, GameConfig, ProjectileConfig
from queue import Empty
from obstacle import Obstacle
from player import Player

running = True

PLAYER_RADIUS = PlayerConfig.RADIUS
RESPAWN_TIME = 4.0  # Temps de respawn en secondes

def handle_exit(signum, frame):
    global running
    running = False

def distance(x1, y1, x2, y2):
    return math.hypot(x2 - x1, y2 - y1)

def get_pixel_color(paint_surface, x, y):
    """Retourne la couleur du pixel à la position (x,y)"""
    try:
        return paint_surface.get_at((int(x), int(y)))
    except:
        return (0, 0, 0)  # Noir par défaut si hors écran

def collides_with_any_obstacle(x, y, radius, obstacles):
    for o in obstacles:
        left = o.x
        top = o.y
        right = o.x + o.width - 1  # corrige dépassement à droite
        bottom = o.y + o.height - 1  # corrige dépassement en bas

        closest_x = max(left, min(x, right))
        closest_y = max(top, min(y, bottom))

        dx = x - closest_x
        dy = y - closest_y
        dist_squared = dx * dx + dy * dy

        if dist_squared < radius * radius:
            return True
    return False

def find_spawn_position(team, obstacles, connected_players):
    """Trouve une position de spawn en fonction de l'équipe sans overlap entre joueurs"""
    MIN_DISTANCE = PlayerConfig.RADIUS * 3  # Distance minimale entre joueurs au spawn

    if team == 1:  # Rouge à droite
        x_range = (GameConfig.BASE_WIDTH - 300, GameConfig.BASE_WIDTH - 100)
        y_range = (200, GameConfig.BASE_HEIGHT - 200)
    elif team == 2:  # Bleu à gauche
        x_range = (100, 300)
        y_range = (200, GameConfig.BASE_HEIGHT - 200)
    else:  # Gris en haut
        x_range = (200, GameConfig.BASE_WIDTH - 200)
        y_range = (100, 300)

    for _ in range(50):  # Augmente les essais
        x = random.randint(*x_range)
        y = random.randint(*y_range)

        # Vérifie obstacles
        if collides_with_any_obstacle(x, y, PlayerConfig.RADIUS, obstacles):
            continue

        # Vérifie la distance avec tous les autres joueurs actifs
        overlap = False
        for other_data in connected_players.values():
            other_p = other_data["player"]
            # Ignore les joueurs en respawn
            if "dead" in other_data and other_data["dead"]:
                continue
            dist = distance(x, y, other_p["x"], other_p["y"])
            if dist < MIN_DISTANCE:
                overlap = True
                break

        if not overlap:
            return x, y

    # Si aucune position safe trouvée
    return (x_range[0] + x_range[1]) // 2, (y_range[0] + y_range[1]) // 2

def player_obstacle_collisions(p, obstacles):
    """Force le joueur à sortir des obstacles même en cas d'encastrement léger, en utilisant une approche cercle/rectangle propre."""
    MAX_ITERATIONS = 15
    PUSH_FORCE = 2  # Force minimale appliquée à chaque itération

    for _ in range(MAX_ITERATIONS):
        collided = False
        for o in obstacles:
            if o.collides_with(p["x"], p["y"], PLAYER_RADIUS):
                collided = True
                # Calcul du point le plus proche
                left, top, right, bottom = o.get_rect()
                closest_x = max(left, min(p["x"], right))
                closest_y = max(top, min(p["y"], bottom))

                # Vecteur de déplacement depuis l'obstacle
                dx = p["x"] - closest_x
                dy = p["y"] - closest_y
                dist = math.hypot(dx, dy)

                if dist == 0:
                    dx, dy = 1, 0
                    dist = 1

                # Pousse le joueur à l'extérieur de l'obstacle (sur le bord + PUSH_FORCE)
                correction = (PLAYER_RADIUS - dist) + PUSH_FORCE
                p["x"] += (dx / dist) * correction
                p["y"] += (dy / dist) * correction
                break
        if not collided:
            break
    return p

def gestion_respawn(connected_players, player_respawns, now, obstacles):
    for pseudo, data in list(connected_players.items()):
        p = data["player"]
        inp = data["inputs"]

        # Vérification du respawn si le joueur est mort
        if pseudo in player_respawns and player_respawns[pseudo]["dead"]:
            if now >= player_respawns[pseudo]["respawn_time"]:
                # Le joueur respawn
                player_respawns[pseudo]["dead"] = False
                # Trouver une position de spawn
                p["x"], p["y"] = find_spawn_position(p["team"], obstacles,connected_players)
                p["ammo"] = PlayerConfig.MAX_AMMO  # Reset des munitions
                p["health"] = PlayerConfig.MAX_HEALTH  # Reset des PV
                print(f"[Game] Le joueur {pseudo} a respawn!")
            else:
                p["ammo"] = 0
                # Le joueur est toujours mort, passer au joueur suivant
                continue

        data["player"] = p
        data["inputs"] = inp
        connected_players[pseudo] = data

def update_joueur(connected_players, obstacles, current_paint_surface, next_proj_id, projectiles, dt, speed_config):
    for pseudo, data in list(connected_players.items()):
        p = data["player"]
        inp = data["inputs"]

        # Déplacement via joystick
        dx, dy = inp["dx"], inp["dy"]

        # Vérifier la couleur sous le joueur pour modifier la vitesse
        if isinstance(current_paint_surface, pygame.Surface):
            pixel_color = get_pixel_color(current_paint_surface, p["x"] + PLAYER_RADIUS, p["y"] + PLAYER_RADIUS)
            team_color = p["team"]

            # Conversion des couleurs pour comparaison
            pixel_rgb = (pixel_color[0], pixel_color[1], pixel_color[2])
            team_rgb = TeamConfig.COLOR_MAP.get(team_color)

            # Détermination si c'est la couleur d'une équipe
            is_team_color = False
            matched_team = None

            for team_id, color in TeamConfig.COLOR_MAP.items():
                if color == pixel_rgb:
                    is_team_color = True
                    matched_team = team_id
                    break

            # Ajustement de la vitesse
            if is_team_color:
                if matched_team == team_color:
                    # Sur sa propre couleur -> boost de vitesse
                    p["speed"] = speed_config["allie"]
                else:
                    # Sur la couleur ennemie -> ralentissement
                    p["speed"] = speed_config["ennemi"]
            else:
                # Sur surface neutre -> vitesse normale
                p["speed"] = speed_config["neutre"]

        radius = PlayerConfig.RADIUS
        new_x = p["x"] + p["speed"] * dx
        new_y = p["y"] + p["speed"] * dy

        # Gestion des collisions avec les obstacles
        collision = collides_with_any_obstacle(new_x, new_y, radius, obstacles)
        # Essai complet (diagonale)
        if not collision:
            p["x"] = max(0, min(GameConfig.BASE_WIDTH, new_x))
            p["y"] = max(0, min(GameConfig.BASE_HEIGHT, new_y))
        # Essai horizontal uniquement
        else:
            collision_x = collides_with_any_obstacle(new_x, p["y"], radius, obstacles)
            if not collision_x:
                p["x"] = max(0, min(GameConfig.BASE_WIDTH, new_x))

            # Essai vertical uniquement
            collision_y = collides_with_any_obstacle(p["x"], new_y, radius, obstacles)
            if not collision_y:
                p["y"] = max(0, min(GameConfig.BASE_HEIGHT, new_y))

        # Calcul angle de visée (pour l'affichage de la flèche)
        ax, ay = inp["aim_dx"], inp["aim_dy"]
        dist_aim = math.hypot(ax, ay)
        if dist_aim > 0.01:
            p["aim_angle"] = math.atan2(ay, ax)
        else:
            p["aim_angle"] = None

        # Recharge munitions
        if p["ammo"] < PlayerConfig.MAX_AMMO:
            p["reload_timer"] += dt
            if p["reload_timer"] >= p["reload_time"]:
                p["ammo"] += 1
                p["reload_timer"] = 0.0

        # Tir => SHOOT_ANGLE
        if inp["shoot_angle"] is not None:
            if p["ammo"] > 0:
                angle = inp["shoot_angle"]
                proj_id = next_proj_id
                next_proj_id += 1

                vx = ProjectileConfig.SPEED * math.cos(angle)
                vy = ProjectileConfig.SPEED * math.sin(angle)

                projectiles[proj_id] = {
                    "x": p["x"],  # point de départ
                    "y": p["y"],
                    "vx": vx,
                    "vy": vy,
                    "team": p["team"],
                    "shooter": pseudo,  # Pour savoir qui a tiré
                    "radius": ProjectileConfig.RADIUS,
                    "range": ProjectileConfig.RANGE,  # distance max
                    "dist_travelled": 0.0  # distance parcourue
                }
                p["ammo"] -= 1

            inp["shoot_angle"] = None

        data["player"] = p
        data["inputs"] = inp
        connected_players[pseudo] = data

def collision_joueur(connected_players, player_respawns, friendly_collisions):
    players_list = list(connected_players.items())
    for i in range(len(players_list)):
        pseudo1, d1 = players_list[i]
        # Ignorer si joueur en respawn
        if pseudo1 in player_respawns and player_respawns[pseudo1]["dead"]:
            continue

        for j in range(i + 1, len(players_list)):
            pseudo2, d2 = players_list[j]
            # Ignorer si joueur en respawn
            if pseudo2 in player_respawns and player_respawns[pseudo2]["dead"]:
                continue

            p1 = d1["player"]
            p2 = d2["player"]

            # ignorer collisions amicales si param OFF + même team
            if (not friendly_collisions.value) and (p1["team"] == p2["team"]):
                continue

            distp = distance(p1["x"], p1["y"], p2["x"], p2["y"])
            if distp < (PLAYER_RADIUS * 2):
                overlap = (PLAYER_RADIUS * 2) - distp
                if distp != 0:
                    nx = (p2["x"] - p1["x"]) / distp
                    ny = (p2["y"] - p1["y"]) / distp
                    p1["x"] -= nx * (overlap / 2)
                    p1["y"] -= ny * (overlap / 2)
                    p2["x"] += nx * (overlap / 2)
                    p2["y"] += ny * (overlap / 2)

                d1["player"] = p1
                d2["player"] = p2
                connected_players[pseudo1] = d1
                connected_players[pseudo2] = d2

def gestion_projectiles(projectiles, connected_players, player_respawns, obstacles, now, friendly_collisions):
    to_remove = []
    for pid, proj in projectiles.items():
        old_x, old_y = proj["x"], proj["y"]
        # Avance
        proj["x"] += proj["vx"]
        proj["y"] += proj["vy"]

        # distance parcourue
        step_dist = math.hypot(proj["vx"], proj["vy"])
        proj["dist_travelled"] += step_dist

        # Si on dépasse la portée, on supprime
        if proj["dist_travelled"] >= proj["range"]:
            to_remove.append(pid)
            continue

        # Collision avec obstacle
        collision = collides_with_any_obstacle(proj["x"], proj["y"], proj["radius"], obstacles)
        if collision:
            # Le projectile s'arrête sur l'obstacle
            proj["x"] = old_x
            proj["y"] = old_y
            to_remove.append(pid)
            continue

        # Sortie écran
        if proj["x"] < 0 or proj["x"] > GameConfig.BASE_WIDTH or proj["y"] < 0 or proj["y"] > GameConfig.BASE_HEIGHT:
            to_remove.append(pid)
            continue

        # Collision projectile ↔ joueurs (qui ne sont pas en respawn)
        for pseudo, data in connected_players.items():
            # Ignorer les joueurs en respawn
            if pseudo in player_respawns and player_respawns[pseudo]["dead"]:
                continue

            # Ignorer le tireur
            if pseudo == proj["shooter"]:
                continue

            p = data["player"]
            distp = distance(proj["x"], proj["y"], p["x"], p["y"])

            if distp < (proj["radius"] + PLAYER_RADIUS):  # Collision détectée

                # Ignorer collisions amicales si param OFF + même team
                if (not friendly_collisions.value) and (p["team"] == proj["team"]):
                    continue

                # Joueur touché -> déclencher respawn
                print(f"[Game] Le joueur {pseudo} a été touché par un projectile de {proj['shooter']}!")

                pseudo_t = projectiles[pid]["shooter"]
                entree_t = connected_players[pseudo_t]
                p_t = Player.from_dict(entree_t["player"])

                entree = connected_players[pseudo]
                p = Player.from_dict(entree["player"])

                p_t.add_xp(5)
                p.take_damage(1)
                if p.is_dead():
                    p_t.add_xp(20)
                    entree["player"].update(p.to_dict())
                    connected_players[pseudo] = entree
                    player_respawns[pseudo] = {
                        "dead": True,
                        "respawn_time": now + RESPAWN_TIME
                    }

                entree_t["player"].update(p_t.to_dict())
                connected_players[pseudo_t] = entree_t

                entree["player"].update(p.to_dict())
                connected_players[pseudo] = entree

                # Supprimer le projectile
                to_remove.append(pid)
                break

    for pid in to_remove:
        if pid in projectiles:
            del projectiles[pid]

def real_game_logic(connected_players, lobby_state_queue, game_started, friendly_collisions, paint_surface_queue, to_couleur_queue, from_couleur_queue, game_duration, speed_config,prepare_phase,game_start_time):
    global running
    signal.signal(signal.SIGINT, handle_exit)
    signal.signal(signal.SIGTERM, handle_exit)

    projectiles = {}
    next_proj_id = 0
    last_time = time.time()
    GAME_DURATION = game_duration.value  # durée de la manche en secondes (variable partagé)

    # Initialiser une surface de peinture par défaut
    current_paint_surface = pygame.Surface((GameConfig.BASE_WIDTH, GameConfig.BASE_HEIGHT), flags=pygame.SRCALPHA)
    current_paint_surface.fill((0, 0, 0))  # Noir par défaut

    # Création des obstacles
    obstacles = []
    for _ in range(20):
        x = random.randint(80, GameConfig.BASE_WIDTH - 80)
        y = random.randint(80, GameConfig.BASE_HEIGHT - 80)
        if random.choice([True, False]):
            width = random.randint(10, 15)
            height = random.randint(60, 100)
        else:
            width = random.randint(60, 100)
            height = random.randint(10, 15)
        obstacles.append(Obstacle(x, y, width, height))

        # À faire juste après la création des obstacles (avant toute boucle de jeu)
        for pseudo, data in connected_players.items():
            p = data["player"]
            # Forcer un spawn initial propre par équipe
            p["x"], p["y"] = find_spawn_position(p["team"], obstacles, connected_players)
            p["health"] = PlayerConfig.MAX_HEALTH
            data["player"] = p
            connected_players[pseudo] = data


    # Initialisation des états de respawn des joueurs
    player_respawns = {}  # {pseudo: {"dead": bool, "respawn_time": float}}

    while running and game_started.value:
        now = time.time()
        dt = now - last_time
        last_time = now

        # Blocage complet pendant prepare_phase
        if prepare_phase.value:
            # Figer les inputs à zéro
            for pseudo, data in connected_players.items():
                inp = data["inputs"]
                inp["dx"] = 0.0
                inp["dy"] = 0.0
                inp["aim_dx"] = 0.0
                inp["aim_dy"] = 0.0
                inp["shoot_angle"] = None
                data["inputs"] = inp
                connected_players[pseudo] = data

            # Envoyer uniquement un snapshot "figé"
            temp_players = {}
            for pseudo, data in connected_players.items():
                p = data["player"]
                pid = data.get("id", 0)
                temp_players[pseudo] = {
                    "id": pid,
                    "x": p["x"],
                    "y": p["y"],
                    "team": p["team"],
                    "ammo": p["ammo"],
                    "aim_angle": p["aim_angle"],
                    "dead": False,
                    "respawn_time": 0
                }

            temp_projectiles = {}
            temp_obstacles = [
                {"x": o.x, "y": o.y, "width": o.width, "height": o.height}
                for o in obstacles
            ]

            display_data = {
                "players": temp_players,
                "projectiles": temp_projectiles,
                "obstacles": temp_obstacles,
                "start_time": now,  # moment actuel juste pour afficher quelque chose
                "duration": GAME_DURATION
            }

            lobby_state_queue.put(display_data)
            time.sleep(0.016)
            continue  # saute toute la boucle, rien ne bouge ni ne progresse


        # Récupération de la surface de peinture
        try:
            surface_data = paint_surface_queue.get_nowait()
            if not isinstance(surface_data, pygame.Surface):
                surface_data = pygame.surfarray.make_surface(surface_data)
            current_paint_surface = surface_data
        except Empty:
            pass

        # 1. Gestion des respawns et mise à jour des joueurs
        gestion_respawn(connected_players, player_respawns, now, obstacles)
        update_joueur(connected_players, obstacles, current_paint_surface, next_proj_id, projectiles, dt, speed_config)

        # 2. Collisions Joueurs (ignorés si en respawn)
        collision_joueur(connected_players, player_respawns, friendly_collisions)

        # 2b. Correction : empêcher les joueurs d'être coincés dans les obstacles après collision
        for pseudo, data in connected_players.items():
            p = data["player"]
            p = player_obstacle_collisions(p, obstacles)
            data["player"] = p
            connected_players[pseudo] = data

        # 3. Projectiles
        gestion_projectiles(projectiles, connected_players, player_respawns, obstacles, now, friendly_collisions)

        # 4. Préparer l'état pour affichage
        temp_players = {}
        for pseudo, data in connected_players.items():
            p = data["player"]
            pid = data.get("id", 0)

            # Ajouter l'état de mort aux données du joueur
            is_dead = pseudo in player_respawns and player_respawns[pseudo]["dead"]
            respawn_time = player_respawns.get(pseudo, {}).get("respawn_time", 0) if is_dead else 0

            temp_players[pseudo] = {
                "id": pid,
                "x": p["x"],
                "y": p["y"],
                "health": p["health"],
                "team": p["team"],
                "ammo": p["ammo"],
                "aim_angle": p["aim_angle"],
                "dead": is_dead,
                "respawn_time": respawn_time
            }

        temp_projectiles = {}
        for pid, proj in projectiles.items():
            temp_projectiles[pid] = {
                "x": proj["x"],
                "y": proj["y"],
                "team": proj["team"]
            }

        temp_obstacles = [
            {"x": o.x, "y": o.y, "width": o.width, "height": o.height}
            for o in obstacles
        ]

        display_data = {
            "players": temp_players,
            "projectiles": temp_projectiles,
            "obstacles": temp_obstacles,
            "start_time": game_start_time.value,  # début de la partie
            "duration": GAME_DURATION
        }

        # Envoi à la queue
        lobby_state_queue.put(display_data)

        # Vérifie si le temps est écoulé
        if time.time() - game_start_time.value >= GAME_DURATION:
            print("[Game] Fin du temps de jeu.")

            # Demande le calcul des couleurs finales
            import pickle
            try:
                arr = pygame.surfarray.array3d(current_paint_surface)
                to_couleur_queue.put(pickle.dumps(arr))
                time.sleep(1)  # attend un peu le traitement
                resultat = from_couleur_queue.get(timeout=2)
            except:
                resultat = {}

            print("[Game] Score final:", resultat)

           # Déterminer le gagnant
            gagnant_str = ""
            if resultat:
                gagnant = max(resultat.items(), key=lambda x: x[1])[0]
                print(f"[Game] L'équipe gagnante est l'équipe {gagnant}")
                gagnant_str = f"L'équipe {gagnant}"
            else:
                gagnant_str = "ÉGALITÉ"
                print("[Game] Aucun résultat de score reçu.")

            # Affichage du gagnant PENDANT 5 SECONDES
            print(f"[Game] Affichage du gagnant : {gagnant_str}")

            # Envoyer un état à afficher avec le gagnant
            display_data = {
                "players": temp_players,
                "projectiles": {},
                "obstacles": temp_obstacles,
                "winner": gagnant_str,
                "show_winner": True  # Indicateur explicite
            }

            # Envoyer plusieurs fois pour garantir que l'affichage le reçoit
            for _ in range(3):
                lobby_state_queue.put(display_data)
                time.sleep(0.1)

            # Afficher le gagnant pendant 5 secondes
            time.sleep(5)

            # Remise à zéro des joueurs avant retour lobby
            p["x"] = 200
            p["y"] = 150
            p["team"] = (p["team"]+1)%3
            p["paint_power"] = PlayerConfig.PAINT_POWER
            p["health"] = PlayerConfig.MAX_HEALTH
            p["speed"] = 0.0
            p["damage"] = PlayerConfig.DAMAGE
            p["ammo"] = PlayerConfig.MAX_AMMO
            p["reload_time"] = PlayerConfig.RELOAD_TIME
            p["reload_timer"] = 0.0
            p["aim_angle"] = None
            p["level"] = 1
            p["xp"] = 0.0
            p["xp_to_next_level"] = 100
            p["powerups"] = []
            p["projectile_count"] = 1
            p["levelup_pending"] = False

            data["inputs"]["dx"] = 0.0
            data["inputs"]["dy"] = 0.0
            data["inputs"]["aim_dx"] = 0.0
            data["inputs"]["aim_dy"] = 0.0
            data["inputs"]["shoot_angle"] = None
            connected_players[pseudo] = data

            # Affichage de l'équipe gagnante pendant 5s avant retour lobby
            gagnant_str = f"L'équipe {gagnant}" if resultat else "ÉGALITÉ"
            print(f"[Game] Affichage du gagnant : {gagnant_str}")

            display_data = {
                "players": temp_players,
                "projectiles": {},
                "obstacles": temp_obstacles,
                "winner": gagnant_str
                }

            lobby_state_queue.put(display_data)

            # Pause d'affichage 5s
            time.sleep(5)


            game_started.value = False  # revenir en mode lobby
            running = False  # Pour sortir de la boucle proprement
            break

        time.sleep(max(0.001, 0.016 - (time.time() - now)))

    print("[Game] Arrêt propre.")
    sys.exit(0)