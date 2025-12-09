import pygame
import random
import sys
import json
import math
import os 
import cv2  
from abc import ABC, abstractmethod

if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DIR_SOUND = os.path.join(BASE_DIR, "sound")
DIR_BG = os.path.join(BASE_DIR, "background")

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
C_GRAY = (100, 100, 100)

class VideoBackground:
    def __init__(self, filepath, width, height):
        self.filepath = filepath
        self.width = width
        self.height = height
        self.cap = None
        self.surface = None
        self.success = False
        
        self.scale_buffer = 50 

        if os.path.exists(filepath):
            try:
                self.cap = cv2.VideoCapture(filepath)
                self.success = True
                print(f"[SYSTEM] Video loaded: {filepath}")
            except Exception as e:
                print(f"[ERROR] Failed to load video: {e}")
        else:
            print(f"[WARNING] Video file not found: {filepath}")

    def update(self):
        if not self.success:
            return

        ret, frame = self.cap.read()

        if not ret:
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            ret, frame = self.cap.read()
        
        if ret:
            new_w = self.width + self.scale_buffer
            new_h = self.height + self.scale_buffer
            frame = cv2.resize(frame, (new_w, new_h))
            
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            self.surface = pygame.image.frombuffer(frame.tobytes(), (new_w, new_h), "RGB")

    def draw(self, screen, offset=(0,0)):
        if self.surface:
            center_offset = - (self.scale_buffer / 2)
            
            bg_x = center_offset + (offset[0] * 0.5)
            bg_y = center_offset + (offset[1] * 0.5)
            screen.blit(self.surface, (bg_x, bg_y))
        else:
            screen.fill(C_BG)

class SoundManager:
    def __init__(self):
        self.sounds = {}
        self.music_playing = False
        self.sfx_volume = 0.3   
        self.music_volume = 0.2 
        
        try:
            pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=2048)
            print("[SYSTEM] Audio Mixer Initialized")
        except pygame.error:
            print("[WARNING] No Audio Device Found")

        self.load_sound("type", os.path.join(DIR_SOUND, "type.wav"))
        self.load_sound("explode", os.path.join(DIR_SOUND, "explode.wav"))
        self.load_sound("error", os.path.join(DIR_SOUND, "error.wav"))
        self.load_sound("damage", os.path.join(DIR_SOUND, "damage.wav"))
        self.load_sound("levelup", os.path.join(DIR_SOUND, "levelup.wav"))
        self.load_sound("gameover", os.path.join(DIR_SOUND, "gameover.wav"))
        
        self.load_music(os.path.join(DIR_SOUND, "bgm.mp3"))

    def load_sound(self, name, filepath):
        if os.path.exists(filepath):
            try:
                self.sounds[name] = pygame.mixer.Sound(filepath)
                self.sounds[name].set_volume(self.sfx_volume)
            except: pass

    def load_music(self, filepath):
        if os.path.exists(filepath):
            try:
                pygame.mixer.music.load(filepath)
                pygame.mixer.music.set_volume(self.music_volume)
                self.music_playing = True
            except: pass

    def play(self, name):
        if name in self.sounds:
            self.sounds[name].set_volume(self.sfx_volume) 
            self.sounds[name].play()

    def play_music(self):
        if self.music_playing:
            try:
                pygame.mixer.music.play(-1, 0.0, 5000) 
                pygame.mixer.music.set_volume(self.music_volume)
            except: pass

    def stop_music(self):
        try: pygame.mixer.music.fadeout(1000)
        except: pass

    def set_sfx_volume(self, volume):
        self.sfx_volume = volume
        for sound in self.sounds.values():
            sound.set_volume(volume)

    def set_music_volume(self, volume):
        self.music_volume = volume
        if self.music_playing:
            try: pygame.mixer.music.set_volume(volume)
            except: pass

