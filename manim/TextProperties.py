from manim import *
import manimpango


class Linebreak(Scene):
    def construct(self):
        before = Text("Example Text")
        after = Text("Example\\nText", line_spacing=2)
        self.add(after)
        self.wait()

class FontSize(Scene):
    def construct(self):
        before = Text("Example Text")
        after = Text("Example Text", font_size=96)
        self.add(after)
        self.wait()

class FontType(Scene):
    def construct(self):
        before = Text("Example Text")
        after = Text("Example Text", font="Manrope")
        self.add(after)
        self.wait()

class Slant(Scene):
    def construct(self):
        before = Text("Example Text")
        after = Text("Example Text", slant=ITALIC)
        option = Text("Example Text", slant=OBLIQUE)
        self.add(after)
        self.wait()

class Weight(Scene):
    def construct(self):
        before = Text("Example Text")
        after = Text("Example Text", weight=THIN)
        option = Text("Example Text", weight=BOLD)
        self.add(after)
        self.wait()

class PossibleWeightsList(Scene):
    def construct(self):
        import manimpango

        g = VGroup()
        weight_list = dict(sorted({weight: manimpango.Weight(weight).value for weight in manimpango.Weight}.items(), key=lambda x: x[1]))
        for weight in weight_list:
            g += Text(weight.name, weight=weight.name, font="Manrope")
        self.add(g.arrange(DOWN).scale(0.5))
        self.wait()

if __name__ == "__main__":
    scene = PossibleWeightsList()
    scene.render()

