"""
Module Player
Gère les joueurs et leurs caractéristiques (position, équipe, vitesse, etc.)
"""
import logging
from operator import truediv

from utils.config import PlayerConfig
from game_core.powerup import PowerUp, PowerUpType

logger = logging.getLogger("Player")

class Player:
    def __init__(self, pseudo, team, x=200, y=150):
        self.pseudo = pseudo
        self.x = x
        self.y = y
        self.team = team

        self.paint_power = PlayerConfig.PAINT_POWER
        self.health = PlayerConfig.MAX_HEALTH
        self.speed = 0.0

        self.damage = PlayerConfig.DAMAGE
        self.ammo = PlayerConfig.MAX_AMMO
        self.reload_time = PlayerConfig.RELOAD_TIME
        self.reload_timer = 0.0

        # Angle de visée (mis à jour en temps réel)
        self.aim_angle = None
        
        # Système de progression
        self.level = 1
        self.xp = 0
        self.xp_to_next_level = 100  # XP requise pour passer au niveau 2
        self.powerups = []  # Liste des powerups actifs
        self.pending_powerups = []  # Powerups en attente de sélection
        self.projectile_count = 1  # Nombre de projectiles tirés à la fois
        self.levelup_pending = False  # Indique si un level up est en attente
        
        logger.debug(f"Joueur {pseudo} créé (équipe {team})")

    def to_dict(self):
        """Convertit les données du joueur en dictionnaire pour la transmission."""
        return {
            "pseudo": self.pseudo,
            "x": self.x,
            "y": self.y,
            "team": self.team,
            "speed": self.speed,
            "paint_power": self.paint_power,
            "damage": self.damage,
            "ammo": self.ammo,
            "reload_time": self.reload_time,
            "reload_timer": self.reload_timer,
            "aim_angle": self.aim_angle,
            "level": self.level,
            "xp": self.xp,
            "xp_to_next_level": self.xp_to_next_level,
            "powerups": [p.to_dict() for p in self.powerups],
            "pending_powerups": [p.to_dict() for p in self.pending_powerups],
            "health": self.health,
            "projectile_count": self.projectile_count,
            "levelup_pending": self.levelup_pending
        }

    @classmethod
    def from_dict(cls, data: dict):
        """Reconstruit un Player à partir du dict renvoyé par to_dict."""
        p = cls(
            pseudo=data["pseudo"],
            x=data["x"],
            y=data["y"],
            team=data["team"]
        )
        p.speed = data.get("speed")
        p.paint_power = data.get("paint_power")
        p.damage = data.get("damage")
        p.ammo = data.get("ammo")
        p.reload_time = data.get("reload_time")
        p.reload_timer = data.get("reload_timer")
        p.aim_angle = data.get("aim_angle")

        p.level = data.get("level", 1)
        p.xp = data.get("xp", 0)
        p.xp_to_next_level = data.get("xp_to_next_level", PlayerConfig.BASE_XP_LEVEL)
        p.powerups = [PowerUp(PowerUpType[pup["type"]], pup["level"]) for pup in data.get("powerups", [])]
        p.pending_powerups = [PowerUp(PowerUpType[pup["type"]], pup["level"]) for pup in
                              data.get("pending_powerups", [])]
        p.levelup_pending = data.get("levelup_pending", False)
        p.health = data.get("health", p.health)
        return p


    def add_xp(self, amount):
        """
        Ajoute de l'expérience au joueur et vérifie s'il passe au niveau supérieur
        """
        self.xp += amount
        
        if self.xp >= self.xp_to_next_level:
            self.level_up()
            return True
        
        return False
    
    def level_up(self):
        """
        Fait monter le joueur d'un niveau et prépare les powerups à choisir
        """
        from powerup import get_random_powerups
        
        self.level += 1
        self.xp -= self.xp_to_next_level
        # Formule pour l'XP du prochain niveau (augmente progressivement)
        self.xp_to_next_level = int(self.xp_to_next_level * 1.5)
        
        logger.info(f"Joueur {self.pseudo} passe au niveau {self.level}!")
        
        # Types de powerups déjà possédés
        existing_types = [p.type for p in self.powerups]
        
        # Générer 2 powerups aléatoires à proposer au joueur
        self.pending_powerups = get_random_powerups(count=2, exclude_types=existing_types)
        self.levelup_pending = True
        
        logger.debug(f"Powerups proposés: {[p.name for p in self.pending_powerups]}")
    
    def select_powerup(self, index):
        """
        Sélectionne un powerup parmi ceux proposés
        """
        if not self.levelup_pending or index >= len(self.pending_powerups):
            return False
        
        selected_powerup = self.pending_powerups[index]
        
        # Vérifier si le joueur possède déjà ce type de powerup
        for i, powerup in enumerate(self.powerups):
            if powerup.type == selected_powerup.type:
                # Augmenter le niveau du powerup existant
                if self.powerups[i].level_up():
                    # Réappliquer le powerup avec son nouveau niveau
                    self.powerups[i].apply_to_player(self)
                    logger.info(f"Powerup {powerup.name} amélioré au niveau {powerup.level}")
                else:
                    logger.info(f"Powerup {powerup.name} déjà au niveau maximum")
                
                # Nettoyer les powerups en attente
                self.pending_powerups = []
                self.levelup_pending = False
                return True
        
        # Nouveau powerup
        selected_powerup.apply_to_player(self)
        self.powerups.append(selected_powerup)
        
        # Nettoyer les powerups en attente
        self.pending_powerups = []
        self.levelup_pending = False
        
        logger.info(f"Nouveau powerup sélectionné: {selected_powerup.name}")
        return True
    
    def take_damage(self, amount):
        """
        Inflige des dégâts au joueur
        
        Args:
            amount: Quantité de dégâts à infliger
            
        Returns:
            bool: True si le joueur est toujours en vie, False s'il est mort
        """
        self.health -= amount
        return True

    def is_dead(self):
        if self.health <= 0:
            return True
        return False