import pygame
import sys
import random
from moviepy.editor import VideoFileClip
import numpy as np
import os
import tempfile
import threading
import time

pygame.init()

WIDTH, HEIGHT = 1920, 1080
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Гра / Game")

try:
    horror_font = pygame.font.Font("fonts/BlackChancery.ttf", 72)
    menu_font = pygame.font.Font("fonts/BlackChancery.ttf", 72)
except:
    horror_font = pygame.font.SysFont("arial", 72, bold=True)
    menu_font = pygame.font.SysFont("arial", 72, bold=True)

try:
    font = pygame.font.Font("fonts/BlackChancery.ttf", 36)
except:
    font = pygame.font.SysFont("arial", 36, bold=True)

WHITE = (255, 255, 255)
GRAY = (180, 180, 180)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
BLOOD_RED = (136, 8, 8)
DARK_RED = (80, 0, 0)
CREEPY_WHITE = (220, 220, 220)
GREEN = (0, 255, 0)

game_state = "intro"
selection_index = 0
language = "ua"
current_level = 1
game_over = False
game_over_selection = 0
game_win = False
victory_achieved = False

GAME_DURATION = 360  
game_time = 0  
monster_speed_multiplier = 1
exit_available = False
is_hiding = False

SAFE_ZONE = pygame.Rect(800, 400, 200, 200) 
EXIT_ZONE = pygame.Rect(1700, 800, 100, 100)  
VICTORY_ZONE = pygame.Rect(100, 800, 150, 150)  
victory_available = False

KEYS = []
keys_collected = 0
total_keys = 3

texts = {
    "ua": {
        "menu": ["Почати гру", "Налаштування", "Вихід"],
        "settings": "Налаштування",
        "back": "Натисніть 'B' щоб повернутися",
        "choose_lang": "Натисніть 'U' — українська, 'E' — англійська",
        "goal_look_around": "огляньтеся",
        "goal_hello": "привіт",
        "stairs_message": "Натисніть E щоб піднятись",
        "stairs_down_message": "Натисніть E щоб спуститись",
        "game_over": ["Гра завершена", "Почати знову", "Повернутися в меню"],
        "game_win": ["Ви втекли!", "Почати знову", "Повернутися в меню"],
        "victory_message": "Перемога! Ви змогли знайти сестру, але вона вже була призраком... але ви залишились живі!",
        "goals": {
            "look_around": "Огляньтеся навколо",
            "run_away": "Утечіть від монстрів!",
            "find_keys": "Знайдіть ключі: {}/{}",
            "find_stairs": "Знайдіть сходи на 2 поверх",
            "explore": "Дослідіть локації",
            "hide": "Знайдіть схованку!",
            "escape": "Втечіть до 6 ранку!",
            "find_sister": "Знайдіть вихід біля стіни!"
        }
    },
    "en": {
        "menu": ["Start Game", "Settings", "Exit"],
        "settings": "Settings",
        "back": "Press 'B' to go back",
        "choose_lang": "Press 'U' for Ukrainian, 'E' for English",
        "goal_look_around": "look around",
        "goal_hello": "hello",
        "stairs_message": "Press E to climb",
        "stairs_down_message": "Press E to descend",
        "game_over": ["Game Over", "Start Again", "Return to Menu"],
        "game_win": ["You Escaped!", "Start Again", "Return to Menu"],
        "victory_message": "Victory! You found your sister, but she was already a ghost... but you survived!",
        "goals": {
            "look_around": "Look around",
            "run_away": "Run away from monsters!",
            "find_keys": "Find keys: {}/{}",
            "find_stairs": "Find stairs to 2nd floor",
            "explore": "Explore locations",
            "hide": "Find hiding place!",
            "escape": "Escape before 6 AM!",
            "find_sister": "Find the exit near the wall!"
        }
    }
}

BOUNDARY_OFFSET = 50
BOUNDARIES = [
    pygame.Rect(0, 0, WIDTH, BOUNDARY_OFFSET),
    pygame.Rect(0, HEIGHT-BOUNDARY_OFFSET, WIDTH, BOUNDARY_OFFSET),
    pygame.Rect(0, 0, BOUNDARY_OFFSET, HEIGHT),
    pygame.Rect(WIDTH-BOUNDARY_OFFSET, 0, BOUNDARY_OFFSET, HEIGHT)
]

