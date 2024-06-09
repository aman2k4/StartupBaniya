from manim import *

text = "I will tell you what our goal is. Our goal is to make the best personal computer that we are proud to sell our family and friends."


class AddText(Scene):
    def construct(self):
        text = Text(text)
        self.add(text)
        self.wait()
        self.remove(text)
        self.wait()


class WriteText(Scene):
    def construct(self):
        text = Text(text)
        self.play(Write(text), run_time=4)
        self.wait()


class AddLetterByLetter(Scene):
    def construct(self):
        text = Text(text)
        self.play(AddTextLetterByLetter(text))
        self.wait()

# Grouping the text by number of words
class GroupTextByWords(Scene):
    def construct(self):
        words = text.split()
        for i in range(0, len(words), 3):
            grouped_text = " ".join(words[i:i+3])
            text_group = Text(grouped_text)
            self.play(Write(text_group))
            self.wait()

scene = GroupTextByWords()
scene.render()
