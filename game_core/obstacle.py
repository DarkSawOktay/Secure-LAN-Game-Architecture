class Obstacle:
    def __init__(self, x, y, width, height):
        self.x = x
        self.y = y
        self.width = width
        self.height = height

    def get_rect(self):
        return self.x, self.y, self.x + self.width - 1, self.y + self.height - 1

    def collides_with(self, x, y, radius):
        left, top, right, bottom = self.get_rect()
        closest_x = max(left, min(x, right))
        closest_y = max(top, min(y, bottom))
        dx = x - closest_x
        dy = y - closest_y
        return dx * dx + dy * dy < radius * radius
