from manim import *

class AIBox(Scene):
    def construct(self):
        # Set the aspect ratio to 9:16 (1080x1920)
        self.camera.frame_width = 9
        self.camera.frame_height = 16

        # Create the box
        box = Rectangle(width=9, height=16, color=WHITE)

        # Create the text
        text = Text("artificial intelligence", font_size=36)

        # Create four copies of the text for each side
        top_text = text.copy()
        bottom_text = text.copy()
        left_text = text.copy().rotate(90 * DEGREES)
        right_text = text.copy().rotate(-90 * DEGREES)

        # Position the texts
        top_text.next_to(box.get_top(), DOWN, buff=0.2)
        bottom_text.next_to(box.get_bottom(), UP, buff=0.2)
        left_text.next_to(box.get_left(), RIGHT, buff=0.2)
        right_text.next_to(box.get_right(), LEFT, buff=0.2)

        # Create a group with all elements
        full_box = VGroup(box, top_text, bottom_text, left_text, right_text)

        # Animate the creation of the box and texts
        self.play(Create(box))
        self.play(Write(top_text), Write(bottom_text), Write(left_text), Write(right_text))

        # Wait for a moment before ending the scene
        self.wait(2)

# Render the scene
if __name__ == "__main__":
    config.pixel_height = 1920
    config.pixel_width = 1080
    config.frame_rate = 30
    scene = AIBox()
    scene.render()