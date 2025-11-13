import pygame
import pymunk
import math
import random

class Circle:
    def __init__(self, x, y, radius, color=(255,255,255), line_width=1):
        self.x = float(x)
        self.y = float(y)
        self.radius = float(radius)
        self.color = color
        self.line_width = line_width

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
            
            ball.vx = reflect_vx 
            ball.vy = reflect_vy

            ball.color = (random.randint(100, 255), random.randint(100, 255), random.randint(100, 255))

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
