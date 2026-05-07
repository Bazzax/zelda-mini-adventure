#!/usr/bin/env python3
"""
Zelda-Style Top-Down Adventure (Pygame)
A complete mini Zelda-like game: move, attack with sword, defeat slimes, collect rupees.
"""

import pygame
import sys
import random
import math

# === CONFIG ===
WIDTH, HEIGHT = 768, 576          # 16x12 tiles at 48px
TILE_SIZE = 48
FPS = 60
TITLE = "Zelda Mini Adventure"

# Colors
GRASS = (76, 153, 76)
DARK_GRASS = (34, 102, 34)
PATH = (210, 180, 140)
WALL = (105, 105, 105)
WATER = (30, 120, 180)
PLAYER_GREEN = (34, 139, 34)
PLAYER_TUNIC = (0, 100, 0)
SWORD = (200, 200, 220)
SLIME = (180, 50, 200)
RUPEE = (0, 220, 80)
HEART = (220, 30, 30)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
YELLOW = (255, 215, 0)

class Player:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.size = 28
        self.speed = 3.5
        self.health = 6          # 3 hearts
        self.max_health = 6
        self.direction = "down"
        self.attacking = False
        self.attack_timer = 0
        self.attack_cooldown = 18
        self.rupees = 0
        self.invincible = 0
        self.knockback_x = 0
        self.knockback_y = 0

    def move(self, dx, dy, walls):
        if self.invincible > 0:
            self.invincible -= 1

        # Apply knockback
        if abs(self.knockback_x) > 0.1 or abs(self.knockback_y) > 0.1:
            self.x += self.knockback_x
            self.y += self.knockback_y
            self.knockback_x *= 0.7
            self.knockback_y *= 0.7

        new_x = self.x + dx * self.speed
        new_y = self.y + dy * self.speed

        # Keep inside room (with wall padding)
        margin = 30
        new_x = max(margin, min(WIDTH - margin, new_x))
        new_y = max(margin, min(HEIGHT - margin, new_y))

        # Wall collision (simple rects)
        player_rect = pygame.Rect(new_x - self.size//2, new_y - self.size//2, self.size, self.size)
        for wall in walls:
            if player_rect.colliderect(wall):
                # Push out
                if dx > 0: new_x = wall.left - self.size//2 - 1
                if dx < 0: new_x = wall.right + self.size//2 + 1
                if dy > 0: new_y = wall.top - self.size//2 - 1
                if dy < 0: new_y = wall.bottom + self.size//2 + 1
                break

        self.x = new_x
        self.y = new_y

    def attack(self, enemies):
        if self.attacking or self.attack_timer > 0:
            return
        self.attacking = True
        self.attack_timer = self.attack_cooldown

        attack_range = 55
        attack_angle = {"up": -90, "down": 90, "left": 180, "right": 0}[self.direction]

        for enemy in enemies[:]:
            dx = enemy.x - self.x
            dy = enemy.y - self.y
            dist = math.hypot(dx, dy)
            if 5 < dist < attack_range:
                angle = math.degrees(math.atan2(dy, dx))
                diff = abs((angle - attack_angle + 180) % 360 - 180)
                if diff < 55:  # ~110 degree attack arc
                    enemy.health -= 1
                    # Knockback enemy
                    enemy.knockback_x = math.cos(math.radians(attack_angle)) * 8
                    enemy.knockback_y = math.sin(math.radians(attack_angle)) * 8
                    if enemy.health <= 0:
                        enemies.remove(enemy)
                        self.rupees += random.randint(1, 3)

    def update(self):
        if self.attack_timer > 0:
            self.attack_timer -= 1
        if self.attack_timer == 0:
            self.attacking = False

    def take_damage(self, amount=1):
        if self.invincible <= 0:
            self.health -= amount
            self.invincible = 45  # ~0.75 seconds
            # Small knockback from enemy direction (handled in enemy collision)
            return True
        return False

    def draw(self, screen):
        # Shadow
        pygame.draw.ellipse(screen, (0, 0, 0, 80), (self.x - 12, self.y + 10, 24, 10))

        # Body (tunic)
        color = PLAYER_TUNIC if self.invincible % 6 < 3 else PLAYER_GREEN
        pygame.draw.rect(screen, color, (self.x - 12, self.y - 10, 24, 22), border_radius=4)

        # Head
        pygame.draw.circle(screen, (255, 220, 185), (self.x, self.y - 14), 9)

        # Hat
        pygame.draw.rect(screen, DARK_GRASS, (self.x - 11, self.y - 23, 22, 10), border_radius=2)

        # Eyes
        eye_offset = 3 if self.direction == "left" else -3 if self.direction == "right" else 0
        pygame.draw.circle(screen, BLACK, (self.x - 4 + eye_offset, self.y - 15), 2)
        pygame.draw.circle(screen, BLACK, (self.x + 4 + eye_offset, self.y - 15), 2)

        # Sword (when attacking)
        if self.attacking:
            sword_len = 38
            angle = {"up": -90, "down": 90, "left": 180, "right": 0}[self.direction]
            rad = math.radians(angle)
            end_x = self.x + math.cos(rad) * sword_len
            end_y = self.y + math.sin(rad) * sword_len - 8

            # Sword blade
            pygame.draw.line(screen, SWORD, (self.x, self.y - 8), (end_x, end_y), 4)
            # Sword handle
            pygame.draw.line(screen, (139, 69, 19), (self.x, self.y - 8), 
                           (self.x + math.cos(rad) * 8, self.y - 8 + math.sin(rad) * 8), 5)

        # Direction indicator (small)
        if not self.attacking:
            dx = {"left": -1, "right": 1, "up": 0, "down": 0}[self.direction]
            dy = {"up": -1, "down": 1, "left": 0, "right": 0}[self.direction]
            pygame.draw.circle(screen, YELLOW, (self.x + dx*14, self.y + dy*14 - 4), 3)


class Enemy:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.size = 22
        self.speed = 1.8
        self.health = 2
        self.knockback_x = 0
        self.knockback_y = 0
        self.hit_timer = 0

    def update(self, player, walls):
        # Knockback
        if abs(self.knockback_x) > 0.1 or abs(self.knockback_y) > 0.1:
            self.x += self.knockback_x
            self.y += self.knockback_y
            self.knockback_x *= 0.65
            self.knockback_y *= 0.65

        # Chase player
        dx = player.x - self.x
        dy = player.y - self.y
        dist = math.hypot(dx, dy)
        if dist > 5:
            self.x += (dx / dist) * self.speed
            self.y += (dy / dist) * self.speed

        # Wall collision
        margin = 25
        self.x = max(margin, min(WIDTH - margin, self.x))
        self.y = max(margin, min(HEIGHT - margin, self.y))

        if self.hit_timer > 0:
            self.hit_timer -= 1

    def draw(self, screen):
        # Shadow
        pygame.draw.ellipse(screen, (0, 0, 0, 60), (self.x - 10, self.y + 8, 20, 8))
        # Body
        color = (220, 80, 220) if self.hit_timer > 0 else SLIME
        pygame.draw.circle(screen, color, (self.x, self.y), self.size)
        # Eyes
        pygame.draw.circle(screen, WHITE, (self.x - 6, self.y - 4), 5)
        pygame.draw.circle(screen, WHITE, (self.x + 6, self.y - 4), 5)
        pygame.draw.circle(screen, BLACK, (self.x - 6, self.y - 4), 2)
        pygame.draw.circle(screen, BLACK, (self.x + 6, self.y - 4), 2)
        # Mouth
        pygame.draw.arc(screen, BLACK, (self.x - 6, self.y + 2, 12, 8), 0, math.pi, 2)


class Rupee:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.size = 12
        self.bob = 0

    def update(self):
        self.bob = (self.bob + 0.15) % (2 * math.pi)

    def draw(self, screen):
        y = self.y + math.sin(self.bob) * 3
        # Diamond shape
        points = [
            (self.x, y - self.size),
            (self.x + self.size//2, y),
            (self.x, y + self.size),
            (self.x - self.size//2, y)
        ]
        pygame.draw.polygon(screen, RUPEE, points)
        pygame.draw.polygon(screen, (0, 180, 60), points, 2)


def create_walls():
    """Create the room walls (border + some pillars)"""
    walls = []
    # Outer walls
    walls.append(pygame.Rect(0, 0, WIDTH, 25))                    # top
    walls.append(pygame.Rect(0, HEIGHT-25, WIDTH, 25))            # bottom
    walls.append(pygame.Rect(0, 0, 25, HEIGHT))                   # left
    walls.append(pygame.Rect(WIDTH-25, 0, 25, HEIGHT))            # right

    # Inner pillars / obstacles
    walls.append(pygame.Rect(180, 160, 48, 48))
    walls.append(pygame.Rect(540, 160, 48, 48))
    walls.append(pygame.Rect(180, 380, 48, 48))
    walls.append(pygame.Rect(540, 380, 48, 48))
    walls.append(pygame.Rect(360, 280, 48, 48))  # center
    return walls


def draw_background(screen):
    """Draw grass, path and water tiles"""
    # Base grass
    screen.fill(GRASS)
    for x in range(0, WIDTH, TILE_SIZE):
        for y in range(0, HEIGHT, TILE_SIZE):
            if (x + y) % (TILE_SIZE * 2) == 0:
                pygame.draw.rect(screen, DARK_GRASS, (x, y, TILE_SIZE, TILE_SIZE))

    # Central path
    pygame.draw.rect(screen, PATH, (120, 200, 528, 176))
    # Small water patches
    pygame.draw.ellipse(screen, WATER, (80, 80, 90, 60))
    pygame.draw.ellipse(screen, (20, 90, 150), (600, 420, 110, 70))


def draw_ui(screen, player, enemies):
    # Top bar
    pygame.draw.rect(screen, (20, 20, 30), (0, 0, WIDTH, 38))
    
    # Hearts
    for i in range(player.max_health // 2):
        x = 20 + i * 32
        filled = player.health > i * 2
        color = HEART if filled else (80, 80, 80)
        # Heart shape
        pygame.draw.circle(screen, color, (x + 6, 19), 7)
        pygame.draw.circle(screen, color, (x + 14, 19), 7)
        pygame.draw.polygon(screen, color, [(x + 1, 22), (x + 10, 32), (x + 19, 22)])

    # Rupees
    font = pygame.font.Font(None, 28)
    rupee_text = font.render(f"× {player.rupees}", True, RUPEE)
    screen.blit(rupee_text, (WIDTH - 80, 10))

    # Enemy count
    enemy_text = font.render(f"Slimes: {len(enemies)}", True, WHITE)
    screen.blit(enemy_text, (WIDTH // 2 - 60, 10))

    # Attack cooldown indicator
    if player.attack_timer > 0:
        pct = player.attack_timer / player.attack_cooldown
        pygame.draw.rect(screen, (255, 200, 0), (WIDTH - 180, 28, 160 * (1 - pct), 6))


def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption(TITLE)
    clock = pygame.time.Clock()
    font_big = pygame.font.Font(None, 72)
    font_med = pygame.font.Font(None, 42)

    # Game objects
    player = Player(WIDTH // 2, HEIGHT // 2 + 40)
    walls = create_walls()
    enemies = [Enemy(random.randint(80, WIDTH-80), random.randint(80, HEIGHT-80)) for _ in range(5)]
    rupees = [Rupee(random.randint(100, WIDTH-100), random.randint(100, HEIGHT-100)) for _ in range(6)]

    game_state = "playing"  # playing, win, lose
    keys_pressed = set()

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                keys_pressed.add(event.key)
                if event.key == pygame.K_SPACE and game_state == "playing":
                    player.attack(enemies)
                if event.key == pygame.K_r and game_state != "playing":
                    # Restart
                    player = Player(WIDTH // 2, HEIGHT // 2 + 40)
                    enemies = [Enemy(random.randint(80, WIDTH-80), random.randint(80, HEIGHT-80)) for _ in range(5)]
                    rupees = [Rupee(random.randint(100, WIDTH-100), random.randint(100, HEIGHT-100)) for _ in range(6)]
                    game_state = "playing"
            if event.type == pygame.KEYUP:
                keys_pressed.discard(event.key)

        if game_state == "playing":
            # Movement
            dx = dy = 0
            if pygame.K_LEFT in keys_pressed or pygame.K_a in keys_pressed:
                dx = -1
                player.direction = "left"
            if pygame.K_RIGHT in keys_pressed or pygame.K_d in keys_pressed:
                dx = 1
                player.direction = "right"
            if pygame.K_UP in keys_pressed or pygame.K_w in keys_pressed:
                dy = -1
                player.direction = "up"
            if pygame.K_DOWN in keys_pressed or pygame.K_s in keys_pressed:
                dy = 1
                player.direction = "down"

            if dx != 0 and dy != 0:
                dx *= 0.707
                dy *= 0.707

            player.move(dx, dy, walls)
            player.update()

            # Update enemies
            for enemy in enemies[:]:
                enemy.update(player, walls)
                # Enemy-player collision
                dist = math.hypot(enemy.x - player.x, enemy.y - player.y)
                if dist < 28:
                    if player.take_damage(1):
                        # Knock player back
                        kdx = (player.x - enemy.x) / max(dist, 1) * 6
                        kdy = (player.y - enemy.y) / max(dist, 1) * 6
                        player.knockback_x = kdx
                        player.knockback_y = kdy
                    if player.health <= 0:
                        game_state = "lose"

            # Update rupees + collection
            for rupee in rupees[:]:
                rupee.update()
                dist = math.hypot(rupee.x - player.x, rupee.y - player.y)
                if dist < 22:
                    player.rupees += 1
                    rupees.remove(rupee)
                    # Spawn new rupee sometimes
                    if random.random() < 0.4:
                        rupees.append(Rupee(random.randint(100, WIDTH-100), random.randint(100, HEIGHT-100)))

            # Win condition
            if len(enemies) == 0:
                game_state = "win"

        # === DRAW ===
        draw_background(screen)

        # Draw walls
        for wall in walls:
            pygame.draw.rect(screen, WALL, wall, border_radius=4)
            pygame.draw.rect(screen, (70, 70, 70), wall, 3, border_radius=4)

        # Draw rupees
        for rupee in rupees:
            rupee.draw(screen)

        # Draw enemies
        for enemy in enemies:
            enemy.draw(screen)

        # Draw player
        player.draw(screen)

        # UI
        draw_ui(screen, player, enemies)

        # Game over / Win screens
        if game_state == "win":
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 160))
            screen.blit(overlay, (0, 0))
            text = font_big.render("VICTORY!", True, YELLOW)
            screen.blit(text, (WIDTH//2 - text.get_width()//2, 180))
            sub = font_med.render(f"You collected {player.rupees} rupees!", True, WHITE)
            screen.blit(sub, (WIDTH//2 - sub.get_width()//2, 270))
            hint = font_med.render("Press R to play again", True, (200, 200, 200))
            screen.blit(hint, (WIDTH//2 - hint.get_width()//2, 380))

        elif game_state == "lose":
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((80, 0, 0, 140))
            screen.blit(overlay, (0, 0))
            text = font_big.render("GAME OVER", True, (255, 80, 80))
            screen.blit(text, (WIDTH//2 - text.get_width()//2, 200))
            sub = font_med.render(f"Rupees collected: {player.rupees}", True, WHITE)
            screen.blit(sub, (WIDTH//2 - sub.get_width()//2, 290))
            hint = font_med.render("Press R to try again", True, (200, 200, 200))
            screen.blit(hint, (WIDTH//2 - hint.get_width()//2, 380))

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
