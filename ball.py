import pygame
import pymunk
import math

class Ball:
    def __init__(self, position, radius, space, mass=1, elasticity=1, friction=0.0,initial_velocity=(0, 0)):
        self.radius = radius
        self.space = space
        self.color = (0, 255, 0)
        self.ligne_color = (255, 0, 0)
        
        self.show_rotation = False

        # Création de la physique Pymunk
        moment_balle = pymunk.moment_for_circle(mass, 0, self.radius)
        self.body = pymunk.Body(mass, moment_balle)
        self.body.velocity = initial_velocity
        self.body.position = position
        
        self.shape = pymunk.Circle(self.body, self.radius)
        self.shape.elasticity = elasticity
        self.shape.friction = friction
        
        # Ajouter l'objet à l'espace physique
        self.space.add(self.body, self.shape)
        
    def draw(self, ecran):
        """ Dessine la balle sur l'écran Pygame """
        pos_x = int(self.body.position.x)
        pos_y = int(self.body.position.y)
        pygame.draw.circle(ecran, self.color, (pos_x, pos_y), self.radius)
        
        # Dessiner une ligne pour voir la rotation
        if self.show_rotation:
            end_x = pos_x + self.radius * math.cos(self.body.angle)
            end_y = pos_y + self.radius * math.sin(self.body.angle)
            pygame.draw.line(ecran, self.ligne_color, (pos_x, pos_y), (int(end_x), int(end_y)), 2)

    def destroy(self):
        """ Supprime la balle de l'espace physique """
        self.space.remove(self.shape, self.body)

    def rotate(self, angle_degrees):
        """ Applique une rotation (en degrés) au corps de la balle """
        self.body.angle += math.radians(angle_degrees)