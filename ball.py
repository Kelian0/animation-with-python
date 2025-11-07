import pygame
import pymunk
import math

class Ball:
    def __init__(self, position, radius, mass=1, elasticity=1, friction=0.0,initial_velocity=(0, 0),gravity=0.98):
        self.radius = radius
        self.color = (255, 255, 255)
        self.ligne_color = (255, 0, 0)
        self.x = position[0]
        self.y = position[1]
        self.vx = initial_velocity[0]
        self.vy = initial_velocity[1]

        self.gravity = gravity

        self.show_rotation = False

    def update_physics(self):
        """Met à jour la position et la vélocité de la balle."""
        # Appliquer la gravité
        self.vy += self.gravity
        
        # Mettre à jour la position
        self.x += self.vx
        self.y += self.vy
        
    def draw(self, ecran):
        """ Dessine la balle sur l'écran Pygame """
        pos_x = int(self.x)
        pos_y = int(self.y)
        pygame.draw.circle(ecran, self.color, (pos_x, pos_y), self.radius)
        
        # Dessiner une ligne pour voir la rotation
        if self.show_rotation:
            end_x = pos_x + self.radius * math.cos(self.body.angle)
            end_y = pos_y + self.radius * math.sin(self.body.angle)
            pygame.draw.line(ecran, self.ligne_color, (pos_x, pos_y), (int(end_x), int(end_y)), 2)

    def rotate(self, angle_degrees):
        """ Applique une rotation (en degrés) au corps de la balle """
        self.body.angle += math.radians(angle_degrees)