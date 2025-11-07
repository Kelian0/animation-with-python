import math
import pygame
import pymunk

class ArcShape:
    """
    Crée un arc KINEMATIC (mobile mais non affecté par la physique)
    basé sur un centre, un rayon, des angles et des segments.
    """
    def __init__(self, center, radius, angle_start_deg, angle_end_deg, space,
                 thickness=1, elasticity=1.0, friction=0.5, color=(200, 200, 200)):
        
        self.radius = radius
        self.angle_start_deg = angle_start_deg
        self.angle_end_deg = angle_end_deg
        self.angle_start_rad = math.radians(angle_start_deg)
        self.angle_end_rad = math.radians(angle_end_deg)
        self.space = space
        self.center = center
        
        # Paramètres d'apparence
        self.thickness = thickness
        self.color = color

        # Paramètres de physique 
        self.elasticity = elasticity
        self.friction = friction
        self.radius_div = 1
        self.num_segments = max(10, int(self.radius / self.radius_div))

        # --- Changement KINEMATIC ---
        # 1. Créer un corps KINEMATIC
        # (se déplace selon notre code, mais n'est pas affecté par la gravité/collisions)
        self.body = pymunk.Body(body_type=pymunk.Body.KINEMATIC)
        self.body.position = center
        self.shapes = self._build_shapes()

        self.space.add(self.body, *self.shapes)

    def _get_point_on_arc(self, angle_rad):
        """ Calcule les coordonnées locales d'un point sur l'arc. """
        # Utilisation correcte du rayon
        x = self.radius * math.cos(angle_rad)
        y = self.radius * math.sin(angle_rad)
        return pymunk.Vec2d(x, y) # Utiliser pymunk.Vec2 est plus propre

    def _build_shapes(self): # Renommé au pluriel
        """ 
        Construit les segments physiques attachés au corps.
        RETOURNE : Une liste [pymunk.Segment]
        """
        shapes_list = []
        points = []

        # Calculer la plage d'angle totale
        angle_range = self.angle_end_rad - self.angle_start_rad
        
        # 1. Générer tous les points (vertices) de l'arc
        for i in range(self.num_segments + 1):
            # Calculer l'angle actuel (interpolation linéaire)
            angle = self.angle_start_rad + (angle_range * i / self.num_segments)
            points.append(self._get_point_on_arc(angle))

        # 2. Créer les Segments entre les points successifs
        for i in range(self.num_segments):
            start_point = points[i]
            end_point = points[i+1]
            segment = pymunk.Segment(self.body, start_point, end_point, self.thickness)
            segment.friction = self.friction
            segment.elasticity = self.elasticity
            shapes_list.append(segment)
            

        return shapes_list


        


    def draw(self, ecran):
        """ 
        Dessine l'arc en transformant les points locaux
        en points à l'écran (monde).
        """
        rad_start = (2*math.pi * self.angle_start_deg) /360
        rad_end = (2*math.pi *self.angle_end_deg) /360
        points = (self.center[0]-self.radius,self.center[1]-self.radius,2*self.radius,2*self.radius)
        pygame.draw.arc(ecran, self.color, points, rad_start, rad_end, width=1)



    def rotate(self, angle_degrees):
        """ 
        Fait tourner le corps KINEMATIC.
        BEAUCOUP plus rapide que de tout reconstruire.
        """
        self.angle_start_deg = self.angle_start_deg + angle_degrees % (2*math.pi )
        self.angle_end_deg = self.angle_end_deg + angle_degrees % (2*math.pi )

        self.body.angle += math.radians(angle_degrees)
    
    def set_radius(self, new_radius):
        """
        Met à jour le rayon de l'arc.
        C'est la SEULE opération qui force une reconstruction.
        """
        self.space.remove(*self.shapes)
        
        # 2. Mettre à jour les propriétés internes de l'objet
        self.radius = new_radius
        
        # 3. [Optionnel mais recommandé] Mettre à jour le nombre de segments
        #    Si le rayon augmente beaucoup, il faut plus de segments
        #    pour que l'arc reste lisse.
        self.num_segments = max(10, int(self.radius / self.radius_div))
        
        # 4. Reconstruire la liste des formes
        #    _build_shapes() utilisera automatiquement le nouveau self.radius
        self.shapes = self._build_shapes()
        
        # 5. Ajouter les NOUVELLES formes à l'espace
        #    (Le corps y est déjà)
        self.space.add(*self.shapes)

    def destroy(self):
        """ Supprime le corps et ses segments de l'espace """
        self.space.remove(self.body)



if __name__ == "__main__":
    print("Création d'un espace de test pour visualiser un arc avec Pygame")
    pygame.init()
    ecran = pygame.display.set_mode((800, 600))
    pygame.display.set_caption("Arc de cercle avec Pygame")
    clock = pygame.time.Clock()
    running = True

    arc = ArcShape(center=(400, 300), radius=200, angle_start_deg=0, angle_end_deg=320, space=pymunk.Space())

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        ecran.fill((0, 0, 0))
        arc.draw(ecran)
        arc.rotate(1)
        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
