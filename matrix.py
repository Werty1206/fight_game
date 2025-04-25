import pygame
import math
import random
from pygame.math import Vector2

pygame.init()
WIDTH, HEIGHT = 1200, 800
screen = pygame.display.set_mode((WIDTH, HEIGHT))
clock = pygame.time.Clock()
pygame.mixer.init()
# Цвета и стили
COLORS = {
    "red": (200, 50, 50),
    "blue": (50, 100, 200),
    "ui_bg": (40, 40, 50),
    "ui_border": (80, 80, 100),
    "button": (70, 70, 90),
    "button_hover": (100, 100, 120),
    "text": (230, 230, 240),
    "background": (30, 30, 30),
    "preview": (150, 150, 150, 100)
}

SOUNDS = {
    "shot": "sounds/shot.wav",
    "explosion": "sounds/explosion.wav",
    "swords": "sounds/swords.wav"
}
pygame.mixer.music.set_volume(0.3)
# Шрифты
try:
    font = pygame.font.Font("fonts/ComicRelief-Regular.ttf", 24)
except:
    font = pygame.font.SysFont('Arial', 24)

class Button:
    def __init__(self, x, y, width, height, text, callback):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.callback = callback
        self.hovered = False

    def draw(self, surface):
        color = COLORS["button_hover"] if self.hovered else COLORS["button"]
        pygame.draw.rect(surface, color, self.rect, border_radius=5)
        pygame.draw.rect(surface, COLORS["ui_border"], self.rect, 2, border_radius=5)
        
        text_surf = font.render(self.text, True, COLORS["text"])
        text_rect = text_surf.get_rect(center=self.rect.center)
        surface.blit(text_surf, text_rect)

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.hovered = self.rect.collidepoint(event.pos)
            
        elif event.type == pygame.MOUSEBUTTONDOWN and self.hovered:
            self.callback()

class UnitSelector:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, 640, 80)
        self.buttons = [
            Button(x + 10, y + 10, 240, 60, "Пехота", lambda: None),
            Button(x + 220, y + 10, 240, 60, "Кавалерия", lambda: None),
            Button(x + 430, y + 10, 240, 60, "Артиллерия", lambda: None)
        ]
        self.active_index = 0

    def draw(self, surface):
        pygame.draw.rect(surface, COLORS["ui_bg"], self.rect, border_radius=5)
        pygame.draw.rect(surface, COLORS["ui_border"], self.rect, 2, border_radius=5)
        
        for i, btn in enumerate(self.buttons):
            btn.rect.width = 200 if i == self.active_index else 200
            btn.rect.height = 60 if i == self.active_index else 50
            btn.draw(surface)

