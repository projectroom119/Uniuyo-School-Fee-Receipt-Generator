    def draw_top_right_block(self, qr_path, passport_path, data):
        self.image(qr_path, x=160, y=7, w=30)
        self.image(passport_path, x=160, y=40, w=30, h=25)

        self.set_xy(170, 70)
        self.set_font("Arial", "B", 9)
        block = [
    ("Gender:", data["gender"]),
    ("Session:", data["session"]),
    ("Level:", data["level"]),
    ("Date:", data["date"])
]

        for label, val in block:
         self.set_xy(160, self.get_y() + 0)
         self.cell(25, 6, label, 0)
         self.cell(80, 6, val, ln=True)
