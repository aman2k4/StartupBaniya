from manim import *

class DoMyJob(Scene):
    def construct(self):
        text=Text("This automation will make me a millionaire")
        self.play(Write(text))
        self.play(FadeOut(text))
        self.wait()



scene=DoMyJob()
scene.render()