class Slider:
    def __init__(self, x, y, w, h, initial_val, label):
        self.rect = pygame.Rect(x, y, w, h)
        self.val = initial_val 
        self.label = label
        self.dragging = False
        self.font = pygame.font.Font(None, 36)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                self.dragging = True
                self.update_val(event.pos[0])
        elif event.type == pygame.MOUSEBUTTONUP:
            self.dragging = False
        elif event.type == pygame.MOUSEMOTION:
            if self.dragging:
                self.update_val(event.pos[0])

    def update_val(self, mouse_x):
        relative_x = mouse_x - self.rect.x
        self.val = max(0.0, min(1.0, relative_x / self.rect.width))

    def draw(self, surface):
        label_surf = self.font.render(f"{self.label}: {int(self.val * 100)}%", True, C_TEXT_MAIN)
        surface.blit(label_surf, (self.rect.x, self.rect.y - 30))
        pygame.draw.rect(surface, C_GRID, self.rect, border_radius=5)
        fill_width = int(self.rect.width * self.val)
        fill_rect = pygame.Rect(self.rect.x, self.rect.y, fill_width, self.rect.height)
        pygame.draw.rect(surface, C_NEON_CYAN, fill_rect, border_radius=5)
        handle_x = self.rect.x + fill_width
        pygame.draw.circle(surface, C_TEXT_MAIN, (handle_x, self.rect.centery), 10)

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
        self.filepath = os.path.join(BASE_DIR, "game_data.json")
        self.__score = 0
        self.__highscore = self._load_data()
        self.__health = 100
        self.__max_health = 100
        self.__streak = 0 

    def _load_data(self):
        try:
            if os.path.exists(self.filepath):
                with open(self.filepath, "r") as f:
                    data = json.load(f)
                    return data.get("highscore", 0)
            else: return 0
        except: return 0

    def save_data(self):
        if self.__score > self.__highscore:
            self.__highscore = self.__score
        try:
            with open(self.filepath, "w") as f:
                json.dump({"highscore": self.__highscore}, f)
        except Exception as e:
            print(f"[ERROR] Failed to save data: {e}")

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

