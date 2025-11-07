import pygame
import sys
import cv2
import pymunk
import numpy as np
import math
import random
from ball import Ball
from arc import ArcShape
from circle import Circle

# --- Constantes ---
LARGEUR_ECRAN = 9 * 100
HAUTEUR_ECRAN = 16 * 100
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
        self.center = (self.center_x, self.center_y)

        pygame.init()
        self.font = pygame.font.Font(None, 52)
        self.ecran = pygame.display.set_mode((self.largeur_ecran, self.hauteur_ecran))
        pygame.display.set_caption("Simulation Physique (R=Rotation, D=Détruire, Espace=Créer)")
        self.clock = pygame.time.Clock()

        self.ARC_UPDATE_FREQUENCY = 100
        self.time_since_last_physics_update = 0

        # Initialisation Enregistreur Vidéo
        self.video_writer = self._init_video_writer()
        self.frame_count = 0
        self.max_duration_sec = 15
        self.max_frames = FPS * self.max_duration_sec  # 60 * 15 = 900

        # Création des objets
        self.objets_dynamiques = []  # Liste pour les objets qui bougent (balles)
        self.objets_statiques = []   # Liste pour les objets fixes
        
        self.creer_objets_initiaux()
        
        self.running = True


    def creer_objets_initiaux(self):
        """ Crée les objets initiaux """
        circle = Circle(self.center_x, self.center_y, radius=200)
        self.objets_statiques.append(circle)
        self.creer_balle()


    def creer_balle(self):
        """ Crée une nouvelle balle à une position aléatoire """
        vx = random.randint(-200, 200) 
        vy = random.randint(-1, 1)

        balle = Ball(position=(self.center_x, self.center_y), radius=20, initial_velocity=(-1, -1))
        self.objets_dynamiques.append(balle)

    def uptdate_physics(self):
        for obj in self.objets_dynamiques:
            obj.update_physics
        
        for obj in self.objets_statiques:
            obj.handle_collision(self.objets_dynamiques[0])

    def run(self):
        """ Boucle de jeu principale """
        while self.running:
            # 1. Gérer les événements
            dt = self.clock.tick(FPS)

            self.frame_count += 1
            if self.frame_count >= self.max_frames:
                print(f"Atteint {self.max_frames} images ({self.max_duration_sec} sec). Arrêt de la simulation.")
                self.running = False
            
            self.handle_events()

            self.uptdate_physics()
          
            # 3. Dessiner les objets
            self.draw()

            # 4. Enregistrer la frame
            self.record_frame()
            
        # Fin de la boucle
        self.cleanup()

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
        
        # Dessiner les objets dynamiques

        for obj in self.objets_statiques:
            obj.draw(self.ecran)

        for obj in self.objets_dynamiques:
            obj.draw(self.ecran)


        # 1. Calculer le temps écoulé
        elapsed_sec = self.frame_count / FPS
        
        # 2. Créer le texte à afficher
        #    (le .2f formate le nombre pour n'avoir que 2 décimales)
        text_to_display = f"Comment the next thing to add to the animation"
        
        # 3. Rendre le texte sur une nouvelle Surface
        #    (True = anticrénelage, BLANC = couleur (défini en haut de votre script))
        text_surface = self.font.render(text_to_display, True, BLANC)
        
        # 4. Obtenir le rectangle du texte et le positionner
        #    (ici, on le place en haut à gauche avec 10px de marge)
        text_rect = text_surface.get_rect(topleft=(45, 200))
        
        # 5. Dessiner la surface du texte sur l'écran principal
        self.ecran.blit(text_surface, text_rect)


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
    game.run()