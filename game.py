import pygame
import random
import sys
import json
import math
from abc import ABC, abstractmethod

WIDTH, HEIGHT = 900, 700
FPS = 60 

C_BG = (5, 5, 15)          
C_GRID = (20, 40, 60)      
C_TEXT_MAIN = (240, 240, 255)
C_NEON_CYAN = (0, 255, 255)
C_NEON_MAGENTA = (255, 0, 150)
C_NEON_GREEN = (50, 255, 50) 
C_NEON_YELLOW = (255, 255, 0) 
C_ERROR = (255, 50, 50)    

class LevelManager:
    def __init__(self):
        self.level = 1
        
    def check_level_up(self, current_score):
        calculated_level = 1 + (current_score // 100)
        if calculated_level > self.level:
            self.level = calculated_level
            return True
        return False

    def get_spawn_delay(self):
        return max(20, 90 - (self.level * 5))

    def get_speed_multiplier(self):
        return self.level * 0.3

class ScreenShake:
    def __init__(self):
        self.intensity = 0
        self.decay = 0.9 
        self.offset_x = 0
        self.offset_y = 0

    def trigger(self, amount):
        self.intensity = amount

    def update(self):
        if self.intensity > 0.5:
            self.offset_x = random.uniform(-self.intensity, self.intensity)
            self.offset_y = random.uniform(-self.intensity, self.intensity)
            self.intensity *= self.decay
        else:
            self.offset_x = 0
            self.offset_y = 0
            self.intensity = 0
    
    def get_offset(self):
        return (self.offset_x, self.offset_y)

class DataManager:
    def __init__(self):
        self.__score = 0
        self.__highscore = self._load_data()
        self.__health = 100
        self.__max_health = 100
        self.__streak = 0 

    def _load_data(self):
        try:
            with open("game_data.json", "r") as f:
                return json.load(f).get("highscore", 0)
        except:
            return 0

    def save_data(self):
        if self.__score > self.__highscore:
            self.__highscore = self.__score
            with open("game_data.json", "w") as f:
                json.dump({"highscore": self.__highscore}, f)

    @property
    def score(self): return self.__score
    
    @property
    def highscore(self): return self.__highscore
    
    @property
    def health(self): return self.__health
    
    @property
    def streak(self): return self.__streak 
    def reset_stats(self):
        self.__score = 0
        self.__health = self.__max_health
        self.__streak = 0

    def add_score(self, amount):
        self.__score += amount

    def take_damage(self, amount):
        self.__health -= amount
        self.reset_streak() 

    def heal(self, amount):
        self.__health += amount
        if self.__health > self.__max_health:
            self.__health = self.__max_health

    def is_alive(self):
        return self.__health > 0

    def increment_streak(self):
        self.__streak += 1
        if self.__streak > 0 and self.__streak % 5 == 0:
            return True 
        return False

    def reset_streak(self):
        self.__streak = 0

class Entity(ABC, pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.x = x
        self.y = y

    @abstractmethod
    def update(self): pass

    @abstractmethod
    def draw(self, surface, offset): pass

class Particle(Entity):
    def __init__(self, x, y, color):
        super().__init__(x, y)
        angle = random.uniform(0, 6.28)
        speed = random.uniform(2, 5)
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed
        self.life = 255
        self.color = color
        self.size = random.randint(2, 4)

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.life -= 8 

    def draw(self, surface, offset):
        if self.life > 0:
            tx = self.x + offset[0]
            ty = self.y + offset[1]
            s = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
            s.fill((*self.color, self.life))
            surface.blit(s, (tx, ty))

class FloatingText(Entity):
    def __init__(self, x, y, text, color):
        super().__init__(x, y)
        self.text = text
        self.color = color
        self.font = pygame.font.Font(None, 30)
        self.life = 255
        self.vy = -2 

    def update(self):
        self.y += self.vy
        self.life -= 5 

    def draw(self, surface, offset):
        if self.life > 0:
            tx = self.x + offset[0]
            ty = self.y + offset[1]
            txt_surf = self.font.render(self.text, True, self.color)
            txt_surf.set_alpha(self.life)
            surface.blit(txt_surf, (tx, ty))

class Meteor(Entity):
    def __init__(self, text, level_speed_bonus):
        x = random.randint(50, WIDTH - 150)
        super().__init__(x, -60)
        self.text = text
        self.base_speed = random.uniform(1.0, 2.0) + level_speed_bonus
        self.font = pygame.font.Font(None, 40)
        self.color = C_TEXT_MAIN
        self.active_glow = False

    def update(self):
        self.y += self.base_speed

    def check_match(self, input_text):
        if self.text.startswith(input_text) and len(input_text) > 0:
            self.color = C_NEON_CYAN
            self.active_glow = True
        else:
            self.color = C_TEXT_MAIN
            self.active_glow = False

    def draw(self, surface, offset):
        tx = self.x + offset[0]
        ty = self.y + offset[1]
        if self.active_glow:
            glow_surf = self.font.render(self.text, True, C_NEON_CYAN)
            surface.blit(glow_surf, (tx - 1, ty))
            surface.blit(glow_surf, (tx + 1, ty))
        
        main_surf = self.font.render(self.text, True, self.color)
        surface.blit(main_surf, (tx, ty))

class Button:
    def __init__(self, text, y_pos, action):
        self.text = text
        self.rect = pygame.Rect(0, 0, 200, 50)
        self.rect.center = (WIDTH // 2, y_pos)
        self.action = action 
        self.font = pygame.font.Font(None, 50)
        self.hovered = False

    def check_hover(self, mouse_pos):
        self.hovered = self.rect.collidepoint(mouse_pos)

    def handle_click(self):
        if self.hovered:
            self.action()

    def draw(self, surface):
        color = C_NEON_CYAN if self.hovered else (100, 100, 100)
        text_surf = self.font.render(self.text, True, color)
        pygame.draw.rect(surface, color, self.rect, 2, border_radius=10)
        text_rect = text_surf.get_rect(center=self.rect.center)
        surface.blit(text_surf, text_rect)

class CyberTyperGame:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("CYBER TYPER: NEON PROTOCOL v2.3 - STREAK EDITION")
        self.clock = pygame.time.Clock()
        
        self.data = DataManager()
        self.shake = ScreenShake()
        self.level_manager = LevelManager()
        
        self.state = "MENU" 
        self.words = ["system", "hacker", "protocol", "circuit", "binary", 
                      "cyber", "neon", "matrix", "linux", "python", "script",
                      "server", "proxy", "firewall", "encryption", "node", "data",
                      "java", "object", "class", "void", "public", "static"]
        
        self.levelup_popup_timer = 0
        self.setup_menu()

    def setup_menu(self):
        self.buttons = [
            Button("START", 350, self.start_game),
            Button("QUIT", 450, self.quit_game)
        ]

    def start_game(self):
        self.data.reset_stats()
        self.level_manager = LevelManager()
        self.meteors = []
        self.particles = []
        self.floaters = [] 
        self.input_buffer = ""
        self.spawn_timer = 0
        self.state = "PLAY"

    def quit_game(self):
        pygame.quit()
        sys.exit()

    def spawn_particles(self, x, y, color):
        for _ in range(12):
            self.particles.append(Particle(x, y, color))

    def run(self):
        running = True
        while running:
            self.screen.fill(C_BG)
            mouse_pos = pygame.mouse.get_pos()
            
            # --- EVENTS ---
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                
                if self.state == "MENU":
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        for btn in self.buttons:
                            btn.handle_click()

                elif self.state == "PLAY":
                    if event.type == pygame.KEYDOWN:
                        
                        if event.key == pygame.K_RETURN:
                            if len(self.input_buffer) > 0: 
                                self.input_buffer = "" 
                                self.data.add_score(-5) 
                                self.data.reset_streak() 
                                self.shake.trigger(3) 
                                self.floaters.append(FloatingText(WIDTH//2, HEIGHT-60, "-5 (Panic)", C_ERROR))
                        
                        elif event.key == pygame.K_BACKSPACE:
                            self.input_buffer = self.input_buffer[:-1]
                        
                        elif event.key == pygame.K_ESCAPE:
                            self.state = "GAMEOVER"
                            self.data.save_data()
                        else:
                            if event.unicode.isalpha():
                                self.input_buffer += event.unicode

                elif self.state == "GAMEOVER":
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_RETURN:
                            self.state = "MENU"

            self.shake.update()
            offset = self.shake.get_offset()

            if self.state == "MENU":
                title_font = pygame.font.Font(None, 80)
                title = title_font.render("CYBER TYPER", True, C_NEON_MAGENTA)
                self.screen.blit(title, (WIDTH//2 - title.get_width()//2, 150))
                
                score_font = pygame.font.Font(None, 40)
                hs_text = score_font.render(f"High Score: {self.data.highscore}", True, C_NEON_CYAN)
                self.screen.blit(hs_text, (WIDTH//2 - hs_text.get_width()//2, 230))

                for btn in self.buttons:
                    btn.check_hover(mouse_pos)
                    btn.draw(self.screen)

            elif self.state == "PLAY":
                if self.level_manager.check_level_up(self.data.score):
                    self.levelup_popup_timer = 60
                    self.shake.trigger(10)

                self.spawn_timer += 1
                if self.spawn_timer > self.level_manager.get_spawn_delay():
                    self.meteors.append(Meteor(random.choice(self.words), self.level_manager.get_speed_multiplier()))
                    self.spawn_timer = 0

                hit_index = -1
                for i, meteor in enumerate(self.meteors):
                    meteor.check_match(self.input_buffer)
                    meteor.update()
                    
                    if self.input_buffer == meteor.text:
                        hit_index = i
                        self.data.add_score(10)
                        
                        is_bonus = self.data.increment_streak()
                        if is_bonus:
                            self.data.heal(10) 
                            self.floaters.append(FloatingText(WIDTH//2, HEIGHT//2, "STREAK 5X! +10 HP", C_NEON_GREEN))
                            self.shake.trigger(8)

                        self.spawn_particles(meteor.x, meteor.y, C_NEON_CYAN)
                        self.floaters.append(FloatingText(meteor.x, meteor.y, "+10", C_NEON_CYAN)) 
                        self.input_buffer = ""
                        self.shake.trigger(5)
                    
                    elif meteor.y > HEIGHT:
                        self.data.take_damage(20) 
                        self.floaters.append(FloatingText(meteor.x, HEIGHT-50, "-20 HP", C_ERROR)) 
                        self.floaters.append(FloatingText(meteor.x, HEIGHT-80, "Streak Lost!", C_ERROR))
                        self.shake.trigger(20)
                        self.meteors.pop(i)
                        flash_s = pygame.Surface((WIDTH, HEIGHT))
                        flash_s.fill(C_ERROR)
                        flash_s.set_alpha(50)
                        self.screen.blit(flash_s, (0,0))
                        break

                if hit_index != -1:
                    self.meteors.pop(hit_index)

                for p in self.particles[:]:
                    p.update()
                    if p.life <= 0: self.particles.remove(p)
                
                for f in self.floaters[:]:
                    f.update()
                    if f.life <= 0: self.floaters.remove(f)

                
                for m in self.meteors: m.draw(self.screen, offset)
                for p in self.particles: p.draw(self.screen, offset)
                for f in self.floaters: f.draw(self.screen, offset) 

                pygame.draw.rect(self.screen, C_GRID, (0, HEIGHT-60, WIDTH, 60))
                
                inp_surf = pygame.font.Font(None, 50).render(self.input_buffer, True, C_NEON_MAGENTA)
                self.screen.blit(inp_surf, (WIDTH//2 - inp_surf.get_width()//2 + offset[0], HEIGHT-45 + offset[1]))
                
                tip_font = pygame.font.Font(None, 20)
                tip_surf = tip_font.render("PRESS ENTER TO CLEAR TYPO (-5 PTS)", True, (100, 100, 100))
                self.screen.blit(tip_surf, (WIDTH//2 - tip_surf.get_width()//2, HEIGHT-15))

                pygame.draw.rect(self.screen, (50,0,0), (20, 20, 200, 20))
                pygame.draw.rect(self.screen, C_ERROR, (20, 20, 2 * self.data.health, 20))
                pygame.draw.rect(self.screen, (200,200,200), (20, 20, 200, 20), 2)
                
                ui_font = pygame.font.Font(None, 36)
                sc_surf = ui_font.render(f"SCORE: {self.data.score}", True, C_TEXT_MAIN)
                lvl_surf = ui_font.render(f"LEVEL: {self.level_manager.level}", True, C_NEON_GREEN)
                
                streak_color = C_NEON_YELLOW if self.data.streak > 0 else (100, 100, 100)
                streak_surf = ui_font.render(f"STREAK: {self.data.streak}", True, streak_color)

                self.screen.blit(sc_surf, (WIDTH - 180, 20))
                self.screen.blit(lvl_surf, (WIDTH - 180, 50))
                self.screen.blit(streak_surf, (WIDTH - 180, 80))

                if self.levelup_popup_timer > 0:
                    self.levelup_popup_timer -= 1
                    popup_font = pygame.font.Font(None, 100)
                    popup_surf = popup_font.render("LEVEL UP!", True, C_NEON_GREEN)
                    if self.levelup_popup_timer % 10 < 5: 
                         self.screen.blit(popup_surf, (WIDTH//2 - popup_surf.get_width()//2, HEIGHT//2 - 100))

                if not self.data.is_alive():
                    self.data.save_data()
                    self.state = "GAMEOVER"

            elif self.state == "GAMEOVER":
                overlay = pygame.Surface((WIDTH, HEIGHT))
                overlay.fill((0,0,0))
                overlay.set_alpha(150)
                self.screen.blit(overlay, (0,0))

                go_font = pygame.font.Font(None, 100)
                go_text = go_font.render("SYSTEM FAILURE", True, C_ERROR)
                self.screen.blit(go_text, (WIDTH//2 - go_text.get_width()//2 + offset[0], 250 + offset[1]))
                
                info_font = pygame.font.Font(None, 40)
                info = info_font.render(f"Final Score: {self.data.score}", True, C_TEXT_MAIN)
                restart = info_font.render("Press ENTER to Main Menu", True, C_NEON_CYAN)
                self.screen.blit(info, (WIDTH//2 - info.get_width()//2, 350))
                self.screen.blit(restart, (WIDTH//2 - restart.get_width()//2, 450))
            
            pygame.display.flip()
            self.clock.tick(FPS)

if __name__ == "__main__":
    game = CyberTyperGame()
    game.run()