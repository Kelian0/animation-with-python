
import numpy as np
import scipy.io.wavfile as wavfile # Utilisé seulement pour le test

class SoundGenerator:
    """
    Une classe pour générer des échantillons audio de différentes formes d'onde.
    
    Initialisée avec des paramètres globaux comme le sample_rate.
    """
    
    def __init__(self, sample_rate=44100, channels=2):
        self.sample_rate = sample_rate
        self.channels = channels
        print(f"SoundGenerator initialisé (Sample Rate: {self.sample_rate} Hz, Canaux: {self.channels})")

    def generate_wave(self, 
                        frequency, 
                        duration_sec, 
                        waveform='sine', 
                        volume=0.8, 
                        use_envelope=True):
        """
        Génère une onde audio avec des paramètres détaillés.

        Args:
            frequency (float): Fréquence du son en Hz (ex: 440.0).
            duration_sec (float): Durée du son en secondes (ex: 0.5).
            waveform (str): 'sine', 'square', ou 'sawtooth'.
            volume (float): Amplitude de 0.0 (silence) à 1.0 (max).
            use_envelope (bool): Si True, applique un fondu (fade-in/out) 
                                 pour éviter les "clics".

        Returns:
            Un tableau NumPy (N, 2) en int16, prêt pour le mixage.
        """
        
        # 1. Calculer le nombre d'échantillons et l'axe de temps
        num_samples = int(duration_sec * self.sample_rate)
        t = np.linspace(0., duration_sec, num_samples, endpoint=False)

        # 2. Générer la forme d'onde de base (valeurs de -1.0 à 1.0)
        if waveform == 'sine':
            # Onde sinusoïdale (son pur)
            wave = np.sin(frequency * t * 2 * np.pi)
        
        elif waveform == 'square':
            # Onde carrée (son "rétro" / 8-bit)
            wave = np.sign(np.sin(frequency * t * 2 * np.pi))
            
        elif waveform == 'sawtooth':
            # Onde en dents de scie (son riche en harmoniques)
            # (t * freq) -> [0, 1, 2, 3...]
            # ... % 1.0 -> [0..1, 0..1, 0..1]
            # * 2 - 1   -> [-1..1, -1..1]
            wave = ((t * frequency) % 1.0) * 2.0 - 1.0
            
        else:
            raise ValueError(f"Forme d'onde '{waveform}' non supportée.")

        # 3. Appliquer l'enveloppe (pour éviter les "clics")
        if use_envelope:
            # Une fenêtre de Hanning est un fondu simple et efficace
            envelope = np.hanning(num_samples)
            wave = wave * envelope

        # 4. Appliquer le volume et convertir en int16
        amplitude = 32767 * volume
        wave_int16 = (wave * amplitude).astype(np.int16)

        # 5. Gérer les canaux (stéréo ou mono)
        if self.channels == 2:
            # Dupliquer le son sur les deux canaux
            stereo_wave = np.column_stack([wave_int16, wave_int16])
            return stereo_wave
        else:
            # Retourner en mono
            return wave_int16


# --- Bloc de Test ---
# Si vous exécutez ce fichier (sound_tools.py) directement,
# cela générera un fichier "test_audio.wav" pour que vous puissiez l'écouter.
if __name__ == "__main__":
    
    print("Test du SoundGenerator...")
    
    # Initialise le générateur
    generator = SoundGenerator(sample_rate=44100, channels=2)
    
    # Crée trois sons différents
    note_do = generator.generate_wave(261.63, 0.5, 'sine')
    note_mi = generator.generate_wave(329.63, 0.5, 'square', volume=0.5)
    note_sol = generator.generate_wave(392.00, 0.5, 'sawtooth', volume=0.7)
    silence = np.zeros((int(0.1 * 44100), 2), dtype=np.int16) # 0.1s de silence
    
    # Concatène les sons
    final_audio = np.concatenate([
        note_do, silence,
        note_mi, silence,
        note_sol
    ])
    
    # Sauvegarde le fichier .wav
    try:
        wavfile.write("test_audio.wav", 44100, final_audio)
        print("\nSUCCÈS !")
        print("Fichier 'test_audio.wav' généré avec trois sons différents.")
        print("Écoutez-le pour vérifier !")
    except Exception as e:
        print(f"\nERREUR lors de la sauvegarde du fichier : {e}")
        print("Assurez-vous que 'scipy' est installé (`pip install scipy`)")