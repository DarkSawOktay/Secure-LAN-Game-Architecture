"""
Configuration centralisée pour le jeu Splatoon-like

Ce module contient toutes les constantes et paramètres utilisés dans le jeu,
organisés par catégories pour une meilleure maintenance.
"""
import os
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
import pygame
import sys
import logging
from typing import Dict, Tuple

# Configuration du système de logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s - %(name)s: %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger("Config")

# ------------------------------------------------------
# CONFIGURATION DE BASE DU JEU
# ------------------------------------------------------
class GameConfig:
    """Configuration générale du jeu"""
    VERSION = "1.0.0"
    TITLE = "Paint War"
    DEBUG_MODE = True
    
    # Dimensions et performance
    BASE_WIDTH = None
    BASE_HEIGHT = None
    FPS = 60
    
    # Apparence
    BG_COLOR = (0, 0, 0)
    
    # Gestion de la partie
    DEFAULT_GAME_DURATION = 180  # Durée par défaut d'une partie en secondes (3 minutes)
    TEAMS_COUNT = 3  # Nombre d'équipes
    
    # QR Code
    QR_BOX_SIZE = 10
    QR_BORDER = 5

    # Transparence du « ghost » en lobby/jeu
    GHOST_ALPHA = 128
    # Largeur du contour des joueurs
    PLAYER_OUTLINE_WIDTH = 2

    # Paramètres de performance et optimisation
    class Performance:
        """Configuration des paramètres de performance"""
        # Traînées des joueurs
        MAX_TRAIL_POINTS = 5000  # Nombre maximal de points de traînée avant optimisation
        TRAIL_HISTORY_SECONDS = 10.0  # Temps en secondes à conserver dans l'historique
        TRAIL_OPTIMIZE_INTERVAL = 1.0  # Intervalle d'optimisation en secondes
        
        # Analyse de couleur
        COLOR_ANALYSIS_INTERVAL = 2.0  # Intervalle d'analyse des couleurs en secondes
        
        # Qualité visuelle vs performance
        LOW_QUALITY_THRESHOLD = 40  # FPS en dessous duquel on réduit la qualité visuelle
        HIGH_QUALITY_THRESHOLD = 55  # FPS au-dessus duquel on peut améliorer la qualité

    # Intervalle d'envoi des snapshots couleur (secondes)
    COLOR_SNAPSHOT_INTERVAL = Performance.COLOR_ANALYSIS_INTERVAL
# ------------------------------------------------------
# CONFIGURATION DES JOUEURS
# ------------------------------------------------------
class PlayerConfig:
    """Configuration des joueurs"""
    # Paramètres de base
    RADIUS = 15        # Rayon du joueur en pixels
    PAINT_POWER = 1.0  # Puissance de peinture (multiplicateur)
    DAMAGE = 1.0       # Dégâts de base
    MAX_HEALTH = 3     # PV de base
    
    # Munitions et recharge
    PROJECTILE_RADIUS = 5
    MAX_AMMO = 10      # Capacité maximale de munitions
    RELOAD_TIME = 2.0  # Temps de rechargement en secondes


    # Système d'expérience et de niveau
    BASE_XP_LEVEL = 100  # XP nécessaire pour le niveau 2
    XP_PAINT = 0.5       # XP gagnée par unité de peinture
    XP_KILL = 50         # XP gagnée par élimination

    # Pour le dessin de la traînée (interpolation)
    TRAIL_STEP  = 6
    # Largeur du contour dans _draw_circle
    OUTLINE_W   = 2

# ------------------------------------------------------
# CONFIGURATION DES PROJECTILES
# ------------------------------------------------------
class ProjectileConfig:
    """Configuration des projectiles"""
    # Paramètres de base
    RADIUS = 5         # Rayon du projectile
    SPEED = 15        # Vitesse en pixels/seconde
    PAINT_RADIUS = 10  # Rayon de l'impact de peinture
    LIFETIME = 2.0     # Durée de vie en secondes
    RANGE = 300        # Portée du projectile
    
    # Couleurs des projectiles par équipe
    COLOR_MAP = {
        0: (200, 200, 200),
        1: (255, 50, 50),    # Projectiles équipe 1 (rouge vif)
        2: (50, 180, 255)    # Projectiles équipe 2 (bleu vif)
    }

    # Couleur par défaut de repli
    DEFAULT_COLOR = COLOR_MAP[0]

# ------------------------------------------------------
# CONFIGURATION DES OBSTACLES
# -----------------------------------------------------
class ObstacleConfig:
    """Configuration des obstacles"""
    # Nombre de base d'obstacles (ajusté selon la taille)
    BASE_COUNT = 20
    MIN_WIDTH = 10
    MAX_WIDTH = 200
    MIN_HEIGHT = 10
    MAX_HEIGHT = 200
    
    # Apparence
    COLOR = (100, 100, 100)  # Gris foncé

# ------------------------------------------------------
# CONFIGURATION DES ÉQUIPES
# ------------------------------------------------------
class TeamConfig:
    """Configuration des équipes"""
    # Couleurs RGB des équipes
    COLOR_MAP = {
        0: (200, 200, 200),  # Neutre (gris)
        1: (237, 28, 36),    # Équipe 1 (rouge)
        2: (0, 162, 232)     # Équipe 2 (bleu)
    }
    
    # Noms des équipes
    NAME_MAP = {
        0: "Gris",
        1: "Rouge",
        2: "Bleu"
    }
    
    # Positions de départ pour chaque équipe
    START_POSITIONS = {
        1: [(100, 100), (150, 100), (200, 100), (250, 100)],     # Équipe 1
        2: [(100, 600), (150, 600), (200, 600), (250, 600)],     # Équipe 2
        3: [(100, 1100), (150, 1100), (200, 1100), (250, 1100)]  # Équipe 3
    }

