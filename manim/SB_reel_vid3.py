from manim import *
import json
import textwrap

class CloudStrike(Scene):
    def construct(self):
        # Set the aspect ratio to 9:16
        self.camera.frame_width = 9
        self.camera.frame_height = 16

        # Array of background images
        image_files = ["insta1.png", "insta2.png", "insta3.png", "insta4.png"]
        backgrounds = [ImageMobject(f"../{img}").scale_to_fit_height(16) for img in image_files]

        with open("../news.json", "r") as file:
            news_data = json.load(file)

        y_position = 5  # Adjusted initial y position
        font_size = 60  # Increased font size
        max_width = 7  # Maximum width for text before wrapping

        current_bg = backgrounds[0]
        self.add(current_bg)

        for i, news_item in enumerate(news_data["interesting_points"]):
            # Wrap text if it exceeds max_width
            wrapped_text = textwrap.fill(news_item["point"], width=int(max_width * 5))
            text = Text(wrapped_text, font="Arial", font_size=font_size, color=WHITE, weight=BOLD)
            text.set_width(max_width)

            # Ensure text stays within the frame
            if y_position - text.get_height() / 2 < -7:
                y_position = 5  # Reset to top if it goes below frame

            text.move_to([0, y_position, 0])

            # Animate text appearance letter by letter
            self.play(AddTextLetterByLetter(text, run_time=2))

            # Wait for a moment
            self.wait(2)

            # Fade out the text
            self.play(FadeOut(text), run_time=1)

            # Change background with fade effect
            next_bg = backgrounds[(i + 1) % len(backgrounds)]
            self.play(
                FadeTransform(current_bg, next_bg),
                run_time=1
            )
            current_bg = next_bg

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