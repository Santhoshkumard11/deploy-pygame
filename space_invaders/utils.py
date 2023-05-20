from pygame import sprite, transform, mixer, time, Surface, font, K_RIGHT, K_LEFT
from constants import IMAGES, ENEMY_MOVE_DOWN, SOUND_PATH, FONT, WHITE
from random import choice


class Ship(sprite.Sprite):
    def __init__(self, game):
        sprite.Sprite.__init__(self)
        self.image = IMAGES["ship"]
        self.rect = self.image.get_rect(topleft=(375, 540))
        self.speed = 5
        self.game = game

    def update(self, keys, *args):
        if keys[K_LEFT] and self.rect.x > 10:
            self.rect.x -= self.speed
        if keys[K_RIGHT] and self.rect.x < 740:
            self.rect.x += self.speed
        self.game.blit(self.image, self.rect)


class Bullet(sprite.Sprite):
    def __init__(self, game, xpos, ypos, direction, speed, filename, side):
        sprite.Sprite.__init__(self)
        self.game = game
        self.image = IMAGES[filename]
        self.rect = self.image.get_rect(topleft=(xpos, ypos))
        self.speed = speed
        self.direction = direction
        self.side = side
        self.filename = filename

    def update(self, keys, *args):
        self.game.blit(self.image, self.rect)
        self.rect.y += self.speed * self.direction
        if self.rect.y < 15 or self.rect.y > 600:
            self.kill()


class Enemy(sprite.Sprite):
    def __init__(self, game, row, column):
        sprite.Sprite.__init__(self)
        self.game = game
        self.row = row
        self.column = column
        self.images = []
        self.load_images()
        self.index = 0
        self.image = self.images[self.index]
        self.rect = self.image.get_rect()

    def toggle_image(self):
        self.index += 1
        if self.index >= len(self.images):
            self.index = 0
        self.image = self.images[self.index]

    def update(self, *args):
        self.game.blit(self.image, self.rect)

    def load_images(self):
        images = {
            0: ["1_2", "1_1"],
            1: ["2_2", "2_1"],
            2: ["2_2", "2_1"],
            3: ["3_1", "3_2"],
            4: ["3_1", "3_2"],
        }
        img1, img2 = (IMAGES["enemy{}".format(img_num)] for img_num in images[self.row])
        self.images.append(transform.scale(img1, (40, 35)))
        self.images.append(transform.scale(img2, (40, 35)))


class EnemiesGroup(sprite.Group):
    def __init__(self, game, columns, rows):
        sprite.Group.__init__(self)
        self.game = game
        self.enemies = [[None] * columns for _ in range(rows)]
        self.columns = columns
        self.rows = rows
        self.leftAddMove = 0
        self.rightAddMove = 0
        self.moveTime = 600
        self.direction = 1
        self.rightMoves = 30
        self.leftMoves = 30
        self.moveNumber = 15
        self.timer = time.get_ticks()
        self.bottom = self.game.enemyPosition + ((rows - 1) * 45) + 35
        self._aliveColumns = list(range(columns))
        self._leftAliveColumn = 0
        self._rightAliveColumn = columns - 1

    def update(self, current_time):
        if current_time - self.timer > self.moveTime:
            if self.direction == 1:
                max_move = self.rightMoves + self.rightAddMove
            else:
                max_move = self.leftMoves + self.leftAddMove

            if self.moveNumber >= max_move:
                self.leftMoves = 30 + self.rightAddMove
                self.rightMoves = 30 + self.leftAddMove
                self.direction *= -1
                self.moveNumber = 0
                self.bottom = 0
                for enemy in self:
                    enemy.rect.y += ENEMY_MOVE_DOWN
                    enemy.toggle_image()
                    if self.bottom < enemy.rect.y + 35:
                        self.bottom = enemy.rect.y + 35
            else:
                velocity = 10 if self.direction == 1 else -10
                for enemy in self:
                    enemy.rect.x += velocity
                    enemy.toggle_image()
                self.moveNumber += 1

            self.timer += self.moveTime

    def add_internal(self, *sprites):
        super(EnemiesGroup, self).add_internal(*sprites)
        for s in sprites:
            self.enemies[s.row][s.column] = s

    def remove_internal(self, *sprites):
        super(EnemiesGroup, self).remove_internal(*sprites)
        for s in sprites:
            self.kill(s)
        self.update_speed()

    def is_column_dead(self, column):
        return not any(self.enemies[row][column] for row in range(self.rows))

    def random_bottom(self):
        col = choice(self._aliveColumns)
        col_enemies = (self.enemies[row - 1][col] for row in range(self.rows, 0, -1))
        return next((en for en in col_enemies if en is not None), None)

    def update_speed(self):
        if len(self) == 1:
            self.moveTime = 200
        elif len(self) <= 10:
            self.moveTime = 400

    def kill(self, enemy):
        self.enemies[enemy.row][enemy.column] = None
        is_column_dead = self.is_column_dead(enemy.column)
        if is_column_dead:
            self._aliveColumns.remove(enemy.column)

        if enemy.column == self._rightAliveColumn:
            while self._rightAliveColumn > 0 and is_column_dead:
                self._rightAliveColumn -= 1
                self.rightAddMove += 5
                is_column_dead = self.is_column_dead(self._rightAliveColumn)

        elif enemy.column == self._leftAliveColumn:
            while self._leftAliveColumn < self.columns and is_column_dead:
                self._leftAliveColumn += 1
                self.leftAddMove += 5
                is_column_dead = self.is_column_dead(self._leftAliveColumn)


