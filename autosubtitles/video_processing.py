import moviepy.editor as mp
from moviepy.video.tools.subtitles import SubtitlesClip
from moviepy.video.compositing.CompositeVideoClip import CompositeVideoClip
from PIL import Image, ImageDraw
import numpy as np

def create_subtitle_clip(txt, video_width, video_height):
    fontsize = 64
    font = 'Manrope-ExtraBold'
    text_color = '#F55E12'
    box_color = '#FFFFFF'
    box_opacity = int(255 * 0.9)  # 90% opacity
    horizontal_padding = 30
    vertical_padding = 20

    # Create text clip
    txt_clip = mp.TextClip(txt, fontsize=fontsize, font=font, color=text_color, method='label', align='center')
    
    # Calculate the size of the background
    txt_width, txt_height = txt_clip.size
    background_width = txt_width + (2 * horizontal_padding)
    background_height = txt_height + (2 * vertical_padding)
    
    # Create a rounded rectangle background using PIL
    background = Image.new('RGBA', (background_width, background_height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(background)
    
    # Convert hex color to RGB and add opacity
    box_color_rgb = tuple(int(box_color[i:i+2], 16) for i in (1, 3, 5))
    box_color_rgba = box_color_rgb + (box_opacity,)
    
    draw.rounded_rectangle([(0, 0), (background_width, background_height)], radius=15, fill=box_color_rgba)
    
    # Convert PIL Image to numpy array
    background_array = np.array(background)
    
    # Create MoviePy clip from the numpy array
    background_clip = mp.ImageClip(background_array).set_duration(txt_clip.duration)

    # Composite text over background
    composite = mp.CompositeVideoClip([background_clip, txt_clip.set_position('center')])
    
    # Set position to center of video
    composite = composite.set_position(('center', 'center'))
    
    return composite

def add_subtitles_to_video(input_video_path: str, output_video_path: str, srt_path: str):
    # Load the video
    video = mp.VideoFileClip(input_video_path)

    # Create a SubtitlesClip with adjusted style
    generator = lambda txt: create_subtitle_clip(txt, video.w, video.h)
    subtitles_clip = SubtitlesClip(srt_path, generator)

    # Overlay subtitles on the video
    final_video = CompositeVideoClip([video, subtitles_clip.set_position(('center', 'center'))])

    # Write the final video
    final_video.write_videofile(output_video_path, codec='libx264', audio_codec='aac')

    print(f"Video processing complete. Output saved as '{output_video_path}'")