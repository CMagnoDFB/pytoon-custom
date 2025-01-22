# from pytoon.animator import animate
# from moviepy.editor import VideoFileClip

# # Create a PyToon animation without providing a transcript
# animation = animate(
#     audio_file="Barca_audio_trim.mp3"  # Input audio (transcript will be auto-generated)
# )

# # Overlay the animation on top of another video and save as an .mp4 file.
# background_video = VideoFileClip("barca_video_trim.mp4")
# animation.export(path='video_auto_transcript.mp4', 
#                 background=background_video
# )

# #,scale=0.7



from moviepy.editor import VideoFileClip
from pytoon.animator import animate

# # 1) Crie o background
#bg = VideoFileClip("barca_video_trim.mp4")


bg = "still.png"

# 2) Instancie a classe 'animate' e especifique o diretório das bocas
anim = animate(audio_file="Barca_audio_trim.mp3",mouth_set_dir="custom1")

# 3) Exporte:
anim.export(
    path="video_saida.mp4",
    background=bg,
    mouth_x=309,
    mouth_y=197,
    scale_x=0.2,
    scale_y=0.2
)