class Unit:
    def __init__(self, team, pos, unit_type):
        self.team = team
        self.pos = Vector2(pos)
        self.target = None
        self.unit_type = unit_type
        self.speed = 2.25 if unit_type == 'cavalry' else 1.5 if unit_type == 'artillery' else 1.0
        self.attack_range = 15
        self.last_shot = 0
        self.projectiles = []
        self.angle = 0
        self.size = 10
        self.collision_radius = 20
        self.sounds = {
            'shot': pygame.mixer.Sound(SOUNDS["shot"]),
            'explosion': pygame.mixer.Sound(SOUNDS["explosion"]),
            'swords': pygame.mixer.Sound(SOUNDS["swords"]),

        }

    def find_target(self, enemies):
        closest = None
        min_dist = float('inf')
        for enemy in enemies:
            dist = self.pos.distance_to(enemy.pos)
            if dist < min_dist:
                min_dist = dist
                closest = enemy
        return closest

    def check_collision(self, others):
        for other in others:
            if other is self:
                continue
            distance = self.pos.distance_to(other.pos)
            if distance < self.collision_radius:
                direction = (self.pos - other.pos).normalize()
                self.pos += direction * (self.collision_radius - distance) * 0.5

    def update(self, enemies, allies):
        self.check_collision(allies)

        if self.unit_type == 'artillery':
            if pygame.time.get_ticks() - self.last_shot > 5000:
                target = self.find_target(enemies)
                if target:
                    self.shoot(target.pos)
                    self.last_shot = pygame.time.get_ticks()
            self.update_projectiles(enemies)
            return

        if not self.target or self.target not in enemies:
            self.target = self.find_target(enemies)
        
        if self.target:
            direction = self.target.pos - self.pos
            if direction.length() > self.attack_range:
                self.pos += direction.normalize() * self.speed
                self.angle = math.degrees(math.atan2(-direction.y, direction.x)) - 90

    def shoot(self, target_pos):
        deviation = random.uniform(-5, 5)
        direction = (target_pos - self.pos).normalize().rotate(deviation)
        self.projectiles.append({
            'pos': Vector2(self.pos),
            'direction': direction,
            'distance': 0,
            'max_distance': self.pos.distance_to(target_pos) * 1.2
        })
        self.sounds['shot'].play()

    def update_projectiles(self, enemies):
        for proj in self.projectiles[:]:
            proj['pos'] += proj['direction'] * 16
            proj['distance'] += 16
            if proj['distance'] > proj['max_distance']:
                self.projectiles.remove(proj)
                continue
            
            hit = False
            for i, enemy in enumerate(enemies[:]):
                if enemy.pos.distance_to(proj['pos']) < 10:
                    enemies.remove(enemy)
                    hit = True
                    break
            if hit:
                self.sounds['explosion'].play()
                self.projectiles.remove(proj)
                

    def draw(self):
        color = COLORS["red"] if self.team == 'red' else COLORS["blue"]
        if self.unit_type == 'infantry':
            pygame.draw.circle(screen, color, (int(self.pos.x), int(self.pos.y)), self.size)
        elif self.unit_type == 'cavalry':
            points = [
                self.pos + Vector2(-self.size, -self.size).rotate(self.angle),
                self.pos + Vector2(self.size, -self.size).rotate(self.angle),
                self.pos + Vector2(self.size, self.size).rotate(self.angle),
                self.pos + Vector2(-self.size, self.size).rotate(self.angle)
            ]
            pygame.draw.polygon(screen, color, points)
        else:
            points = [
                self.pos + Vector2(0, -self.size*1.5),
                self.pos + Vector2(-self.size, self.size),
                self.pos + Vector2(self.size, self.size)
            ]
            pygame.draw.polygon(screen, color, points)

        for proj in self.projectiles:
            pygame.draw.circle(screen, COLORS["text"], (int(proj['pos'].x), int(proj['pos'].y)), 3)