STAIRS_AREA = pygame.Rect(1200, 140, 200, 150)  
STAIRS_DOWN_AREA = pygame.Rect(200, 200, 150, 150)  

LEVEL1_WALLS = [
    pygame.Rect(1750, 0, 100, 1000),
    pygame.Rect(50, 0, 100, 1000)
]

LEVEL2_WALLS = [
    pygame.Rect(1750, 0, 100, 1000),
    pygame.Rect(50, 0, 100, 1000)
]

current_goal = None
next_goal = None
goal_start_time = 0
goal_duration = 15  
next_goal_delay = 15
goal_shown = False
goal_completed = False

blood_drops = []
last_blood_time = 0

try:
    level1_music = "evilstepsup.mp3"
    level2_music = "evilstepsup.mp3"
    pygame.mixer.music.load(level1_music)
    pygame.mixer.music.set_volume(0.33)
    has_music = True
except:
    has_music = False

try:
    goal_sound = pygame.mixer.Sound("sounds/creepy_whisper.wav")
    stairs_sound = pygame.mixer.Sound("skrip.mp3")
    death_sound = pygame.mixer.Sound("sounds/death_scream.wav") if pygame.mixer else None
    victory_sound = pygame.mixer.Sound("sounds/victory.wav") if pygame.mixer else None
    has_sounds = True
except:
    has_sounds = False

try:
    background_clip = VideoFileClip("фонправ.mp4").resize((WIDTH, HEIGHT))
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as audio_temp:
        background_audio_path = audio_temp.name
        background_clip.audio.write_audiofile(background_audio_path, logger=None)
    has_background = True
except:
    has_background = False

background_running = False
background_thread = None
current_background_frame = None

class Character:
    def __init__(self, x, y, image_path, speed=5, is_enemy=False):
        try:
            self.image = pygame.image.load(image_path).convert_alpha()
            self.image = pygame.transform.scale(self.image, (100, 100))
        except:
            self.image = pygame.Surface((100, 100), pygame.SRCALPHA)
            color = RED if not is_enemy else (0, 0, 255)
            pygame.draw.rect(self.image, color, (0, 0, 100, 100))
        
        self.rect = self.image.get_rect(center=(x, y))
        self.base_speed = speed
        self.speed = speed
        self.direction = [0, 0]
        self.is_enemy = is_enemy
        self.crazy_mode = False

    def update_speed(self, multiplier):
        self.speed = self.base_speed * multiplier
        if self.crazy_mode:
            self.speed *= 2

    def check_collision(self, new_rect):
        for boundary in BOUNDARIES:
            if new_rect.colliderect(boundary):
                return True
        
        walls = LEVEL1_WALLS if current_level == 1 else LEVEL2_WALLS
        for wall in walls:
            if new_rect.colliderect(wall):
                return True
        return False

    def update(self):
        if self.is_enemy and not is_hiding:
            if random.random() < 0.02 or self.crazy_mode:
                dx = hero.rect.x - self.rect.x
                dy = hero.rect.y - self.rect.y
                dist = max(1, (dx**2 + dy**2)**0.5)
                self.direction = [dx/dist, dy/dist]
        
        new_x = self.rect.x + self.direction[0] * self.speed
        new_y = self.rect.y + self.direction[1] * self.speed

        new_x = max(BOUNDARY_OFFSET, min(WIDTH - BOUNDARY_OFFSET - self.rect.width, new_x))
        new_y = max(BOUNDARY_OFFSET, min(HEIGHT - BOUNDARY_OFFSET - self.rect.height, new_y))

        temp_rect = self.rect.copy()
        temp_rect.x = new_x
        temp_rect.y = new_y
        
        if self.check_collision(temp_rect):
            return

        self.rect.x = new_x
        self.rect.y = new_y

    def draw(self, surface):
        surface.blit(self.image, self.rect)

