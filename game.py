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
        self.max_duration_sec = 45
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

            # 4. Variables de gestion (Système de file d'attente)
            self.music_playback_head = 0.0      # Où en est-on dans le morceau (en sec)
            self.music_window_timer = 0         # Timer (en frames) de la fenêtre de 1s EN COURS
            self.music_windows_queued = 0       # Nb de fenêtres de 1s en ATTENTE
            self.music_window_duration_sec = 0.5
            self.music_window_duration_frames = int(self.music_window_duration_sec * FPS)

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
        collision_this_frame = False
        for obj in self.objets_dynamiques:
            obj.update_physics()
        
        for obj in self.objets_statiques:
            # On vérifie s'il y a collision
            if obj.handle_collision(self.objets_dynamiques[0]):
                # 1. Jouer le son (pour l'entendre en direct)
                # self.bounce_sound.play()
                # 2. Enregistrer le son dans notre piste audio master
                # self.record_sfx_at_current_frame()
                collision_this_frame = True

        # Ne rien faire si la musique n'a pas chargé
        if self.music_length_sec <= 0:
            return

        # 1. Détection de collision : Ajouter à la file d'attente
        if collision_this_frame:
            if self.music_windows_queued < 3:
                self.music_windows_queued += 1
                print(f"Collision ! Fenêtre ajoutée à la file. (Total en attente: {self.music_windows_queued})")

        # 2. Gestion du timer
        
        # Si une fenêtre est activement en cours de lecture
        if self.music_window_timer > 0:
            self.music_window_timer -= 1 # On la décompte
            
            # Si elle VIENT de se terminer (timer atteint 0)
            if self.music_window_timer == 0:
                # On avance la tête de lecture pour la PROCHAINE fenêtre
                self.music_playback_head += self.music_window_duration_sec
                
                # Gérer le bouclage (looping)
                if self.music_playback_head >= self.music_length_sec:
                    self.music_playback_head = 0.0
                
                print(f"Fenêtre musique terminée. Prochaine reprise à {self.music_playback_head:.2f}s")
        
        # Si aucune fenêtre n'est en cours ET qu'il y en a en attente
        if self.music_window_timer == 0 and self.music_windows_queued > 0:
            # On "consomme" une fenêtre de la file d'attente
            self.music_windows_queued -= 1
            # On démarre le timer pour 1 seconde
            self.music_window_timer = self.music_window_duration_frames
            print(f"Démarrage d'une fenêtre musique (chunk à {self.music_playback_head:.2f}s). (Restant en attente: {self.music_windows_queued})")
    
    
    def record_background_music(self):
        """
        Mixe la musique de fond dans la master_audio_track
        si la fenêtre de musique est active.
        """
        # Ne rien faire si la fenêtre n'est pas active ou si la musique n'a pas chargé
        if self.music_window_timer <= 0 or self.music_length_sec <= 0:
            return

        # 1. Calculer combien d'échantillons audio représentent cette image
        samples_per_frame = int(self.sample_rate / FPS)
        
        # 2. Trouver la position de DESTINATION (où écrire dans le master)
        start_dest_sample = int(self.frame_count * (self.sample_rate / FPS))
        end_dest_sample = start_dest_sample + samples_per_frame
        
        # 3. Gérer le débordement de fin de vidéo
        if start_dest_sample >= len(self.master_audio_track):
            return # On a dépassé la fin de la vidéo
        
        actual_chunk_len = samples_per_frame
        if end_dest_sample > len(self.master_audio_track):
            end_dest_sample = len(self.master_audio_track)
            actual_chunk_len = end_dest_sample - start_dest_sample
            if actual_chunk_len <= 0: return

        # 4. Trouver la position SOURCE (où lire dans le fichier musique)
        # Temps (en sec) dans la fenêtre de 1s actuelle
        frames_elapsed = self.music_window_duration_frames - self.music_window_timer
        time_into_window_sec = frames_elapsed / FPS # <-- MODIFIÉ
        # Temps (en sec) absolu dans le fichier musique
        current_music_time_sec = self.music_playback_head + time_into_window_sec
        
        start_source_sample = int(current_music_time_sec * self.sample_rate)
        
        # 5. Obtenir le morceau audio de la SOURCE (gérer le bouclage)
        music_array_len = len(self.music_sound_array)
        
        # Appliquer le modulo pour boucler
        start_source_sample = start_source_sample % music_array_len
        end_source_sample = start_source_sample + actual_chunk_len
        
        source_chunk = None
        if end_source_sample <= music_array_len:
            # Cas simple : le morceau est en un seul bloc
            source_chunk = self.music_sound_array[start_source_sample:end_source_sample]
        else:
            # Cas complexe : le morceau boucle (il est en deux parties)
            part1_len = music_array_len - start_source_sample
            part1 = self.music_sound_array[start_source_sample:]
            
            part2_len = end_source_sample - music_array_len
            part2 = self.music_sound_array[:part2_len]
            
            source_chunk = np.vstack((part1, part2)) # Combiner les deux parties

        # 6. Obtenir le morceau de DESTINATION (depuis le master)
        dest_chunk = self.master_audio_track[start_dest_sample:end_dest_sample]
        
        # 7. Mixer (ajouter les deux morceaux, avec 'clipping')
        mixed_audio = np.clip(
            dest_chunk.astype(np.int32) + source_chunk.astype(np.int32), 
            -32768, 
            32767
        )
        
        # 8. Réécrire le morceau mixé dans le master
        self.master_audio_track[start_dest_sample:end_dest_sample] = mixed_audio.astype(np.int16)
    
    def run(self):
        """ Boucle de jeu principale """
        while self.running:
            dt = self.clock.tick(FPS)

            if self.frame_count >= self.max_frames:
                print(f"Atteint {self.max_frames} images ({self.max_duration_sec} sec). Arrêt de la simulation.")
                self.running = False
            
            self.handle_events()
            self.uptdate_physics()
            self.record_background_music()
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