class Game:
    def __init__(self):
        self.reset()
        self.selector = UnitSelector(20, 20)
        self.team_panel = pygame.Rect(WIDTH - 250, 20, 240, 60)
        self.start_btn = Button(WIDTH//2 - 100, HEIGHT - 80, 200, 50, "НАЧАТЬ БОЙ", self.start_battle)
        self.switch_team_btn = Button(WIDTH - 250, 80, 240, 40, "Сменить команду", self.switch_team)
        self.ui_rects = []
        self.sounds = {
            'shot': pygame.mixer.Sound(SOUNDS["shot"]),
            'explosion': pygame.mixer.Sound(SOUNDS["explosion"]),
            'swords': pygame.mixer.Sound(SOUNDS["swords"]),
        }
        self.sound_btn = Button(WIDTH - 120, HEIGHT - 40, 100, 30, "Sound ON", self.toggle_sound)
        pygame.mixer.music.set_volume(0.3)


    def reset(self):
        self.teams = {'red': [], 'blue': []}
        self.current_team = 'red'
        self.placement_phase = True
        self.unit_types = ['infantry', 'cavalry', 'artillery']
        self.selected_unit = 0
        self.min_distance = 20
        self.mouse_down = False
        self.last_placed_pos = None
        self.game_over = False
        self.winner = None

    def update_ui_rects(self):
        """Обновляем список запретных зон интерфейса"""
        self.ui_rects = [
            self.selector.rect,
            self.team_panel,
            self.start_btn.rect,
            self.switch_team_btn.rect,
            pygame.Rect(20, HEIGHT-120, 150, 50),     # Красные счетчики
            pygame.Rect(WIDTH-170, HEIGHT-120, 150, 50)  # Синие счетчики
        ]
    
    def toggle_sound(self):
        if pygame.mixer.music.get_volume() > 0:
            pygame.mixer.music.set_volume(0)
            for sound in self.sounds.values():
                sound.set_volume(0)
        else:
            pygame.mixer.music.set_volume(0.3)
            for sound in self.sounds.values():
                sound.set_volume(0.5)
    
    def start_battle(self):
        if self.placement_phase and len(self.teams['red']) > 0 and len(self.teams['blue']) > 0:
            self.placement_phase = False

    def switch_team(self):
        self.current_team = 'blue' if self.current_team == 'red' else 'red'

    def handle_click(self, pos):
        pos_vec = Vector2(pos)
        
        # Проверка на клик в зоне интерфейса
        for rect in self.ui_rects:
            if rect.collidepoint(pos_vec):
                return False
        
        # Остальная проверка...
        for unit in self.teams[self.current_team]:
            if pos_vec.distance_to(unit.pos) < self.min_distance:
                return False
        
        unit_type = self.unit_types[self.selected_unit]
        self.teams[self.current_team].append(Unit(self.current_team, pos, unit_type))
        return True

    def check_collisions(self):
        red = self.teams['red']
        blue = self.teams['blue']
        
        if not red and not blue:
            self.game_over = True
            self.winner = 'Draw'
        elif not red:
            self.game_over = True
            self.winner = 'Blue'
        elif not blue:
            self.game_over = True
            self.winner = 'Red'
        
        if self.game_over:
            return

        pairs = []
        for attacker in red[:]:
            for defender in blue[:]:
                if attacker.pos.distance_to(defender.pos) < attacker.attack_range:
                    pairs.append((attacker, defender))

        for a, b in pairs:
            if a not in red or b not in blue:
                continue
            
            if a.unit_type == 'infantry' and b.unit_type == 'artillery':
                blue.remove(b)
                continue
                
            if b.unit_type == 'infantry' and a.unit_type == 'artillery':
                red.remove(a)
                continue

            if self.resolve_combat(a, b):
                if a in red: red.remove(a)
            else:
                if b in blue: blue.remove(b)

        for team in self.teams.values():
            for i, unit in enumerate(team):
                unit.check_collision(team[:i] + team[i+1:])

    def resolve_combat(self, a, b):
        if {a.unit_type, b.unit_type} == {'infantry', 'infantry'}:
            self.sounds['swords'].play()
        elif 'cavalry' in {a.unit_type, b.unit_type}:
            self.sounds['swords'].play()
        if a.unit_type == 'infantry' and b.unit_type == 'artillery':
            return False
        if a.unit_type == 'cavalry' and b.unit_type == 'artillery':
            return False
        if a.unit_type == 'artillery' and b.unit_type == 'cavalry':
            return True
        if a.unit_type == 'cavalry' and b.unit_type == 'infantry':
            return random.random() < 0.3
        if a.unit_type == 'infantry' and b.unit_type == 'cavalry':
            return random.random() < 0.7
        if a.unit_type == b.unit_type:
            return random.choice([True, False])
        return random.choice([True, False])

    def draw_team_panel(self):
        pygame.draw.rect(screen, COLORS["ui_bg"], self.team_panel, border_radius=5)
        pygame.draw.rect(screen, COLORS["ui_border"], self.team_panel, 2, border_radius=5)
        
        team_color = COLORS[self.current_team]
        pygame.draw.circle(screen, team_color, (self.team_panel.x + 30, self.team_panel.centery), 15)
        text = font.render(f"Команда: {self.current_team.capitalize()}", True, COLORS["text"])
        screen.blit(text, (self.team_panel.x + 60, self.team_panel.centery - 15))

    def draw_unit_counters(self):
        red_count = len(self.teams['red'])
        blue_count = len(self.teams['blue'])
        
        pygame.draw.rect(screen, COLORS["red"], (20, HEIGHT-120, 150, 50), border_radius=5)
        text = font.render(f"Красные: {red_count}", True, COLORS["text"])
        screen.blit(text, (30, HEIGHT-110))
        
        pygame.draw.rect(screen, COLORS["blue"], (WIDTH-170, HEIGHT-120, 150, 50), border_radius=5)
        text = font.render(f"Синие: {blue_count}", True, COLORS["text"])
        screen.blit(text, (WIDTH-160, HEIGHT-110))

    def draw_ui(self):
        
        if self.game_over:
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 200))
            screen.blit(overlay, (0, 0))
            
            texts = [
                f"Победитель: {self.winner}",
                "R - Новая игра",
                "Q - Выход"
            ]
            for i, text in enumerate(texts):
                surf = font.render(text, True, COLORS["text"])
                screen.blit(surf, (WIDTH//2 - surf.get_width()//2, HEIGHT//2 - 50 + 30*i))
        else:
            self.selector.draw(screen)
            self.draw_team_panel()
            self.draw_unit_counters()
            
            if self.placement_phase:
                self.sound_btn.draw(screen)
                self.start_btn.draw(screen)
                self.switch_team_btn.draw(screen)
        self.update_ui_rects()

    def handle_ui_events(self, event):
        for element in [self.start_btn, self.switch_team_btn]:
            element.handle_event(event)
        
        if self.placement_phase:
            for i, btn in enumerate(self.selector.buttons):
                btn.handle_event(event)
                if btn.rect.collidepoint(pygame.mouse.get_pos()):
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        self.selected_unit = i
                        self.selector.active_index = i

game = Game()
running = True

while running:
    screen.fill(COLORS["background"])
    current_mouse_pos = pygame.mouse.get_pos()
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        
        game.handle_ui_events(event)
        
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1 and game.placement_phase and not game.game_over:
                game.mouse_down = True
                if game.handle_click(current_mouse_pos):
                    game.last_placed_pos = Vector2(current_mouse_pos)
        
        if event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                game.mouse_down = False
                game.last_placed_pos = None
        
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_q:
                running = False
            if event.key == pygame.K_r:
                if game.game_over:
                    game.reset()
                elif game.placement_phase:
                    game.switch_team()
            if game.placement_phase and not game.game_over:
                if pygame.K_1 <= event.key <= pygame.K_3:
                    game.selected_unit = event.key - pygame.K_1
                    game.selector.active_index = game.selected_unit

    if game.placement_phase and game.mouse_down and not game.game_over:
        if game.last_placed_pos is not None:
            # Добавляем проверку на UI зоны
            if (Vector2(current_mouse_pos).distance_to(game.last_placed_pos) >= game.min_distance 
                and not any(rect.collidepoint(current_mouse_pos) for rect in game.ui_rects)):
                if game.handle_click(current_mouse_pos):
                    game.last_placed_pos = Vector2(current_mouse_pos)

    if not game.placement_phase and not game.game_over:
        for team in game.teams.values():
            for unit in team:
                enemies = game.teams['blue'] if unit.team == 'red' else game.teams['red']
                allies = [u for u in team if u is not unit]
                unit.update(enemies, allies)
        game.check_collisions()

    for unit in game.teams['red'] + game.teams['blue']:
        unit.draw()

    if game.placement_phase and not game.game_over:
        preview_color = COLORS[game.current_team]
        mouse_pos = Vector2(pygame.mouse.get_pos())
        unit_type = game.unit_types[game.selected_unit]
        
        # Рисуем радиус размещения
        pygame.draw.circle(screen, preview_color + (50,), (int(mouse_pos.x), int(mouse_pos.y)), game.min_distance, 2)
        
        # Рисуем предпросмотр юнита
        if unit_type == 'infantry':
            pygame.draw.circle(screen, preview_color + (100,), (int(mouse_pos.x), int(mouse_pos.y)), 10)
        elif unit_type == 'cavalry':
            points = [
                mouse_pos + Vector2(-10, -10),
                mouse_pos + Vector2(10, -10),
                mouse_pos + Vector2(10, 10),
                mouse_pos + Vector2(-10, 10)
            ]
            pygame.draw.polygon(screen, preview_color + (100,), points)
        else:
            points = [
                mouse_pos + Vector2(0, -15),
                mouse_pos + Vector2(-10, 10),
                mouse_pos + Vector2(10, 10)
            ]
            pygame.draw.polygon(screen, preview_color + (100,), points)

    game.draw_ui()
    pygame.display.flip()
    clock.tick(60)

pygame.quit()