# ------------------------------------------------------
# CONFIGURATION DE L'AFFICHAGE (UI)
# ------------------------------------------------------
class UIConfig:
    # Font sizes
    TITLE_FONT_SIZE        = 72
    INFO_FONT_SIZE         = 36
    TEXT_FONT_SIZE         = 24

    # QR code display
    QR_SIZE                = 200

    # Lobby layout ratios (pourcentages de la hauteur)
    LOBBY_TITLE_RATIO      = 0.10   # titre à 10% de la hauteur
    LOBBY_INFO_RATIO       = 0.20   # URL à 20%
    LOBBY_QR_RATIO         = 0.50   # QR code à 50%
    LOBBY_PLAYER_Y_RATIO   = 0.80   # ligne des joueurs à 80%

    # Margins et dimensions
    LOBBY_SIDE_MARGIN      = 0.05   # 5% de marge horizontale
    LOBBY_BOTTOM_MARGIN    = 0.02   # 2% de marge verticale sous zone

    # Scoreboard
    SCOREBOARD_X           = 200
    SCOREBOARD_Y           = 40
    SCOREBOARD_W_RATIO     = 0.6    # 60% de la largeur de l'écran
    SCOREBOARD_H           = 20

    # Timer
    TIMER_MARGIN           = 10     # marge du timer en haut à droite

# ------------------------------------------------------
# CONFIGURATION DES COULEURS UI
# ------------------------------------------------------
class ColorConfig:
    # Backgrounds
    BACKGROUND_LOBBY       = (20, 20, 30)
    BACKGROUND_GAME        = GameConfig.BG_COLOR

    # Scoreboard
    SCORE_BG               = (255, 255, 255)
    SCORE_BG_INNER         = (0, 0, 0)
    SCORE_TEXT             = (255, 255, 255)

    # Timer
    TIMER_COLOR            = (255, 255, 255)
    TIMER_COLOR_PAST       = (255, 200, 0)
    TIMER_BG               = (0, 0, 0, 150)

    # Players
    PLAYER_OUTLINE         = (255, 255, 255)
    PLAYER_TEXT            = (255, 255, 255)

    # Obstacles & projectiles
    OBSTACLE               = ObstacleConfig.COLOR
    PROJECTILE_COLORS      = ProjectileConfig.COLOR_MAP

    # Couleur par défaut si team/projectile non trouvée
    DEFAULT_PROJECTILE = ProjectileConfig.DEFAULT_COLOR
    DEFAULT_TEAM       = TeamConfig.COLOR_MAP.get(0, (200, 200, 200))

    # Couleur du texte en lobby
    LOBBY_TEXT         = (255, 255, 255)

# ------------------------------------------------------
# DÉTECTION DE L'ENVIRONNEMENT
# ------------------------------------------------------
# Initialiser pygame et le système vidéo uniquement si nécessaire
try:
    pygame.init()
    pygame.display.init()
    
    # Obtenir la résolution native de l'écran
    info = pygame.display.Info()
    NATIVE_WIDTH = info.current_w
    NATIVE_HEIGHT = info.current_h

    # On définit la taille logique de référence sur la même résolution
    GameConfig.BASE_WIDTH = NATIVE_WIDTH
    GameConfig.BASE_HEIGHT = NATIVE_HEIGHT
    
    # Détecter les écrans exceptionnellement grands (cinéma, etc.)
    IS_CINEMA_SCREEN = (NATIVE_WIDTH > 3000 or NATIVE_HEIGHT > 2000)
    IS_LARGE_SCREEN = (NATIVE_WIDTH > 1920 or NATIVE_HEIGHT > 1080)
    
    # Facteurs d'échelle
    SCALE_X = NATIVE_WIDTH / GameConfig.BASE_WIDTH
    SCALE_Y = NATIVE_HEIGHT / GameConfig.BASE_HEIGHT
    
    # Ajustement de la configuration selon la taille de l'écran
    if IS_CINEMA_SCREEN:
        logger.info(f"Écran de taille exceptionnelle détecté: {NATIVE_WIDTH}x{NATIVE_HEIGHT}")
        logger.info("Adaptation automatique des paramètres pour grand écran")
        
        # Adaptation du FPS pour les grands écrans (plus exigeants)
        if NATIVE_WIDTH * NATIVE_HEIGHT > 6000000:  # > 6 megapixels
            GameConfig.FPS = 30
            logger.info("FPS limité à 30 pour optimiser les performances sur écran géant")
except Exception as e:
    logger.warning(f"Erreur lors de l'initialisation de pygame: {e}")
    NATIVE_WIDTH = 1920
    NATIVE_HEIGHT = 1080
    IS_CINEMA_SCREEN = False
    IS_LARGE_SCREEN = False
    SCALE_X = 1.0
    SCALE_Y = 1.0

# Enregistrer l'environnement d'exécution
RUNNING_PLATFORM = sys.platform