class Blocker(sprite.Sprite):
    def __init__(self, game, size, color, row, column):
        sprite.Sprite.__init__(self)
        self.game = game
        self.height = size
        self.width = size
        self.color = color
        self.image = Surface((self.width, self.height))
        self.image.fill(self.color)
        self.rect = self.image.get_rect()
        self.row = row
        self.column = column

    def update(self, keys, *args):
        self.game.blit(self.image, self.rect)


class Mystery(sprite.Sprite):
    def __init__(self, game):
        sprite.Sprite.__init__(self)
        self.game = game
        self.image = IMAGES["mystery"]
        self.image = transform.scale(self.image, (75, 35))
        self.rect = self.image.get_rect(topleft=(-80, 45))
        self.row = 5
        self.moveTime = 25000
        self.direction = 1
        self.timer = time.get_ticks()
        self.mysteryEntered = mixer.Sound(SOUND_PATH + "mysteryentered.wav")
        self.mysteryEntered.set_volume(0.3)
        self.playSound = True

    def update(self, keys, currentTime, *args):
        resetTimer = False
        passed = currentTime - self.timer
        if passed > self.moveTime:
            if (self.rect.x < 0 or self.rect.x > 800) and self.playSound:
                self.mysteryEntered.play()
                self.playSound = False
            if self.rect.x < 840 and self.direction == 1:
                self.mysteryEntered.fadeout(4000)
                self.rect.x += 2
                self.game.screen.blit(self.image, self.rect)
            if self.rect.x > -100 and self.direction == -1:
                self.mysteryEntered.fadeout(4000)
                self.rect.x -= 2
                self.game.screen.blit(self.image, self.rect)

        if self.rect.x > 830:
            self.playSound = True
            self.direction = -1
            resetTimer = True
        if self.rect.x < -90:
            self.playSound = True
            self.direction = 1
            resetTimer = True
        if passed > self.moveTime and resetTimer:
            self.timer = currentTime


class EnemyExplosion(sprite.Sprite):
    def __init__(self, game, enemy, *groups):
        super(EnemyExplosion, self).__init__(*groups)
        self.game = game
        self.image = transform.scale(self.get_image(enemy.row), (40, 35))
        self.image2 = transform.scale(self.get_image(enemy.row), (50, 45))
        self.rect = self.image.get_rect(topleft=(enemy.rect.x, enemy.rect.y))
        self.timer = time.get_ticks()

    @staticmethod
    def get_image(row):
        img_colors = ["purple", "blue", "blue", "green", "green"]
        return IMAGES["explosion{}".format(img_colors[row])]

    def update(self, current_time, *args):
        passed = current_time - self.timer
        if passed <= 100:
            self.game.screen.blit(self.image, self.rect)
        elif passed <= 200:
            self.game.screen.blit(self.image2, (self.rect.x - 6, self.rect.y - 6))
        elif 400 < passed:
            self.kill()


class MysteryExplosion(sprite.Sprite):
    def __init__(self, mystery, score, *groups):
        super(MysteryExplosion, self).__init__(*groups)
        self.text = Text(
            FONT, 20, str(score), WHITE, mystery.rect.x + 20, mystery.rect.y + 6
        )
        self.timer = time.get_ticks()

    def update(self, current_time, *args):
        passed = current_time - self.timer
        if passed <= 200 or 400 < passed <= 600:
            self.text.draw(self.game.screen)
        elif 600 < passed:
            self.kill()


class ShipExplosion(sprite.Sprite):
    def __init__(self, game, ship, *groups):
        super(ShipExplosion, self).__init__(*groups)
        self.game = game
        self.image = IMAGES["ship"]
        self.rect = self.image.get_rect(topleft=(ship.rect.x, ship.rect.y))
        self.timer = time.get_ticks()

    def update(self, current_time, *args):
        passed = current_time - self.timer
        if 300 < passed <= 600:
            self.game.screen.blit(self.image, self.rect)
        elif 900 < passed:
            self.kill()


class Life(sprite.Sprite):
    def __init__(self, game, xpos, ypos):
        sprite.Sprite.__init__(self)
        self.game = game
        self.image = IMAGES["ship"]
        self.image = transform.scale(self.image, (23, 23))
        self.rect = self.image.get_rect(topleft=(xpos, ypos))

    def update(self, *args):
        self.game.screen.blit(self.image, self.rect)


class Text(object):
    def __init__(self, textFont, size, message, color, xpos, ypos):
        self.font = font.Font(textFont, size)
        self.surface = self.font.render(message, True, color)
        self.rect = self.surface.get_rect(topleft=(xpos, ypos))

    def draw(self, surface):
        surface.blit(self.surface, self.rect)
