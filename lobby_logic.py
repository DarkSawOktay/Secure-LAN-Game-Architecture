import random
import signal
import time
import logging
import sys
from config import PlayerConfig, TeamConfig, GameConfig

# Configuration du logger
logger = logging.getLogger("Lobby")

# Constantes pour le lobby
UPDATE_RATE = 30  # mises à jour par seconde
DISPLAY_RATE = 10  # envois à l'affichage par seconde
LOBBY_PLAYER_SPEED = 10.0  # vitesse de déplacement dans le lobby

# Variable pour le contrôle d'exécution
running = True

def handle_exit(signum, frame):
    """Gestionnaire de signal pour l'arrêt propre"""
    global running
    running = False
    logger.info("Signal d'arrêt reçu")

def initialize_player(pseudo, player, team_id):
    """Initialise les attributs d'un nouveau joueur"""
    player["team"] = team_id
    
    # Position de départ selon l'équipe
    if team_id == 1:  # Rouge
        player["x"] = random.randint(100, 400)
        player["y"] = random.randint(100, 300)
    elif team_id == 2:  # Bleu
        player["x"] = random.randint(600, 900) 
        player["y"] = random.randint(400, 600)
    else:  # Gris
        player["x"] = random.randint(350, 650)
        player["y"] = random.randint(250, 450)
    
    # Initialisation des attributs du joueur
    player["radius"] = PlayerConfig.RADIUS
    player["base_speed"] = PlayerConfig.BASE_SPEED
    player["speed"] = PlayerConfig.BASE_SPEED
    player["ammo"] = PlayerConfig.MAX_AMMO
    player["max_ammo"] = PlayerConfig.MAX_AMMO
    player["reload_time"] = PlayerConfig.RELOAD_TIME
    player["reload_timer"] = 0.0
    player["aim_angle"] = None
    player["name"] = pseudo
    
    return player

def assign_team(connected_players):
    """Détermine l'équipe pour un nouveau joueur en équilibrant les équipes"""
    # Comptage des joueurs par équipe
    team_counts = {team_id: 0 for team_id in range(0, GameConfig.TEAMS_COUNT)}
    
    for data in connected_players.values():
        player = data.get("player", {})
        t = player.get("team")
        if t in team_counts:
            team_counts[t] += 1

    # Choisir l'équipe dont le compteur est minimal
    chosen = min(team_counts, key=lambda x: team_counts[x])
    return chosen

def update_player_position(player, inputs):
    """Met à jour la position du joueur en fonction des entrées"""
    # Déplacement via joystick (simulé ou réel)
    dx, dy = inputs["dx"], inputs["dy"]
    
    # Mise à jour des positions
    player["x"] += LOBBY_PLAYER_SPEED * dx
    player["y"] += LOBBY_PLAYER_SPEED * dy
    
    # Limites de l'écran
    player["x"] = max(50, min(GameConfig.BASE_WIDTH - 50, player["x"]))
    player["y"] = max(50, min(GameConfig.BASE_HEIGHT - 50, player["y"]))
    
    # Calcul angle de visée (pour l'affichage de la flèche)
    ax, ay = inputs["aim_dx"], inputs["aim_dy"]
    dist_aim = (ax**2 + ay**2)**0.5
    if dist_aim > 0.01:
        player["aim_angle"] = time.time() % (2*3.14159)  # Animation rotation
    else:
        player["aim_angle"] = None
    
    # Direction (pour l'affichage)
    player["direction"] = player.get("aim_angle", 0)
    
    return player

def create_display_state(connected_players):
    """Crée un état simplifié pour l'affichage"""
    state_for_display = {}
    
    for pseudo, data in connected_players.items():
        p = data["player"]
        pid = data.get("id", 0)
        state_for_display[pseudo] = {
            "id":        pid,
            "x":         p.get("x", 0),
            "y":         p.get("y", 0),
            "team":      p.get("team", 0),
            "name":      p.get("name", pseudo),
            "direction": p.get("direction", 0),
            "radius":    p.get("radius", PlayerConfig.RADIUS)
        }
    
    return state_for_display

def count_teams(connected_players):
    """Compte les joueurs par équipe et retourne les statistiques"""
    team_counts = {0: 0, 1: 0, 2: 0}
    players_by_team = {0: [], 1: [], 2: []}
    
    for pseudo, data in connected_players.items():
        p = data["player"]
        if "team" in p:
            team = p["team"]
            if team in team_counts:
                team_counts[team] += 1
                players_by_team[team].append(pseudo)
    
    return team_counts, players_by_team

def send_display_state(state, queue):
    """Envoie l'état à l'affichage en vidant d'abord la queue"""
    try:
        # Vider la queue avant de mettre le nouvel état
        while not queue.empty():
            try:
                queue.get_nowait()
            except:
                pass
        
        # Envoyer le nouvel état
        queue.put(state)
        return True
    except Exception as e:
        logger.error(f"Erreur lors de l'envoi de l'état du lobby: {e}")
        return False

def lobby_logic(connected_players, lobby_state_queue, game_started):
    """
    Gère la logique du lobby avant le début d'une partie.
    Gère le déplacement des joueurs et la synchronisation de leur état.
    
    Args:
        connected_players: Dictionnaire partagé des joueurs connectés
        lobby_state_queue: Queue pour envoyer l'état au processus d'affichage
        game_started: Flag pour indiquer si le jeu a commencé
    """
    global running
    signal.signal(signal.SIGINT, handle_exit)
    signal.signal(signal.SIGTERM, handle_exit)
    
    logger.info("Démarrage du processus de logique du lobby")
    
    last_time = time.time()
    last_display_time = time.time()
    update_interval = 1/UPDATE_RATE
    display_interval = 1/DISPLAY_RATE
    
    while running and not game_started.value:
        now = time.time()
        dt = now - last_time
        
        # Limiter la fréquence de mise à jour
        if dt < update_interval:
            time.sleep(max(0, update_interval - dt))
            continue
        
        last_time = now
        
        # Compter et logger les équipes
        team_counts, _ = count_teams(connected_players)
        
        # Mise à jour des positions des joueurs dans le lobby
        for pseudo, data in list(connected_players.items()):
            try:
                p = data["player"]
                inp = data["inputs"]
                
                # Si nouveau joueur ou joueur sans équipe, assigner à une équipe
                if "team" not in p:
                    assigned_team = assign_team(connected_players)
                    p = initialize_player(pseudo, p, assigned_team)
                    logger.info(f"Joueur {pseudo} assigné à l'équipe {assigned_team}")
                
                # S'assurer que x et y existent
                if "x" not in p or "y" not in p:
                    p["x"] = random.randint(100, 900)
                    p["y"] = random.randint(100, 600)
                
                # Mise à jour de la position du joueur
                p = update_player_position(p, inp)
                
                # Mettre à jour les données du joueur
                data["player"] = p
                connected_players[pseudo] = data
            except Exception as e:
                logger.error(f"Erreur lors de la mise à jour du joueur {pseudo}: {e}")
        
        # Créer un état simplifié pour l'affichage
        state_for_display = create_display_state(connected_players)
        
        # Envoyer l'état à intervalle régulier
        if now - last_display_time >= display_interval:
            if send_display_state(state_for_display, lobby_state_queue):
                last_display_time = now
    
    logger.info("Sortie propre du processus de logique du lobby")