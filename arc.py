import math
import pygame
import pymunk

class ArcShape:
    """
    Crée un arc KINEMATIC (mobile mais non affecté par la physique)
    basé sur un centre, un rayon, des angles et des segments.
    """
    def __init__(self, center, radius, angle_start_deg, angle_end_deg, num_segments, space,
                 thickness=2, elasticity=1.0, friction=0.5, color=(200, 200, 200)):
        
        self.radius = radius
        self.angle_start_deg = angle_start_deg
        self.angle_end_deg = angle_end_deg
        self.num_segments = num_segments
        self.space = space
        self.center = center
        
        # Paramètres d'apparence
        self.thickness = thickness
        self.color = color

        # Paramètres de physique 
        self.elasticity = elasticity
        self.friction = friction

        # --- Changement KINEMATIC ---
        # 1. Créer un corps KINEMATIC
        # (se déplace selon notre code, mais n'est pas affecté par la gravité/collisions)
        self.body = pymunk.Body(body_type=pymunk.Body.KINEMATIC)
        self.body.position = center
        self.space.add(self.body)
        
        # self.points_local_coords garde les points RELATIFS au centre du corps
        # (ils ne changeront jamais, même si le corps tourne)
        self.points_local_coords = []
        self.segments_physics = []
        
        # 2. Construire les formes attachées à ce corps
        self._build_shape()

    def _build_shape(self):
        """ 
        Construit les segments physiques attachés au corps.
        Les coordonnées sont RELATIVES au centre du corps (self.body.position).
        """
        # Nettoyer les anciens segments s'ils existent
        if self.segments_physics:
            self.space.remove(*self.segments_physics)
            self.segments_physics = []
            
        point_precedent = None
        
        start_rad = math.radians(self.angle_start_deg)
        end_rad = math.radians(self.angle_end_deg)

        for i in range(self.num_segments + 1):
            ratio = i / self.num_segments
            angle = start_rad + ratio * (end_rad - start_rad)
            
            # Coordonnées RELATIVES (locales) au corps
            # Note: +sin(angle) pour un "bol" (Y augmente vers le bas)
            x = self.radius * math.cos(angle)
            y = self.radius * math.sin(angle)
            
            current_point = pymunk.Vec2d(x, y)
            self.points_local_coords.append(current_point)
            
            if point_precedent is not None:
                # Attacher le segment au self.body KINEMATIC
                segment = pymunk.Segment(self.body, point_precedent, current_point, self.thickness)
                segment.elasticity = self.elasticity
                segment.friction = self.friction
                self.segments_physics.append(segment)
            
            point_precedent = current_point
        
        # Ajouter tous les nouveaux segments à l'espace
        self.space.add(*self.segments_physics)

    def draw(self, ecran):
        """ 
        Dessine l'arc en transformant les points locaux
        en points à l'écran (monde).
        """

        points = (self.center[0]-self.radius,self.center[1]-self.radius,self.radius,self.radius)
        pygame.draw.arc(ecran, self.color, points, 0, math.pi/2, width=0)


    def destroy(self):
        """ Supprime le corps et ses segments de l'espace """
        if self.segments_physics:
            self.space.remove(*self.segments_physics)
            self.segments_physics = []
        self.space.remove(self.body)

    def rotate(self, angle_degrees):
        """ 
        Fait tourner le corps KINEMATIC.
        BEAUCOUP plus rapide que de tout reconstruire.
        """
        self.body.angle += math.radians(angle_degrees)
    
    def set_radius(self, new_radius):
        """
        Met à jour le rayon de l'arc.
        C'est la SEULE opération qui force une reconstruction.
        """
        self.radius = new_radius
        self._build_shape() # Reconstruit les segments avec le nouveau rayon

if __name__ == "__main__":
    print("Création d'un espace de test pour visualiser un arc avec Pygame")
    pygame.init()
    ecran = pygame.display.set_mode((800, 600))
    pygame.display.set_caption("Arc de cercle avec Pygame")
    clock = pygame.time.Clock()
    running = True

    arc = ArcShape(center=(400, 300), radius=200, angle_start_deg=20, angle_end_deg=80, num_segments=100, space=pymunk.Space())
    arc.space.gravity = (0, 900)

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        ecran.fill((0, 0, 0))
        arc.draw(ecran)
        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