try:
    level1_bg = pygame.image.load("лок1.png")
    level1_bg = pygame.transform.scale(level1_bg, (WIDTH, HEIGHT))
    level2_bg = pygame.image.load("лок2.png")
    level2_bg = pygame.transform.scale(level2_bg, (WIDTH, HEIGHT))
    has_background_images = True
except:
    level1_bg = pygame.Surface((WIDTH, HEIGHT))
    level1_bg.fill((50, 50, 50))
    level2_bg = pygame.Surface((WIDTH, HEIGHT))
    level2_bg.fill((70, 70, 90))
    has_background_images = False

try:
    hero = Character(WIDTH // 2, HEIGHT // 2, "герой.gif")
    enemy1 = Character(300, 300, "плевакин.gif", is_enemy=True)
    enemy2 = Character(1500, 700, "систр.gif", is_enemy=True)
    has_characters = True
except:
    hero = Character(WIDTH // 2, HEIGHT // 2, "")
    enemy1 = Character(300, 300, "", is_enemy=True)
    enemy2 = Character(1500, 700, "", is_enemy=True)
    has_characters = False

def update_blood():
    global last_blood_time
    now = time.time()
    if now - last_blood_time > 0.5:
        blood_drops.append({
            'x': random.randint(40, 200),
            'y': 80,
            'speed': random.uniform(1.0, 3.0),
            'size': random.randint(2, 5)
        })
        last_blood_time = now
    
    for drop in blood_drops[:]:
        drop['y'] += drop['speed']
        if drop['y'] > 180:
            blood_drops.remove(drop)

def draw_blood():
    for drop in blood_drops:
        pygame.draw.circle(screen, BLOOD_RED, (int(drop['x']), int(drop['y'])), drop['size'])

def draw_menu(options, active_index):
    for i, text in enumerate(options):
        color = WHITE if i == active_index else GRAY
        rendered = menu_font.render(text, True, color)
        rect = rendered.get_rect(center=(WIDTH // 2, 300 + i * 100))
        screen.blit(rendered, rect)

def draw_settings():
    screen.fill(BLACK)
    title = font.render(texts[language]["settings"], True, WHITE)
    back = font.render(texts[language]["back"], True, GRAY)
    lang = font.render(texts[language]["choose_lang"], True, GRAY)

    screen.blit(title, title.get_rect(center=(WIDTH // 2, 250)))
    screen.blit(lang, lang.get_rect(center=(WIDTH // 2, 380)))
    screen.blit(back, back.get_rect(center=(WIDTH // 2, 470)))

def draw_intro():
    screen.fill(BLACK)
    title = font.render("Проклятий Дом", True, WHITE)
    disclaimer = font.render("УВАГА: У грі присутні скримери!", True, RED)
    prompt = font.render("Натисніть будь-яку клавішу...", True, GRAY)
    screen.blit(title, title.get_rect(center=(WIDTH // 2, 300)))
    screen.blit(disclaimer, disclaimer.get_rect(center=(WIDTH // 2, 420)))
    screen.blit(prompt, prompt.get_rect(center=(WIDTH // 2, 550)))

def draw_game_over():
    screen.fill(BLACK)
    if game_win:
        title = horror_font.render(texts[language]["game_win"][0], True, (0, 255, 0))
    elif victory_achieved:
        title = horror_font.render(texts[language]["victory_message"], True, (0, 255, 0))
    else:
        title = horror_font.render(texts[language]["game_over"][0], True, RED)
    screen.blit(title, title.get_rect(center=(WIDTH // 2, 250)))
    
    options = texts[language]["game_win"][1:] if (game_win or victory_achieved) else texts[language]["game_over"][1:]
    for i, option in enumerate(options):
        color = WHITE if i == game_over_selection else GRAY
        text = menu_font.render(option, True, color)
        screen.blit(text, text.get_rect(center=(WIDTH // 2, 400 + i * 100)))

def spawn_keys():
    global KEYS
    KEYS = []
    for _ in range(total_keys):
        KEYS.append({
            'rect': pygame.Rect(
                random.randint(BOUNDARY_OFFSET, WIDTH - BOUNDARY_OFFSET - 50),
                random.randint(BOUNDARY_OFFSET, HEIGHT - BOUNDARY_OFFSET - 50),
                30, 30
            ),
            'collected': False
        })

def draw_keys():
    for key in KEYS:
        if not key['collected']:
            pygame.draw.rect(screen, (255, 215, 0), key['rect'])

def check_key_collision():
    global keys_collected
    for key in KEYS:
        if not key['collected'] and hero.rect.colliderect(key['rect']):
            key['collected'] = True
            keys_collected += 1
            if keys_collected == total_keys:
                return True
    return False

def check_safe_zone():
    global is_hiding
    is_hiding = hero.rect.colliderect(SAFE_ZONE) and 180 <= game_time < 240

def check_exit():
    if exit_available and hero.rect.colliderect(EXIT_ZONE):
        return True
    return False

def check_victory():
    global victory_achieved
    if victory_available and hero.rect.colliderect(VICTORY_ZONE):
        victory_achieved = True
        if has_sounds and victory_sound:
            try:
                victory_sound.play()
            except:
                pass
        return True
    return False

def update_game_time():
    global game_time, current_goal, goal_start_time, monster_speed_multiplier, exit_available, victory_available
    
    game_time += 1/60  
    
    hours = (12 + game_time // 60) % 12
    if hours == 0: hours = 12
    minutes = int(game_time % 60)
    am_pm = "AM" if (12 + game_time // 60) % 24 < 12 else "PM"
    
    current_hour = (12 + game_time // 60) % 12
    if current_hour == 0: current_hour = 12
    
    if 0 <= game_time < 20:
        if current_goal != "look_around":
            current_goal = "look_around"
            goal_start_time = time.time()
            monster_speed_multiplier = 1
    
    elif 25 <= game_time < 60:
        if current_goal != "run_away":
            current_goal = "run_away"
            goal_start_time = time.time()
            monster_speed_multiplier = 1
    
    elif 60 <= game_time < 90:
        if current_goal != "find_keys":
            current_goal = "find_keys"
            goal_start_time = time.time()
            spawn_keys()
    
    elif 90 <= game_time < 120:
        if current_goal != "find_stairs":
            current_goal = "find_stairs"
            goal_start_time = time.time()
    
    elif 120 <= game_time < 180:
        if current_goal != "explore":
            current_goal = "explore"
            goal_start_time = time.time()
    
    elif 180 <= game_time < 240:
        if current_goal != "hide":
            current_goal = "hide"
            goal_start_time = time.time()
            monster_speed_multiplier = 1
    
    elif 240 <= game_time < 300:
        if current_goal != "find_sister":
            current_goal = "find_sister"
            goal_start_time = time.time()
            victory_available = True
    
    elif 300 <= game_time < 360:
        if current_goal != "escape":
            current_goal = "escape"
            goal_start_time = time.time()
            exit_available = True
    
    enemy1.update_speed(monster_speed_multiplier)
    enemy2.update_speed(monster_speed_multiplier)
    
    return f"{int(hours):02d}:{int(minutes):02d} {am_pm}"

def draw_timer(time_text):
    timer_surface = pygame.Surface((200, 50), pygame.SRCALPHA)
    timer_surface.fill((0, 0, 0, 128))
    timer_text = font.render(time_text, True, WHITE)
    timer_surface.blit(timer_text, (10, 10))
    screen.blit(timer_surface, (WIDTH - 210, 10))

def draw_goal():
    global goal_completed, current_goal
    
    current_time = time.time()
    elapsed = current_time - goal_start_time
    
    if current_goal == "look_around":
        text = texts[language]["goals"]["look_around"]
        draw_goal_text(text, current_time)
    
    elif current_goal == "run_away":
        text = texts[language]["goals"]["run_away"]
        draw_goal_text(text, current_time)
    
    elif current_goal == "find_keys":
        text = texts[language]["goals"]["find_keys"].format(keys_collected, total_keys)
        draw_goal_text(text, current_time)
        
        if game_time >= 89 and game_time < 90:
            enemy1.crazy_mode = False
            enemy2.crazy_mode = False
    
    elif current_goal == "find_stairs":
        if current_level == 1:
            text = texts[language]["goals"]["find_stairs"]
        else:
            text = texts[language]["goals"]["explore"]
        draw_goal_text(text, current_time)
    
    elif current_goal == "explore":
        text = texts[language]["goals"]["explore"]
        draw_goal_text(text, current_time)
    
    elif current_goal == "hide":
        if is_hiding:
            text = "Ты в безопасности!" if language == "ua" else "You're safe!"
        else:
            text = texts[language]["goals"]["hide"]
        draw_goal_text(text, current_time)
    
    elif current_goal == "find_sister":
        text = texts[language]["goals"]["find_sister"]
        draw_goal_text(text, current_time)
    
    elif current_goal == "escape":
        text = texts[language]["goals"]["escape"]
        draw_goal_text(text, current_time)

def draw_goal_text(text, current_time):
    shadow = font.render(text, True, (0, 0, 0))
    screen.blit(shadow, (252, 102))
    
    main = font.render(text, True, (255, 0, 0))
    screen.blit(main, (250, 100))
    
    if int(current_time * 0.4) % 2 == 0:
        for i in range(-1, 2, 1):
            for j in range(-1, 2, 1):
                glow = font.render(text, True, (150, 0, 0))
                screen.blit(glow, (250 + i, 100 + j))

def draw_stairs_message():
    if current_level == 1 and hero.rect.colliderect(STAIRS_AREA) and keys_collected == total_keys:
        if random.random() > 0.1:
            msg = texts[language]["stairs_message"]
            shadow = horror_font.render(msg, True, (40, 0, 0))
            screen.blit(shadow, (WIDTH//2 - shadow.get_width()//2 + 2, 102))
            
            color = (CREEPY_WHITE if random.random() > 0.3 else (200, 200, 200))
            text = horror_font.render(msg, True, color)
            screen.blit(text, (WIDTH//2 - text.get_width()//2, 100))
    elif current_level == 2 and hero.rect.colliderect(STAIRS_DOWN_AREA):
        if random.random() > 0.1:
            msg = texts[language]["stairs_down_message"]
            shadow = horror_font.render(msg, True, (40, 0, 0))
            screen.blit(shadow, (WIDTH//2 - shadow.get_width()//2 + 2, 102))
            
            color = (CREEPY_WHITE if random.random() > 0.3 else (200, 200, 200))
            text = horror_font.render(msg, True, color)
            screen.blit(text, (WIDTH//2 - text.get_width()//2, 100))

def change_level(new_level):
    global current_level, hero, enemy1, enemy2
    
    current_level = new_level
    if current_level == 1:
        hero.rect.center = (WIDTH // 2, HEIGHT // 2)
        enemy1.rect.center = (300, 300)
        enemy2.rect.center = (1500, 700)
        if has_music and not pygame.mixer.music.get_busy():
            pygame.mixer.music.load(level1_music)
            pygame.mixer.music.play(-1)
    else:
        hero.rect.center = (400, 400)
        enemy1.rect.center = (1200, 500)
        enemy2.rect.center = (1200, 300)
        if has_music and not pygame.mixer.music.get_busy():
            pygame.mixer.music.load(level2_music)
            pygame.mixer.music.play(-1)

def play_video_in_pygame(video_path):
    try:
        clip = VideoFileClip(video_path).resize((WIDTH, HEIGHT))
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as audio_temp:
            temp_audio_path = audio_temp.name
            clip.audio.write_audiofile(temp_audio_path, logger=None)

        pygame.mixer.music.load(temp_audio_path)
        pygame.mixer.music.play()

        clock = pygame.time.Clock()
        start_time = pygame.time.get_ticks()
        duration = clip.duration

        while (pygame.time.get_ticks() - start_time) / 1000.0 < duration:
            t = (pygame.time.get_ticks() - start_time) / 1000.0
            frame = clip.get_frame(t)
            frame = np.rot90(frame, 3)
            frame = pygame.surfarray.make_surface(frame)
            frame = pygame.transform.scale(frame, (WIDTH, HEIGHT))

            screen.blit(frame, (0, 0))
            pygame.display.flip()
            clock.tick(30)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.mixer.music.stop()
                    return

        pygame.mixer.music.stop()
        try:
            os.remove(temp_audio_path)
        except:
            print("Помилка з файлом")
    except Exception as e:
        print(f"Помилка завантаження відео: {e}")

def background_video_loop():
    global background_running, current_background_frame
    
    if has_background and background_audio_path:
        try:
            pygame.mixer.music.load(background_audio_path)
            pygame.mixer.music.play(-1)
        except Exception as e:
            print(f"Ошибка воспроизведения фоновой музыки: {e}")

    clock = pygame.time.Clock()
    start_time = pygame.time.get_ticks()

    while background_running:
        try:
            if has_background and background_clip:
                t = ((pygame.time.get_ticks() - start_time) / 1000.0) % background_clip.duration
                frame = background_clip.get_frame(t)
                frame = np.rot90(frame, 3)
                frame = pygame.surfarray.make_surface(frame)
                frame = pygame.transform.scale(frame, (WIDTH, HEIGHT))
                current_background_frame = frame
            else:
                current_background_frame = None
        except Exception as e:
            print(f"Ошибка получения кадра: {e}")
            current_background_frame = None

        clock.tick(30)

def start_game_window():
    global game_state, current_goal, goal_start_time, goal_shown, goal_completed
    global current_level, game_over, game_over_selection, game_time, game_win, victory_achieved
    global keys_collected, monster_speed_multiplier, exit_available, victory_available

    current_goal = "look_around"
    goal_start_time = time.time()
    goal_shown = True
    goal_completed = False
    current_level = 1
    game_over = False
    game_win = False
    victory_achieved = False
    game_time = 0
    keys_collected = 0
    monster_speed_multiplier = 1
    exit_available = False
    victory_available = False
    enemy1.crazy_mode = False
    enemy2.crazy_mode = False
    
    change_level(1)

    clock = pygame.time.Clock()
    running = True

    while running:
        time_text = update_game_time()
        
        if game_time >= GAME_DURATION:
            game_over = True
        
        update_blood()

        keys = pygame.key.get_pressed()
        hero.direction = [0, 0]

        if not game_over and not victory_achieved:
            if keys[pygame.K_w]: hero.direction[1] = -1
            if keys[pygame.K_s]: hero.direction[1] = 1
            if keys[pygame.K_a]: hero.direction[0] = -1
            if keys[pygame.K_d]: hero.direction[0] = 1

            if current_level == 1 and hero.rect.colliderect(STAIRS_AREA) and keys[pygame.K_e] and keys_collected == total_keys:
                if has_sounds:
                    try:
                        stairs_sound.play()
                    except:
                        pass
                change_level(2)
            
            elif current_level == 2 and hero.rect.colliderect(STAIRS_DOWN_AREA) and keys[pygame.K_e]:
                if has_sounds:
                    try:
                        stairs_sound.play()
                    except:
                        pass
                change_level(1)
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                game_state = "main_menu"
                background_running = True
                if background_thread is None or not background_thread.is_alive():
                    background_thread = threading.Thread(target=background_video_loop)
                    background_thread.daemon = True
                    background_thread.start()
            
            if (game_over or victory_achieved) and event.type == pygame.KEYDOWN:
                if event.key == pygame.K_DOWN:
                    game_over_selection = (game_over_selection + 1) % 2
                elif event.key == pygame.K_UP:
                    game_over_selection = (game_over_selection - 1) % 2
                elif event.key == pygame.K_RETURN:
                    if game_over_selection == 0:  
                        current_goal = "look_around"
                        goal_start_time = time.time()
                        goal_shown = True
                        goal_completed = False
                        current_level = 1
                        game_over = False
                        game_win = False
                        victory_achieved = False
                        game_time = 0
                        keys_collected = 0
                        monster_speed_multiplier = 1
                        exit_available = False
                        victory_available = False
                        enemy1.crazy_mode = False
                        enemy2.crazy_mode = False
                        change_level(1)
                    else:  
                        running = False
                        game_state = "main_menu"
                        background_running = True
                        if background_thread is None or not background_thread.is_alive():
                            background_thread = threading.Thread(target=background_video_loop)
                            background_thread.daemon = True
                            background_thread.start()

        if not game_over and not victory_achieved:
            if current_goal == "find_keys":
                check_key_collision()
            
            check_safe_zone()
            
            if check_exit():
                game_over = True
                game_win = True
            
            if check_victory():
                game_over = True
            
            hero.update()

            if random.random() < 0.02:
                enemy1.direction = [random.choice([-1, 0, 1]), random.choice([-1, 0, 1])]
                enemy2.direction = [random.choice([-1, 0, 1]), random.choice([-1, 0, 1])]

            enemy1.update()
            enemy2.update()

            if hero.rect.colliderect(enemy1.rect) or hero.rect.colliderect(enemy2.rect):
                if has_sounds and death_sound:
                    try:
                        death_sound.play()
                    except:
                        pass
                game_over = True

        if current_level == 1:
            screen.blit(level1_bg, (0, 0))
        else:
            screen.blit(level2_bg, (0, 0))

        walls = LEVEL1_WALLS if current_level == 1 else LEVEL2_WALLS
        for wall in walls:
            pygame.draw.rect(screen, (255, 0, 0), wall, 2)

        if current_goal == "find_keys":
            draw_keys()
        
        if exit_available:
            pygame.draw.rect(screen, (0, 255, 0), EXIT_ZONE, 2)
        
        if victory_available:
            pygame.draw.rect(screen, (0, 255, 255), VICTORY_ZONE, 2)
        
        if 180 <= game_time < 240:
            pygame.draw.rect(screen, (0, 0, 255), SAFE_ZONE, 2)

        hero.draw(screen)
        enemy1.draw(screen)
        enemy2.draw(screen)
        
        if not game_over and not victory_achieved:
            draw_goal()
            draw_stairs_message()
        else:
            draw_game_over()
            
        draw_blood()
        draw_timer(time_text)

        pygame.display.flip()
        clock.tick(60)

clock = pygame.time.Clock()
while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            background_running = False
            if background_thread is not None and background_thread.is_alive():
                background_thread.join(timeout=1.0)
            pygame.quit()
            sys.exit()

        if game_state == "intro":
            if event.type == pygame.KEYDOWN:
                game_state = "main_menu"
                background_running = True
                if background_thread is None or not background_thread.is_alive():
                    background_thread = threading.Thread(target=background_video_loop)
                    background_thread.daemon = True
                    background_thread.start()

        elif event.type == pygame.KEYDOWN:
            if game_state == "main_menu":
                if event.key == pygame.K_DOWN:
                    selection_index = (selection_index + 1) % 3
                elif event.key == pygame.K_UP:
                    selection_index = (selection_index - 1) % 3
                elif event.key == pygame.K_RETURN:
                    if selection_index == 0:
                        background_running = False
                        pygame.mixer.music.stop()
                        if language == "ua":
                            play_video_in_pygame("укркнига.mp4")
                        else:
                            play_video_in_pygame("англкнига1.mp4")
                        start_game_window()
                        background_running = True
                        if background_thread is None or not background_thread.is_alive():
                            background_thread = threading.Thread(target=background_video_loop)
                            background_thread.daemon = True
                            background_thread.start()
                    elif selection_index == 1:
                        game_state = "settings"
                    elif selection_index == 2:
                        background_running = False
                        if background_thread is not None and background_thread.is_alive():
                            background_thread.join(timeout=1.0)
                        pygame.quit()
                        sys.exit()
            elif game_state == "settings":
                if event.key == pygame.K_b:
                    game_state = "main_menu"
                elif event.key == pygame.K_u:
                    language = "ua"
                elif event.key == pygame.K_e:
                    language = "en"

    if game_state == "intro":
        draw_intro()
    elif game_state == "settings":
        draw_settings()
    elif game_state == "main_menu":
        if current_background_frame is not None:
            screen.blit(current_background_frame, (0, 0))
        else:
            screen.fill(BLACK)
        draw_menu(texts[language]["menu"], selection_index)

    pygame.display.flip()
    clock.tick(30)