class CyberTyperGame:
    def __init__(self):
        pygame.init()
        pygame.mixer.pre_init(44100, -16, 2, 2048)
        
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("CYBER TYPER: NEON PROTOCOL")
        self.clock = pygame.time.Clock()
        
        self.sound = SoundManager()
        self.sound.play_music() 

        video_path = os.path.join(DIR_BG, "background.mp4")
        self.video_bg = VideoBackground(video_path, WIDTH, HEIGHT)

        self.data = DataManager()
        self.shake = ScreenShake()
        self.level_manager = LevelManager()
        
        self.state = "MENU" 
        self.words = ["system", "hacker", "protocol", "circuit", "binary", 
                      "cyber", "neon", "matrix", "linux", "python", "script",
                      "server", "proxy", "firewall", "encryption", "node", "data",
                      "java", "object", "class", "void", "public", "static",
                      "terminal", "root", "sudo", "apt", "kernel", "bios"]
        
        self.levelup_popup_timer = 0
        self.setup_menu()
        
        self.slider_bgm = Slider(WIDTH//2 - 150, 250, 300, 20, self.sound.music_volume, "BGM Volume")
        self.slider_sfx = Slider(WIDTH//2 - 150, 350, 300, 20, self.sound.sfx_volume, "SFX Volume")
        self.btn_back = Button("BACK", 500, self.back_to_menu)

    def setup_menu(self):
        self.buttons = [
            Button("START", 300, self.start_game),
            Button("OPTIONS", 380, self.open_options), 
            Button("QUIT", 460, self.quit_game)
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
        self.sound.play("levelup") 

    def open_options(self):
        self.state = "OPTIONS"

    def back_to_menu(self):
        self.state = "MENU"

    def quit_game(self):
        pygame.quit()
        sys.exit()

    def spawn_particles(self, x, y, color):
        for _ in range(12):
            self.particles.append(Particle(x, y, color))

    def run(self):
        running = True
        while running:
            self.shake.update()
            offset = self.shake.get_offset()

            self.video_bg.update()
            self.video_bg.draw(self.screen, offset)
            
            dark_overlay = pygame.Surface((WIDTH, HEIGHT))
            dark_overlay.fill((0, 0, 0))
            dark_overlay.set_alpha(100) 
            self.screen.blit(dark_overlay, (0,0))

            mouse_pos = pygame.mouse.get_pos()
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                
                if self.state == "MENU":
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        for btn in self.buttons:
                            btn.handle_click()

                elif self.state == "OPTIONS":
                    self.slider_bgm.handle_event(event)
                    self.slider_sfx.handle_event(event)
                    
                    self.sound.set_music_volume(self.slider_bgm.val)
                    self.sound.set_sfx_volume(self.slider_sfx.val)
                    
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        self.btn_back.handle_click()
                        if self.slider_sfx.rect.collidepoint(event.pos):
                            self.sound.play("type")

                elif self.state == "PLAY":
                    if event.type == pygame.KEYDOWN:
                        
                        if event.key == pygame.K_RETURN:
                            if len(self.input_buffer) > 0: 
                                self.input_buffer = "" 
                                self.data.add_score(-5) 
                                self.data.reset_streak() 
                                self.shake.trigger(3) 
                                self.floaters.append(FloatingText(WIDTH//2, HEIGHT-60, "-5 (Panic)", C_ERROR))
                                self.sound.play("error") 

                        elif event.key == pygame.K_BACKSPACE:
                            self.input_buffer = self.input_buffer[:-1]
                            self.sound.play("type") 
                        
                        elif event.key == pygame.K_ESCAPE:
                            self.state = "GAMEOVER"
                            self.data.save_data()
                            self.sound.stop_music()
                            self.sound.play("gameover")
                        else:
                            if event.unicode.isalpha():
                                self.input_buffer += event.unicode
                                self.sound.play("type") 

                elif self.state == "GAMEOVER":
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_RETURN:
                            self.state = "MENU"
                            self.sound.play_music() 

            if self.state == "MENU":
                title_font = pygame.font.Font(None, 80)
                title = title_font.render("CYBER TYPER", True, C_NEON_MAGENTA)
                title_shadow = title_font.render("CYBER TYPER", True, (0,0,0))
                self.screen.blit(title_shadow, (WIDTH//2 - title.get_width()//2 + 3, 103))
                self.screen.blit(title, (WIDTH//2 - title.get_width()//2, 100))
                
                score_font = pygame.font.Font(None, 40)
                hs_text = score_font.render(f"High Score: {self.data.highscore}", True, C_NEON_CYAN)
                self.screen.blit(hs_text, (WIDTH//2 - hs_text.get_width()//2, 180))

                for btn in self.buttons:
                    btn.check_hover(mouse_pos)
                    btn.draw(self.screen)

            elif self.state == "OPTIONS":
                opt_title = pygame.font.Font(None, 60).render("AUDIO SETTINGS", True, C_NEON_MAGENTA)
                self.screen.blit(opt_title, (WIDTH//2 - opt_title.get_width()//2, 100))

                self.slider_bgm.draw(self.screen)
                self.slider_sfx.draw(self.screen)

                self.btn_back.check_hover(mouse_pos)
                self.btn_back.draw(self.screen)

            elif self.state == "PLAY":
                if self.level_manager.check_level_up(self.data.score):
                    self.levelup_popup_timer = 60
                    self.shake.trigger(10)
                    self.sound.play("levelup") 

                self.spawn_timer += 1
                if self.spawn_timer > self.level_manager.get_spawn_delay():
                    self.meteors.append(Meteor(random.choice(self.words), self.level_manager.get_speed_multiplier()))
                    self.spawn_timer = 0

                meteors_to_remove = []
                hit_found = False 

                for meteor in self.meteors:
                    meteor.check_match(self.input_buffer)
                    meteor.update()
                    
                    if self.input_buffer == meteor.text and not hit_found:
                        hit_found = True
                        meteors_to_remove.append(meteor) 
                        
                        self.data.add_score(10)
                        is_bonus = self.data.increment_streak()
                        if is_bonus:
                            self.data.heal(10) 
                            self.floaters.append(FloatingText(WIDTH//2, HEIGHT//2, "STREAK 5X! +10 HP", C_NEON_GREEN))
                            self.shake.trigger(8)
                            self.sound.play("levelup")

                        self.spawn_particles(meteor.x, meteor.y, C_NEON_CYAN)
                        self.floaters.append(FloatingText(meteor.x, meteor.y, "+10", C_NEON_CYAN)) 
                        self.shake.trigger(5)
                        self.sound.play("explode")
                    
                    elif meteor.y > HEIGHT:
                        if meteor not in meteors_to_remove: 
                            meteors_to_remove.append(meteor) 
                        
                        self.data.take_damage(20) 
                        self.floaters.append(FloatingText(meteor.x, HEIGHT-50, "-20 HP", C_ERROR)) 
                        self.floaters.append(FloatingText(meteor.x, HEIGHT-80, "Streak Lost!", C_ERROR))
                        self.shake.trigger(20)
                        
                        flash_s = pygame.Surface((WIDTH, HEIGHT))
                        flash_s.fill(C_ERROR)
                        flash_s.set_alpha(50)
                        self.screen.blit(flash_s, (0,0))
                        self.sound.play("damage")
                
                if hit_found:
                    self.input_buffer = ""
                
                for m in meteors_to_remove:
                    if m in self.meteors:
                        self.meteors.remove(m)
                
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
                    self.sound.stop_music()
                    self.sound.play("gameover")

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