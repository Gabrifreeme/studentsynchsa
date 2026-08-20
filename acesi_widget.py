import tkinter as tk
import math
import time
import threading


class ACEsiWidget:
    def __init__(self, root):
        self.root = root
        self.root.title("ACEsi Core")
        self.root.geometry("200x200")
        self.root.configure(bg='black')
        self.root.attributes("-topmost", True)
        self.root.attributes("-alpha", 0.85)
        self.root.bind("<Escape>", lambda e: self.root.destroy())

        self.canvas = tk.Canvas(root, width=200, height=200, bg='black', highlightthickness=0)
        self.canvas.pack()

        self.base_radius = 50
        self.current_radius = 50
        self.pulse_speed = 0.05
        self.angle = 0

        self.audio_state = 'idle'

        self.update_pulse()

    def draw_core(self, radius):
        self.canvas.delete("all")
        cx, cy = 100, 100

        if self.audio_state == 'speaking':
            color = "#00ffcc"
            outline_color = "#ffffff"
        elif self.audio_state == 'user_speaking':
            color = "#39ff14"
            outline_color = "#ffffff"
        else:
            color = "#cc5500"
            outline_color = "#ffaa33"

        self.canvas.create_oval(cx - radius - 10, cy - radius - 10,
                                cx + radius + 10, cy + radius + 10,
                                outline=color, width=1)
        self.canvas.create_oval(cx - radius, cy - radius,
                                cx + radius, cy + radius,
                                fill=color, outline=outline_color, width=2)

    def update_pulse(self):
        if self.audio_state == 'idle':
            self.pulse_speed = 0.05
            amplitude = 8
            self.angle += self.pulse_speed
            self.current_radius = self.base_radius + (math.sin(self.angle) * amplitude)
        elif self.audio_state in ['speaking', 'user_speaking']:
            self.pulse_speed = 0.25
            amplitude = 25
            self.angle += self.pulse_speed
            self.current_radius = self.base_radius + 15 + (math.sin(self.angle) * amplitude)

        self.draw_core(self.current_radius)
        self.root.after(20, self.update_pulse)


if __name__ == "__main__":
    root = tk.Tk()
    app = ACEsiWidget(root)

    def simulate_speech():
        time.sleep(3)
        print("ACEsi text printed: 'Live and active. What do you need?'")
        app.audio_state = 'speaking'
        time.sleep(4)
        app.audio_state = 'idle'

    threading.Thread(target=simulate_speech, daemon=True).start()
    root.mainloop()
