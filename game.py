import pygame
import sys
import cv2
import pymunk
import numpy as np
import math
import random
from ball import Ball
from arc import ArcShape

# --- Constantes ---
LARGEUR_ECRAN = 9 * 50
HAUTEUR_ECRAN = 16 * 50
BLANC = (255, 255, 255)
NOIR = (0, 0, 0)
ROUGE = (255, 0, 0)
FPS = 60


# --- Classe principale du Jeu ---
class Game:
    def __init__(self,largeur_ecran = LARGEUR_ECRAN,hauteur_ecran = HAUTEUR_ECRAN):
        # Initialisation Pygame
        self.largeur_ecran = largeur_ecran
        self.hauteur_ecran = hauteur_ecran
        self.particles = []
        self.center_x = self.largeur_ecran // 2
        self.center_y = self.hauteur_ecran // 2

        pygame.init()
        self.ecran = pygame.display.set_mode((self.largeur_ecran, self.hauteur_ecran))
        pygame.display.set_caption("Simulation Physique (R=Rotation, D=Détruire, Espace=Créer)")
        self.clock = pygame.time.Clock()

        self.arc_update_counter = 0
        self.ARC_UPDATE_FREQUENCY = 1

        # Initialisation Pymunk
        self.space = pymunk.Space()
        self.space.gravity = (0, 900)

        # Initialisation Enregistreur Vidéo
        self.video_writer = self._init_video_writer()

        # Création des objets
        self.objets_dynamiques = []  # Liste pour les objets qui bougent (balles)
        self.arcs = []   # Liste pour les objets fixes
        
        self.creer_objets_initiaux()
        
        self.running = True


    def creer_objets_initiaux(self):
        """ Crée l'arc initial """
        for i in range(1,50):
            arc = ArcShape(
                center=(self.center_x, self.center_y ), 
                radius=100+i*50, 
                angle_start_deg=0+i*5, 
                angle_end_deg=300+i*5, 
                num_segments=100, 
                space=self.space
            )
            self.arcs.append(arc) # ArcShape a sa propre méthode draw
    
    def check_arc_states(self,arc):
        """
        Vérifie si le balle est à l'intérieur ou à l'extérieur
        du cercle imaginaire de l'arc.
        """
        
        # --- MODIFICATION REQUISE ICI ---
        # Obtenir les propriétés du cercle de l'arc
        # Le centre n'est plus fixe, il est sur le corps de l'arc
        arc_center = arc.body.position 
        # --- FIN DE LA MODIFICATION ---
        
        # On utilise le carré du rayon pour éviter de calculer une racine carrée (plus rapide)
        radius_sqrd = arc.radius**2

        all_ball_outside = True 
        
        for balle in self.objets_dynamiques:
            # Obtenir la position de la balle
            ball_pos = balle.body.position
            
            # Calculer la distance au carré
            distance_sqrd = (ball_pos - arc_center).get_length_sqrd()
            
            # L'état actuel est-il "dehors" ?
            is_currently_outside = distance_sqrd > radius_sqrd
            all_ball_outside = all_ball_outside and is_currently_outside

        return all_ball_outside

    def creer_balle(self):
        """ Crée une nouvelle balle à une position aléatoire """
        vx = random.randint(-200, 200) 
        # vy: vitesse verticale (poussée vers le haut, donc négative)
        vy = random.randint(-400, -200)
        balle = Ball(position=(self.center_x, self.center_y), radius=10, space=self.space, initial_velocity=(vx, vy))
        self.objets_dynamiques.append(balle)

    def run(self):
        """ Boucle de jeu principale """
        while self.running:
            # 1. Gérer les événements
            self.handle_events()
            
            # 2. Mettre à jour la physique
            self.space.step(1.0 / FPS)
          
            self.update_arcs() # Appeler notre nouvelle méthode

            # 3. Dessiner les objets
            self.draw()

            # 4. Enregistrer la frame
            self.record_frame()

            # 5. Contrôler le FPS
            self.clock.tick(FPS)
            
        # Fin de la boucle
        self.cleanup()

    def update_arcs(self):
        """
        Met à jour la rotation, la taille et vérifie l'état de tous les arcs.
        C'est une fonction coûteuse, à ne pas appeler à chaque frame.
        """
        # On itère sur une COPIE de la liste (.copy())
        # car on va modifier la liste originale (self.arcs) en cours de route.
        for arc in self.arcs.copy():
            # Utilise la nouvelle méthode de rotation (très rapide)
            arc.rotate(1) 
            
            new_radius = arc.radius - 0.1
            arc.set_radius(new_radius)

            # Si l'arc est devenu trop petit, on le détruit
            if arc.radius < 10:
                self.create_arc_explosion(arc) 
                arc.destroy()
                self.arcs.remove(arc) 
                continue # Passer à l'arc suivant

            # Si toutes les balles sont sorties, on le détruit
            # Note: Le centre est maintenant 'arc.body.position'
            if self.check_arc_states(arc):
                self.create_arc_explosion(arc)
                arc.destroy()
                self.arcs.remove(arc)


    def creer_particule(self, x, y):
        """
        Crée une particule unique avec une vélocité et une durée de vie.
        Format: [position, vélocité, durée_de_vie]
        """
        position = [x, y]
        # Donner une vélocité d'explosion aléatoire (dans toutes les directions)
        velocite = [random.uniform(-0.2, 0.2), random.uniform(-.2, .2)]
        # Durée de vie en nombre de frames
        duree_de_vie = random.randint(30, 60) # Dure entre 0.5 et 1 seconde
        
        self.particles.append([position, velocite, duree_de_vie])

    def create_arc_explosion(self, arc):
        """
        Crée une explosion de particules sur toute la longueur d'un arc.
        """
        print(f"Création d'une explosion pour l'arc (rayon {arc.radius:.0f})")
        # On crée une particule tous les N points pour ne pas surcharger
        points_a_creer = arc.points_for_drawing[::1] # '::3' prend 1 point sur 3
        
        for point in points_a_creer:
            self.creer_particule(point[0], point[1])

    def handle_events(self):
        """ Gère les entrées utilisateur (clavier, souris) """
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            
    

            if event.type == pygame.KEYDOWN:
                
                # Appuyer sur ESPACE pour créer une nouvelle balle
                if event.key == pygame.K_SPACE:
                    self.creer_balle()
                
                # Appuyer sur D pour détruire la balle la plus ancienne
                if event.key == pygame.K_d:
                    if self.objets_dynamiques:
                        balle_a_detruire = self.objets_dynamiques.pop(0) # Prend la première de la liste
                        balle_a_detruire.destroy()

    def draw(self):
        """ Dessine tous les éléments du jeu """
        s = pygame.Surface((self.largeur_ecran, self.hauteur_ecran))
        s.set_alpha(90) # Plus ce chiffre est bas (ex: 10), plus la traînée est longue
        s.fill(NOIR)    # La couleur qui "estompe"
        self.ecran.blit(s, (0, 0))
        
        # Dessiner les objets statiques
        for obj in self.arcs:
                obj.draw(self.ecran) # Soit la méthode draw de l'objet, soit la lambda du sol
            
        # Dessiner les objets dynamiques
        for obj in self.objets_dynamiques:
            obj.draw(self.ecran)

        for particule in self.particles.copy():
            # 1. Mettre à jour la position
            particule[0][0] += particule[1][0] # pos_x += vel_x
            particule[0][1] += particule[1][1] + 1# pos_y += vel_y
            
            # 2. Réduire la durée de vie
            particule[2] -= 1 # durée_de_vie -= 1
            
            # 3. Supprimer si la durée de vie est écoulée
            if particule[2] <= 0:
                self.particles.remove(particule)
            else:
                # 4. Dessiner la particule (un simple cercle blanc)
                # On peut faire varier la taille ou la couleur avec la durée de vie
                couleur_particule = (100, 100, 100) # Blanc-gris
                pygame.draw.circle(self.ecran, couleur_particule, particule[0], 2)
        # --- FIN NOUVEAU ---
            
        pygame.display.flip()

    def record_frame(self):
        """ Capture l'écran et l'écrit dans le fichier vidéo """
        frame_pixels = pygame.surfarray.array3d(self.ecran)
        frame_transposed = np.transpose(frame_pixels, (1, 0, 2))
        frame_bgr = cv2.cvtColor(frame_transposed, cv2.COLOR_RGB2BGR)
        self.video_writer.write(frame_bgr)

    def _init_video_writer(self):
        """ Configure et retourne l'objet VideoWriter d'OpenCV """
        VIDEO_FILENAME = 'simulation_physique.mp4'
        fourcc = cv2.VideoWriter_fourcc(*'mp4v') 
        return cv2.VideoWriter(VIDEO_FILENAME, fourcc, FPS, (self.largeur_ecran, self.hauteur_ecran))
    
    def cleanup(self):
        """ Termine l'enregistrement et ferme Pygame """
        print("Finalisation de la vidéo...")
        self.video_writer.release()
        print(f"Vidéo sauvegardée.")
        pygame.quit()
        sys.exit()

# --- Point d'entrée du script ---
if __name__ == "__main__":
    game = Game()
    game.creer_balle() # Créer une balle au démarrage
    game.run()