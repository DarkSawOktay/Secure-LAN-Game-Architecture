"""
Module PowerUp
Gère les powerups et leurs effets sur les joueurs
"""
import logging
import random
from enum import Enum, auto

logger = logging.getLogger("PowerUp")

class PowerUpType(Enum):
    """Types de powerups disponibles"""
    TRIPLE_SHOT = auto()       # Tir triple
    LONG_SHOT = auto()         # Tir longue portée
    SPEED_BOOST = auto()       # Boost de vitesse
    PAINT_AREA = auto()        # Plus grande surface de peinture

class PowerUp:
    """
    Classe PowerUp pour gérer les améliorations des joueurs.
    """
    def __init__(self, powerup_type, level=1):
        self.type = powerup_type
        self.level = level
        self.max_level = 3  # Maximum 3 niveaux par powerup
        
        # Informations pour l'affichage
        self.name = self._get_name()
        self.description = self._get_description()
        self.icon = None  # Pour une future implémentation d'icônes
        
    def _get_name(self):
        """Retourne le nom du powerup"""
        names = {
            PowerUpType.TRIPLE_SHOT: "Tir Multiple",
            PowerUpType.LONG_SHOT: "Tir Multiple",
            PowerUpType.SPEED_BOOST: "Vitesse Améliorée",
            PowerUpType.PAINT_AREA: "Grande Peinture"
        }
        return names.get(self.type, "Powerup Inconnu")
    
    def _get_description(self):
        """Retourne la description du powerup selon son niveau"""
        descriptions = {
            PowerUpType.TRIPLE_SHOT: [
                "Tire 2 projectiles à la fois",
                "Tire 3 projectiles à la fois",
                "Tire 4 projectiles à la fois"
            ],
            PowerUpType.LONG_SHOT: [
                "Portée de 400",
                "Portée de 500",
                "Portée de 600"
            ],
            PowerUpType.SPEED_BOOST: [
                "Vitesse +10%",
                "Vitesse +20%",
                "Vitesse +30%"
            ],
            PowerUpType.PAINT_AREA: [
                "Surface de peinture +15%",
                "Surface de peinture +30%",
                "Surface de peinture +50%"
            ]
        }
        
        type_descriptions = descriptions.get(self.type, ["Effet inconnu"])
        level_index = min(self.level - 1, len(type_descriptions) - 1)
        return type_descriptions[level_index]
    
    def apply_to_player(self, player):
        """
        Applique l'effet du powerup au joueur
        
        Args:
            player: L'objet joueur à modifier
        """
        if self.type == PowerUpType.TRIPLE_SHOT:
            # Nombre de projectiles basé sur le niveau (2, 3, ou 4)
            player.projectile_count = 1 + self.level

        elif self.type == PowerUpType.LONG_SHOT:
            # Portée de tir: 500, 600, 700
            player.portee += 100 * (self.level - 1)
            
        elif self.type == PowerUpType.SPEED_BOOST:
            # Bonus de vitesse: +10%, +20%, +30%
            boost_factor = 1.0 + (self.level * 0.1)
            player.base_speed = player.base_speed * boost_factor
            
        elif self.type == PowerUpType.PAINT_AREA:
            # Surface de peinture: +15%, +30%, +50%
            area_bonus = 1.0 + (self.level * 0.15 + (0.05 if self.level == 3 else 0))
            player.radius = int(player.radius * area_bonus)
            player.paint_power = player.paint_power * area_bonus

        logger.debug(f"PowerUp appliqué à {player.pseudo}: {self.name} (Niveau {self.level})")
        
    def level_up(self):
        """
        Augmente le niveau du powerup s'il n'a pas atteint le niveau maximum
        """
        if self.level < self.max_level:
            self.level += 1
            self.name = self._get_name()
            self.description = self._get_description()
            return True
        return False
        
    def to_dict(self):
        """Convertit le powerup en dictionnaire pour la transmission"""
        return {
            "type": self.type.name,
            "level": self.level,
            "name": self.name,
            "description": self.description
        }

def get_random_powerups(count=2, exclude_types=None):
    """
    Génère une liste de powerups aléatoires
    """
    all_types = list(PowerUpType)
    available_types = [t for t in all_types if exclude_types is None or t not in exclude_types]
    
    if len(available_types) < count:
        # S'il n'y a pas assez de types disponibles, compléter avec des doublons
        additional_types = random.choices(all_types, k=count-len(available_types))
        available_types.extend(additional_types)
    
    selected_types = random.sample(available_types, count)
    return [PowerUp(t) for t in selected_types]
