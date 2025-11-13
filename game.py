import pygame
import sys
import cv2
import numpy as np
import math
import random
import os
from tqdm import tqdm

# Bibliothèques pour la fusion vidéo/audio finale
from moviepy import VideoFileClip, AudioFileClip
import scipy.io.wavfile as wavfile

# Modules du projet
from ball import Ball
from arc import ArcShape
from circle import Circle
from sound_tools import SoundGenerator

# --- Constantes Globales ---
LARGEUR_ECRAN = 9 * 100
HAUTEUR_ECRAN = 16 * 100
BLANC = (255, 255, 255)
NOIR = (0, 0, 0)
ROUGE = (255, 0, 0)
FPS = 60
TEMPS_MAX_SEC = 15


# --- Classe principale du Jeu ---
class Game:
    def __init__(self, largeur_ecran=LARGEUR_ECRAN, hauteur_ecran=HAUTEUR_ECRAN):
        
        # --- Configuration de la fenêtre (virtuelle) ---
        self.largeur_ecran = largeur_ecran
        self.hauteur_ecran = hauteur_ecran
        self.center_x = self.largeur_ecran // 2
        self.center_y = self.hauteur_ecran // 2
        self.center = (self.center_x, self.center_y)

        # --- Configuration Audio ---
        self.sample_rate = 44100  # Qualité CD standard
        self.channels = 2         # Stéréo
        self.sound_gen = SoundGenerator(sample_rate=self.sample_rate, channels=self.channels)


        # --- Mode "Headless" (Sans Fenêtre) ---
        # Force Pygame à utiliser un "faux" pilote vidéo
        # pour ne pas ouvrir de fenêtre visible.
        os.environ['SDL_VIDEODRIVER'] = 'dummy'
        
        
        pygame.init()
        # Initialise le mixer audio avec nos paramètres fixes
        pygame.mixer.init(frequency=self.sample_rate, size=-16, channels=self.channels, buffer=2048)
        
        # --- Chargement des Médias ---
        self.font = pygame.font.Font(None, 52)
        self.ecran = pygame.display.set_mode((self.largeur_ecran, self.hauteur_ecran))
        pygame.display.set_caption("Simulation Physique")
        
        # Pré-calculer le rendu du texte statique
        self.static_text_surface = self.font.render("Comment the next thing to add to the animation", True, BLANC)
        self.static_text_rect = self.static_text_surface.get_rect(topleft=(45, 200))

        # --- Chargement des Effets Sonores (SFX) ---
        # Charge le son de rebond et le convertit en tableau NumPy
        self.generated_sound_arrays = []
        frequencies_hz = [261.63, 293.66, 329.63, 392.00, 440.00, 523.25]
        
        for freq in frequencies_hz:
            # On utilise notre nouvelle classe !
            sound_array = self.sound_gen.generate_wave( # <--- MODIFIÉ
                frequency=freq,
                duration_sec=0.2,
                waveform='sawtooth', # Essayez 'square' ou 'sawtooth' !
                volume=0.7
            )
            self.generated_sound_arrays.append(sound_array)
            

        # --- Configuration de la Simulation ---
        self.clock = pygame.time.Clock()
        self.frame_count = 0
        self.max_duration_sec = TEMPS_MAX_SEC
        self.max_frames = FPS * self.max_duration_sec


        try:
            music_file = "music/future-8bit.mp3" # Mettez le chemin de VOTRE fichier
            music_volume = 0.5 # Volume de la musique (0.0 à 1.0)
            
            print(f"Audio: Chargement du fichier musique '{music_file}'...")
            music_sound = pygame.mixer.Sound(music_file)
            music_array = pygame.sndarray.array(music_sound)
            
            # 1. Conversion en Stéréo (au cas où)
            if music_array.ndim == 1:
                music_array = np.column_stack([music_array, music_array])
            elif music_array.shape[1] > self.channels:
                music_array = music_array[:, :self.channels]
            elif music_array.shape[1] < self.channels:
                 music_array = np.column_stack([music_array[:, 0], music_array[:, 0]])
            
            # 2. Calculer la longueur totale nécessaire
            master_len = int(self.max_duration_sec * self.sample_rate)
            music_len = len(music_array)
            
            # 3. Faire boucler la musique pour remplir la durée
            if music_len == 0:
                raise ValueError("Le fichier audio est vide.")
                
            num_repeats = int(np.ceil(master_len / music_len))
            looped_music_array = np.tile(music_array, (num_repeats, 1))
            
            # 4. Tronquer la musique bouclée à la longueur exacte
            looped_music_array = looped_music_array[:master_len]

            # 5. Appliquer le volume et assigner à la piste master
            # (On applique le volume avant de convertir en int16)
            self.master_audio_track = (looped_music_array * music_volume).astype(np.int16)
            
        except Exception as e:
            print(f"--- ERREUR ---")
            print(f"Impossible de charger le fichier musique : '{music_file}'")
            print(f"Détail de l'erreur: {e}")
            print("Génération d'une piste de silence à la place.")
            # Créer une piste de silence en cas d'échec
            total_samples = int(self.max_duration_sec * self.sample_rate)
            self.master_audio_track = np.zeros((total_samples, self.channels), dtype=np.int16)
        
        # Initialisation de l'enregistreur vidéo
        self.video_writer = self._init_video_writer()

        # Création des objets de la simulation
        self.objets_dynamiques = [] 
        self.objets_statiques = [] 
        self.creer_objets_initiaux()

    def creer_objets_initiaux(self):
        """ Crée les objets initiaux de la simulation (le cercle). """
        circle = Circle(self.center_x, self.center_y, radius=200)
        self.objets_statiques.append(circle)
        self.creer_balle()

    def creer_balle(self,x=None,y=None,initial_velocity=None):
        """ Crée une nouvelle balle et l'ajoute à la simulation. """
        if x is None and y is None:
            x = self.center_x
            y = self.center_y
        if initial_velocity is None:
            initial_velocity = (-1, 0)
        balle = Ball(position=(x, y), radius=20, initial_velocity=initial_velocity)
        self.objets_dynamiques.append(balle)

    def uptdate_physics(self): # (faute de frappe "uptdate" conservée)
        """ Met à jour la physique de tous les objets dynamiques. """
        for obj in self.objets_dynamiques:
            obj.update_physics()
        
        for obj in self.objets_statiques:
            # Si une collision est détectée (par handle_collision)

            for i,ball in enumerate(self.objets_dynamiques[0:100]):
                if obj.handle_collision(ball):
                    if i <= 10:
                        self.record_sfx_at_current_frame()

                    random_x = random.uniform(.7, 1.2)
                    random_y = random.uniform(.7, 1.2)
                    initial_velocity = [-ball.vx+random_x,-ball.vy + random_y]
                    initial_velocity = initial_velocity / np.linalg.norm(initial_velocity)

                    self.creer_balle(x=ball.x,y=ball.y,initial_velocity=(ball.vx*random_x,ball.vy*random_y))

    def run(self):
        """ Boucle de jeu principale (rendu). """
        
        print("--- Démarrage du rendu ---")
        
        # Utilise tqdm pour créer une barre de progression dans le terminal
        for self.frame_count in tqdm(range(self.max_frames), desc="[1/2] Simulation des frames", unit="frame"):
            
            self.uptdate_physics()
            self.draw()
            self.record_frame()
            
        print(f"Simulation terminée ({self.max_frames} frames).")
        
        # Lancer le processus de finalisation (fusion audio/vidéo)
        self.cleanup()

    def draw(self):
        """ Dessine tous les éléments du jeu sur l'écran (virtuel). """
        
        # Crée une surface noire semi-transparente pour l'effet de traînée
        s = pygame.Surface((self.largeur_ecran, self.hauteur_ecran))
        s.set_alpha(100) # (0=transparent, 255=opaque)
        s.fill(NOIR)  
        self.ecran.blit(s, (0, 0)) # Applique le "voile" noir

        # Dessine les objets
        for obj in self.objets_statiques:
            obj.draw(self.ecran)
        for obj in self.objets_dynamiques:
            obj.draw(self.ecran)

        # Dessine le texte statique (pré-calculé dans __init__)
        self.ecran.blit(self.static_text_surface, self.static_text_rect)
        
    def record_frame(self):
        """ Capture l'écran Pygame et l'écrit dans le fichier vidéo OpenCV. """
        
        # 1. Extraire les pixels de Pygame (format (Largeur, Hauteur, 3))
        frame_pixels = pygame.surfarray.array3d(self.ecran)
        
        # 2. Transposer en (Hauteur, Largeur, 3) (format NumPy/OpenCV)
        frame_transposed = np.transpose(frame_pixels, (1, 0, 2))
        
        # 3. Convertir de RGB (Pygame) à BGR (OpenCV)
        frame_bgr = cv2.cvtColor(frame_transposed, cv2.COLOR_RGB2BGR)
        
        # 4. Écrire l'image dans le fichier vidéo
        self.video_writer.write(frame_bgr)

    def record_sfx_at_current_frame(self):
        """ Mixe le son de rebond dans la piste audio master à la frame actuelle. """
        
        # 1. Calculer l'échantillon de départ basé sur le temps actuel
        start_sample = int(self.frame_count * (self.sample_rate / FPS))
        
        # 2. Choisir UN son au hasard et obtenir ses données
        sound_data_to_mix = np.array(pygame.mixer.Sound("fx/bounce_1.wav"))[:,0:2] #"fx\bounce_1.wav" #random.choice(self.generated_sound_arrays)
        sound_length = len(sound_data_to_mix)
        
        # 3. Calculer l'échantillon de fin
        end_sample = start_sample + sound_length
        
        # 4. Gérer le cas où le son dépasse la fin de la vidéo
        if end_sample > len(self.master_audio_track):
            # Recalculer la longueur pour qu'elle s'arrête exactement à la fin
            sound_length = len(self.master_audio_track) - start_sample
            
            # Si le son est entièrement en dehors de la piste, ne rien faire
            if sound_length <= 0:
                return
            
            # Tronquer le son pour qu'il corresponde à la nouvelle longueur
            sound_data_to_mix = sound_data_to_mix[:sound_length]
            
            # Mettre à jour la fin pour le mixage
            end_sample = start_sample + sound_length

        # 5. Extraire la région de la piste master où le son sera joué
        # Cette région a maintenant EXACTEMENT la même longueur que sound_data_to_mix
        mix_region = self.master_audio_track[start_sample : end_sample]
        
        # 6. "Mixer" le son (ajouter les valeurs)
        mixed_audio = np.clip(
            mix_region.astype(np.int32) + sound_data_to_mix.astype(np.int32), 
            -32768, 
            32767
        )
        
        # 7. Réinsérer la partie mixée dans la piste master
        self.master_audio_track[start_sample : end_sample] = mixed_audio.astype(np.int16)
 
    def _init_video_writer(self):
        """ Configure et retourne l'objet VideoWriter d'OpenCV. """
        
        self.temp_video_filename = 'temp_video_sans_son.mp4' 
        fourcc = cv2.VideoWriter_fourcc(*'mp4v') # Codec MP4
        
        return cv2.VideoWriter(self.temp_video_filename, fourcc, FPS, (self.largeur_ecran, self.hauteur_ecran))
    
    def cleanup(self):
        """ Termine l'enregistrement, génère l'audio, fusionne, et ferme Pygame. """
        
        print("Finalisation (Étape 1/3 : Écriture de la vidéo)...")
        self.video_writer.release() 

        print("Finalisation (Étape 2/3 : Écriture de l'audio SFX)...")
        self.temp_audio_filename = "temp_sfx_track.wav"
        
        video_clip = None
        audio_clip = None
        
        try:
            # Écrit le tableau NumPy en fichier .wav
            wavfile.write(self.temp_audio_filename, self.sample_rate, self.master_audio_track)

            print("Finalisation (Étape 3/3 : Fusion vidéo et audio)...")
            
            # Charge les fichiers temporaires avec MoviePy
            video_clip = VideoFileClip(self.temp_video_filename)
            audio_clip = AudioFileClip(self.temp_audio_filename)
            
            # Fusionne l'audio sur la vidéo
            final_clip = video_clip.with_audio(audio_clip)
            
            final_video_filename = "simulation_physique_AVEC_SFX.mp4"
            
            # Écrit le fichier final (avec une barre de progression)
            final_clip.write_videofile(
                final_video_filename, 
                codec='libx264',
                audio_codec='aac',
                temp_audiofile='temp-audio.m4a',
                remove_temp=True,
                fps=FPS,
                preset='ultrafast', # Encodage rapide
                threads=4,          # Utilise 4 coeurs CPU
                logger='bar'        # Affiche la barre de progression
            )
            
            print(f"Vidéo finale avec SFX sauvegardée sous : {final_video_filename}")

        except Exception as e:
            # En cas d'erreur (ex: MoviePy non installé), informe l'utilisateur
            print(f"\n--- ERREUR LORS DE LA FUSION AUDIO/VIDÉO ---")
            print(f"Erreur : {e}")
            print("\nVérifiez que 'scipy' et 'moviepy' sont installés.")
            print(f"Le fichier vidéo *sans son* est disponible ici : {self.temp_video_filename}")
            print(f"Le fichier audio *SFX seul* est disponible ici : {self.temp_audio_filename}")
        
        finally:
            # Nettoie les objets MoviePy
            print("Libération des fichiers temporaires...")
            if video_clip:
                video_clip.close()
            if audio_clip:
                audio_clip.close()
            
            # Supprime les fichiers temporaires (sauf si une erreur a eu lieu)
            try:
                if os.path.exists(self.temp_video_filename) and 'e' not in locals():
                    os.remove(self.temp_video_filename)
                if os.path.exists(self.temp_audio_filename) and 'e' not in locals():
                    os.remove(self.temp_audio_filename)
            except PermissionError as pe:
                print(f"ERREUR : Impossible de supprimer les fichiers temporaires. {pe}")

        pygame.quit()
        sys.exit()

# --- Point d'entrée du script ---
if __name__ == "__main__":
    game = Game()
    game.run()