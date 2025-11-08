import pygame
import sys
import cv2
import numpy as np
import math
import random
from ball import Ball
from arc import ArcShape
from circle import Circle

# --- AJOUTS POUR LA FUSION FINALE ---
import os
from moviepy import VideoFileClip, AudioFileClip
import scipy.io.wavfile as wavfile
# ---------------------------con--------


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
        self.center_x = self.largeur_ecran // 2
        self.center_y = self.hauteur_ecran // 2
        self.center = (self.center_x, self.center_y)

        # --- MODIFICATION DE L'INIT AUDIO ---
        # Nous devons définir un sample rate (qualité audio) constant
        self.sample_rate = 44100 
        self.channels = 2
        
        pygame.init()
        # Initialisation du mixer AVEC des paramètres fixes
        pygame.mixer.init(frequency=self.sample_rate, size=-16, channels=self.channels, buffer=2048)
        # ------------------------------------
        
        self.bounce_sound = pygame.mixer.Sound("fx/bounce_1.wav")
        self.font = pygame.font.Font(None, 52)
        self.ecran = pygame.display.set_mode((self.largeur_ecran, self.hauteur_ecran))
        pygame.display.set_caption("Simulation Physique")
        self.clock = pygame.time.Clock()

        self.frame_count = 0
        self.max_duration_sec = 15
        self.max_frames = FPS * self.max_duration_sec

        # --- AJOUTS : PISTE AUDIO MASTER ---
        self.music_file = "music/Evangelion.mp3" 
        self.music_length_sec = 0 # Sera > 0 si le chargement réussit
        
        try:
            # 1. Charger la musique comme un 'Sound'
            self.music_sound = pygame.mixer.Sound(self.music_file)
            self.music_length_sec = self.music_sound.get_length()
            
            # 2. Obtenir ses données NumPy
            self.music_sound_array = pygame.sndarray.array(self.music_sound)

            # 3. Assurer que la musique est aussi en stéréo (pour le mixage)
            if self.music_sound_array.ndim == 1:
                print("Audio: Fichier musique est MONO. Conversion en stéréo.")
                self.music_sound_array = np.column_stack([self.music_sound_array, self.music_sound_array])
            elif self.music_sound_array.shape[1] > self.channels:
                print(f"Audio: Fichier musique a {self.music_sound_array.shape[1]} canaux. Tronquage en stéréo.")
                self.music_sound_array = self.music_sound_array[:, :self.channels]
            elif self.music_sound_array.shape[1] < self.channels:
                self.music_sound_array = np.column_stack([self.music_sound_array[:, 0], self.music_sound_array[:, 0]])
            
            print(f"Musique de fond '{self.music_file}' chargée (pour enregistrement), durée: {self.music_length_sec:.2f}s")
            
            # 4. Variables de gestion (identiques à avant)
            self.is_music_window_active = False 
            self.music_window_timer = 0         
            self.music_playback_head = 0.0

        except Exception as e:
            print(f"--- ERREUR ---")
            print(f"Impossible de charger le fichier musique : '{self.music_file}'")
            print(f"Détail de l'erreur: {e}")

        # 1. Obtenir les données audio du son de rebond sous forme de tableau NumPy
        self.bounce_sound_array = pygame.sndarray.array(self.bounce_sound)
        
        # 2. S'assurer que le son est en stéréo (pour correspondre à notre master)
        if self.bounce_sound_array.ndim == 1:
            # Cas 1: C'est MONO. On le duplique en stéréo.
            print("Audio: Fichier son 'bounce.wav' est MONO. Conversion en stéréo.")
            self.bounce_sound_array = np.column_stack([self.bounce_sound_array, self.bounce_sound_array])
        
        elif self.bounce_sound_array.shape[1] > self.channels:
            # Cas 2: C'est multi-canal (ex: 8 canaux). On ne prend que les 2 premiers.
            print(f"Audio: Fichier son 'bounce.wav' a {self.bounce_sound_array.shape[1]} canaux. Tronquage en stéréo.")
            self.bounce_sound_array = self.bounce_sound_array[:, :self.channels] # Prend les 'self.channels' (2) premières colonnes
            
        elif self.bounce_sound_array.shape[1] < self.channels:
            # Cas 3 (rare): Le fichier a 1 canal mais est formaté en 2D (ex: shape (N, 1)).
            print(f"Audio: Fichier son 'bounce.wav' a 1 canal (formaté 2D). Conversion en stéréo.")
            self.bounce_sound_array = np.column_stack([self.bounce_sound_array[:, 0], self.bounce_sound_array[:, 0]])
            
        # (Si shape[1] == self.channels, il est déjà stéréo, on ne fait rien)
        
        # 3. Créer la piste audio master vide (15 sec de silence)
        total_samples = int(self.max_duration_sec * self.sample_rate)
        self.master_audio_track = np.zeros((total_samples, self.channels), dtype=np.int16)
        # -----------------------------------
        
        # Initialisation Enregistreur Vidéo
        self.video_writer = self._init_video_writer()

        # Création des objets
        self.objets_dynamiques = [] 
        self.objets_statiques = [] 
        self.creer_objets_initiaux()
        
        self.running = True

    # ... (creer_objets_initiaux, creer_balle restent inchangés) ...

    def creer_objets_initiaux(self):
        """ Crée les objets initiaux """
        circle = Circle(self.center_x, self.center_y, radius=200)
        self.objets_statiques.append(circle)
        self.creer_balle()

    def creer_balle(self):
        """ Crée une nouvelle balle à une position aléatoire """
        balle = Ball(position=(self.center_x, self.center_y), radius=20, initial_velocity=(-1, -1))
        self.objets_dynamiques.append(balle)


    # --- MODIFICATION DE LA PHYSIQUE POUR ENREGISTRER L'AUDIO ---
    def uptdate_physics(self): # Note: faute de frappe "uptdate" conservée
        for obj in self.objets_dynamiques:
            obj.update_physics()
        
        for obj in self.objets_statiques:
            # On vérifie s'il y a collision
            if obj.handle_collision(self.objets_dynamiques[0]):
                # 1. Jouer le son (pour l'entendre en direct)
                self.bounce_sound.play()
                # 2. Enregistrer le son dans notre piste audio master
                self.record_sfx_at_current_frame()

    # --- NOUVELLE MÉTHODE : RECORD_SFX ---
    def record_sfx_at_current_frame(self):
        """ Mixe le son de rebond dans la piste audio master à la position actuelle. """
        
        # 1. Calculer où commence le son (en "samples")
        start_sample = int(self.frame_count * (self.sample_rate / FPS))
        
        # 2. Déterminer la longueur du son
        sound_length = len(self.bounce_sound_array)
        end_sample = start_sample + sound_length
        
        # 3. Vérifier qu'on ne dépasse pas la fin de la vidéo (15 sec)
        if end_sample > len(self.master_audio_track):
            # Tronquer le son s'il dépasse
            sound_length = len(self.master_audio_track) - start_sample
            if sound_length <= 0:
                return # Le son commence après la fin, ne rien faire
            
            sound_data_to_mix = self.bounce_sound_array[:sound_length]
        else:
            sound_data_to_mix = self.bounce_sound_array

        # 4. "Mixer" le son (ajouter les valeurs)
        # On utilise des int32 pour l'addition pour éviter les débordements (clipping)
        mix_region = self.master_audio_track[start_sample : start_sample + sound_length]
        
        mixed_audio = np.clip(
            mix_region.astype(np.int32) + sound_data_to_mix.astype(np.int32), 
            -32768, 
            32767
        )
        
        # 5. Réinsérer la partie mixée dans la piste master
        self.master_audio_track[start_sample : start_sample + sound_length] = mixed_audio.astype(np.int16)
    # ----------------------------------------
    
    def run(self):
        """ Boucle de jeu principale """
        while self.running:
            dt = self.clock.tick(FPS)

            if self.frame_count >= self.max_frames:
                print(f"Atteint {self.max_frames} images ({self.max_duration_sec} sec). Arrêt de la simulation.")
                self.running = False
            
            self.handle_events()
            self.uptdate_physics()
            self.draw()
            self.record_frame()
            
            # Important : incrémenter le frame_count APRÈS tout le traitement
            self.frame_count += 1 
            
        # Fin de la boucle
        self.cleanup()

    # ... (handle_events reste inchangé) ...
    def handle_events(self):
        """ Gère les entrées utilisateur (clavier, souris) """
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    self.creer_balle()

    # ... (draw reste inchangé) ...
    def draw(self):
        """ Dessine tous les éléments du jeu """
        s = pygame.Surface((self.largeur_ecran, self.hauteur_ecran))
        s.set_alpha(100) # J'ai mis 100, 1000 était trop élevé
        s.fill(NOIR)  
        self.ecran.blit(s, (0, 0))

        for obj in self.objets_statiques:
            obj.draw(self.ecran)
        for obj in self.objets_dynamiques:
            obj.draw(self.ecran)

        text_to_display = f"Comment the next thing to add to the animation"
        text_surface = self.font.render(text_to_display, True, BLANC)
        text_rect = text_surface.get_rect(topleft=(45, 200))
        self.ecran.blit(text_surface, text_rect)

        pygame.display.flip()
        
    def record_frame(self):
        """ Capture l'écran et l'écrit dans le fichier vidéo """
        frame_pixels = pygame.surfarray.array3d(self.ecran)
        frame_transposed = np.transpose(frame_pixels, (1, 0, 2))
        frame_bgr = cv2.cvtColor(frame_transposed, cv2.COLOR_RGB2BGR)
        self.video_writer.write(frame_bgr)


    # --- MODIFICATION DE L'INIT VIDÉO ---
    def _init_video_writer(self):
        """ Configure et retourne l'objet VideoWriter d'OpenCV """
        
        # On enregistre la vidéo dans un fichier temporaire
        self.temp_video_filename = 'temp_video_sans_son.mp4' 
        
        fourcc = cv2.VideoWriter_fourcc(*'mp4v') 
        return cv2.VideoWriter(self.temp_video_filename, fourcc, FPS, (self.largeur_ecran, self.hauteur_ecran))
    

    # --- MODIFICATION DE CLEANUP POUR LA FUSION ---
    def cleanup(self):
        """ Termine l'enregistrement, génère l'audio, fusionne, et ferme Pygame """
        
        print("Finalisation (Étape 1/3 : Écriture de la vidéo)...")
        self.video_writer.release() 

        print("Finalisation (Étape 2/3 : Écriture de l'audio SFX)...")
        self.temp_audio_filename = "temp_sfx_track.wav"
        
        video_clip = None
        audio_clip = None
        
        try:
            wavfile.write(self.temp_audio_filename, self.sample_rate, self.master_audio_track)

            print("Finalisation (Étape 3/3 : Fusion vidéo et audio)...")
            
            video_clip = VideoFileClip(self.temp_video_filename)
            audio_clip = AudioFileClip(self.temp_audio_filename)
            
            # --- CORRECTION ICI ---
            # 'set_audio' (v1) devient 'with_audio' (v2)
            final_clip = video_clip.with_audio(audio_clip)
            # --------------------
            
            final_video_filename = "simulation_physique_AVEC_SFX.mp4"
            
            final_clip.write_videofile(
                final_video_filename, 
                codec='libx264',
                audio_codec='aac',
                temp_audiofile='temp-audio.m4a',
                remove_temp=True,
                fps=FPS
            )
            
            print(f"Vidéo finale avec SFX sauvegardée sous : {final_video_filename}")

        except Exception as e:
            print(f"\n--- ERREUR LORS DE LA FUSION AUDIO/VIDÉO ---")
            print(f"Erreur : {e}")
            print("\nVérifiez que 'scipy' et 'moviepy' sont installés.")
            print(f"\nLe fichier vidéo *sans son* est disponible ici : {self.temp_video_filename}")
            print(f"Le fichier audio *SFX seul* est disponible ici : {self.temp_audio_filename}")
        
        finally:
            print("Libération des fichiers temporaires...")
            if video_clip:
                video_clip.close()
            if audio_clip:
                audio_clip.close()
            
            try:
                if os.path.exists(self.temp_video_filename) and 'e' not in locals():
                    os.remove(self.temp_video_filename)
                if os.path.exists(self.temp_audio_filename) and 'e' not in locals():
                    os.remove(self.temp_audio_filename)
            except PermissionError as pe:
                print(f"ERREUR : Toujours impossible de supprimer les fichiers temporaires. {pe}")

        pygame.quit()
        sys.exit()

# --- Point d'entrée du script ---
if __name__ == "__main__":
    game = Game()
    game.run()