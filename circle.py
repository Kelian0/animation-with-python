import pygame
import random
import math

class Circle:
    def __init__(self, x, y, radius, color=(255,255,255), line_width=1,frixion = 1.1):
        self.x = float(x)
        self.y = float(y)
        self.radius = float(radius)
        self.color = color
        self.line_width = line_width
        self.frixion = frixion

    def handle_collision(self, ball):
        """Vérifie et gère la collision avec la balle."""
        
        # Calculer la distance entre le centre du cercle et le centre de la balle
        dist_x = ball.x - self.x
        dist_y = ball.y - self.y
        distance = math.hypot(dist_x, dist_y) # Équivalent à sqrt(dist_x**2 + dist_y**2)
        
        # Distance de collision = Rayon du conteneur - Rayon de la balle
        collision_distance = self.radius - ball.radius
        
        # 1. Détection de la collision
        if distance > collision_distance:
            # La balle a dépassé la limite
            
            # 2. Correction de la position (pour éviter que la balle ne "coince")
            # On la replace sur le bord, le long du vecteur normal
            
            # Vecteur normal (normalisé)
            norm_x = dist_x / distance
            norm_y = dist_y / distance
            
            # Replacer la balle exactement sur le bord
            ball.x = self.x + norm_x * collision_distance
            ball.y = self.y + norm_y * collision_distance
            
            # 3. Réponse à la collision (Réflexion de la vélocité)
            
            # Calcul du produit scalaire (dot product) entre la vélocité et la normale
            # V . N
            dot_product = ball.vx * norm_x + ball.vy * norm_y
            
            # Formule de la réflexion: V_reflechi = V - 2 * (V . N) * N
            # On multiplie aussi par la restitution pour simuler la perte d'énergie
            reflect_vx = ball.vx - 2 * dot_product * norm_x
            reflect_vy = ball.vy - 2 * dot_product * norm_y
            
            # C'est une vélocité (en pixels/frame) à ajuster.
            base_vx = reflect_vx * self.frixion
            base_vy = reflect_vy * self.frixion
        
            # 2. Définir la "force" de l'aléatoire (en degrés)
            #    (ex: 10.0 signifie que l'angle variera de -10° à +10°)
            MAX_ANGLE_OFFSET_DEGREES = 10.0
            
            # 3. Convertir la vélocité de base en (vitesse, angle)
            # Vitesse = magnitude du vecteur
            speed = math.hypot(base_vx, base_vy) 
            # Angle = angle du vecteur (en radians)
            angle_rad = math.atan2(base_vy, base_vx) 
            
            # 4. Calculer le décalage aléatoire (en radians)
            max_offset_rad = math.radians(MAX_ANGLE_OFFSET_DEGREES)
            random_offset_rad = random.uniform(-max_offset_rad, max_offset_rad)
            
            # 5. Appliquer le décalage pour obtenir le nouvel angle
            new_angle_rad = angle_rad + random_offset_rad
            
            # 6. Reconvertir (nouvel angle, vitesse d'origine) en vx / vy
            ball.vx = speed * math.cos(new_angle_rad)
            ball.vy = speed * math.sin(new_angle_rad)

            MAX_SPEED = 25.0 

            # 1. Calculer la vitesse actuelle (magnitude)
            #    math.hypot(vx, vy) est équivalent à sqrt(vx**2 + vy**2)
            current_speed = math.hypot(ball.vx, ball.vy)
            
            # 2. Vérifier si on dépasse la limite
            if current_speed > MAX_SPEED:
                # 3. Calculer le ratio de réduction
                #    (ex: si speed=30 et MAX=25, ratio = 25/30 = 0.83)
                scale_factor = MAX_SPEED / current_speed
                
                # 4. Réduire les deux composantes de la vélocité
                ball.vx *= scale_factor
                ball.vy *= scale_factor

            return True 
        return False

    def draw(self, screen):
        """Dessine le cercle conteneur."""
        pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), int(self.radius), self.line_width)



if __name__ == "__main__":
    print("Création d'un espace de test pour visualiser un arc avec Pygame")
    pygame.init()
    ecran = pygame.display.set_mode((800, 600))
    pygame.display.set_caption("Arc de cercle avec Pygame")
    clock = pygame.time.Clock()
    running = True

    circle = Circle(x=400, y=300, radius=10)

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        ecran.fill((0, 0, 0))
        circle.draw(ecran)
        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
