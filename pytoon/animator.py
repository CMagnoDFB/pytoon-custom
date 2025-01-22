import os
import json
import random

from PIL import Image
from datetime import datetime
import numpy as np
import cv2
import copy
from moviepy.editor import (
    ImageSequenceClip,
    CompositeVideoClip,
    CompositeAudioClip,
    AudioFileClip,
    VideoClip,
    ImageClip
)

from .util import read_json
from .dataloader import get_assets
from .lipsync import viseme_sequencer

class FrameSequence:
    """
    Armazena a sequência de quadros que compõem a animação da boca,
    sem mais referências às poses (boneco).
    """
    def __init__(self):
        self.mouth_files = []   # Caminhos (strings) dos arquivos de boca para cada quadro
        self.final_frames = []  # Imagens finais (np.array RGBA) para cada quadro


class animate:
    """
    Classe principal para gerar animação de bocas (visemes) sincronizadas com o áudio,
    sem envolver a pose do personagem.
    """

    def __init__(self, audio_file: str, transcript: str = None, fps: int = 48, mouth_set_dir="positive"):
        """
        - audio_file: caminho para o arquivo de áudio (ex: .wav ou .mp3)
        - transcript: texto ou caminho de transcrição (opcional, depende de como o lipsync foi implementado)
        - fps: frames por segundo do vídeo resultante
        """
        self.mouth_set_dir = mouth_set_dir  # Diretório de visemes (bocas) a ser utilizado
        self.audio_file = audio_file
        self.fps = fps
        
        # Cria um objeto para armazenar a sequência de frames da boca
        self.sequence = FrameSequence()

        # (Se ainda precisar de assets por algum motivo, você pode manter.)
        self.assets = get_assets()  

        # Gera a sequência de visemas (formas da boca) sincronizadas com o áudio
        self.viseme_sequence = viseme_sequencer(audio_file, transcript, fps=self.fps)

        # Monta a lista final de arquivos de boca (self.sequence.mouth_files)
        self.build_mouth_sequence()

        # Gera cada frame final (apenas a boca em RGBA)
        self.compile_frames()

        # Calcula duração total
        self.duration = len(self.sequence.mouth_files) / self.fps if self.fps > 0 else 0

        
        print(f"[INFO] Total de frames de boca: {len(self.sequence.mouth_files)}")
        print(f"[INFO] Duração estimada (s): {self.duration:.2f}")

    def build_mouth_sequence(self):
        """
        Processa a saída do lipsync e monta uma lista de arquivos de boca (visemes)
        para cada quadro.
        """
        for segment in self.viseme_sequence:
            # Cada 'segment' deve conter .visemes = lista de nomes de arquivo
            if segment.visemes:
                # Adiciona todos os nomes de arquivo de boca na sequência
                self.sequence.mouth_files.extend(segment.visemes)
        
        # Prepara o caminho absoluto para cada arquivo de boca
        # Ex.: /caminho/até/este_arquivo/ + assets/visemes/negative/ + nome_do_arquivo.png
        base_dir = os.path.dirname(__file__)
        for i, file_name in enumerate(self.sequence.mouth_files):
            full_path = os.path.join(base_dir, "assets", "visemes", self.mouth_set_dir, file_name)
            self.sequence.mouth_files[i] = full_path

    def compile_frames(self):
        """
        Carrega cada arquivo de boca e converte em RGBA (np.array).
        Aqui você pode aplicar transformações *padrão* (flip, rotate) se quiser,
        mas, por enquanto, vamos manter o tamanho original.
        """
        for mouth_file in self.sequence.mouth_files:
            # Abre a imagem da boca em RGBA
            pil_mouth = Image.open(mouth_file).convert("RGBA")
            
            # Converte para np.array RGBA
            mouth_np = np.array(pil_mouth, dtype=np.uint8)
            
            # Salva no final_frames (aqui o "frame" é só a boca)
            self.sequence.final_frames.append(mouth_np)

    def export(
        self,
        path: str,
        background,
        mouth_x: int = 0,
        mouth_y: int = 0,
        scale_x: float = 1.0,
        scale_y: float = 1.0
    ):
        """
        Exporta o vídeo final, colando a boca no background, que pode ser:
          - um objeto VideoClip (video)
          - ou um caminho para arquivo de imagem (still image).

        :param path: caminho de saída, ex. "output.mp4"
        :param background: 
            - se for um VideoClip, usamos diretamente
            - se for uma string terminando em .png / .jpg, interpretamos como imagem
        :param mouth_x, mouth_y: coordenadas onde a boca será colada (centro da boca)
        :param scale_x, scale_y: fatores de escala (1.0 mantém o tamanho original)
        """

        # 1) Verifica se background é um "VideoClip" ou uma string (caminho da imagem)
        if isinstance(background, VideoClip):
            bg_clip = background
            bg_duration = bg_clip.duration
        else:
            # Supondo que seja string de uma imagem
            if not os.path.isfile(background):
                raise FileNotFoundError(f"Background image not found: {background}")
            # Cria um ImageClip com a MESMA duração da animação
            bg_clip = ImageClip(background).set_duration(self.duration)
            bg_duration = self.duration

        # 2) Ajusta a escala da boca em cada frame
        scaled_frames = []
        for frame in self.sequence.final_frames:
            h, w = frame.shape[:2]
            new_w = int(w * scale_x)
            new_h = int(h * scale_y)
            # Evitar dimensões zero ou negativas
            if new_w < 1: new_w = 1
            if new_h < 1: new_h = 1

            scaled = cv2.resize(frame, (new_w, new_h), interpolation=cv2.INTER_AREA)
            scaled_frames.append(scaled)

        # 3) Cria o clip de animação (boca) a partir dos frames RGBA
        mouth_clip = ImageSequenceClip(scaled_frames, fps=self.fps, with_mask=True)

        # Descobre tamanho do 1o frame da boca (depois de escala), para posicionar o centro
        if scaled_frames:
            final_h, final_w = scaled_frames[0].shape[:2]
        else:
            final_h, final_w = 0, 0

        # Ajuste de posição => (mouth_x, mouth_y) como centro
        pos_x = mouth_x - (final_w // 2)
        pos_y = mouth_y - (final_h // 2)
        mouth_clip = mouth_clip.set_position((pos_x, pos_y))

        # 4) Composição final no MoviePy
        final_clip = CompositeVideoClip([bg_clip, mouth_clip], use_bgclip=True)
        final_clip = final_clip.set_duration(min(bg_duration, self.duration))

        # 5) Define o áudio (voz) no final_clip (se você quiser atrasar, use set_start())
        audio_clip = AudioFileClip(self.audio_file)
        final_audio = CompositeAudioClip([audio_clip])
        final_clip = final_clip.set_audio(final_audio)

        # 6) Exporta o resultado
        final_clip.write_videofile(
            path,
            codec="libx264",
            audio_codec="aac",
            preset="ultrafast",
            threads=4,
            fps=self.fps
        )
