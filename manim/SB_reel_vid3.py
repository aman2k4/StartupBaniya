from manim import *
import json
import textwrap

class CloudStrike(Scene):
    def construct(self):
        # Set the aspect ratio to 9:16
        self.camera.frame_width = 9
        self.camera.frame_height = 16

        # Set the background image
        background = ImageMobject("../insta1.png").scale_to_fit_height(16)
        self.add(background)

        with open("../news.json", "r") as file:
            news_data = json.load(file)

        y_position = 5  # Adjusted initial y position
        font_size = 36  # Increased font size
        max_width = 7  # Maximum width for text before wrapping

        for news_item in news_data["interesting_points"][:3]:
            # Wrap text if it exceeds max_width
            wrapped_text = textwrap.fill(news_item["point"], width=int(max_width * 5))
            
            text = Text(wrapped_text, font="Arial", font_size=font_size, color=WHITE)
            text.set_width(max_width)
            
            # Ensure text stays within the frame
            if y_position - text.get_height() / 2 < -7:
                y_position = 5  # Reset to top if it goes below frame

            text.move_to([0, y_position, 0])
            
            # Add text to the scene first, then animate
            self.add(text)
            self.play(Write(text), run_time=3)

            y_position -= text.get_height() + 0.5  # Space between text blocks

        # Wait for a moment before ending the scene
        self.wait(2)

# Render the scene
if __name__ == "__main__":
    config.pixel_height = 1920
    config.pixel_width = 1080
    config.frame_rate = 30
    scene = CloudStrike()
    scene.render()