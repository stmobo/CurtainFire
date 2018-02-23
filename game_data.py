import pygame

title_font = pygame.font.Font("aldo_the_apache/AldotheApache.ttf", 150)
display_font = pygame.font.Font("open_24_display/Open 24 Display St.ttf", 50)
prompt_font = pygame.font.Font("open_24_display/Open 24 Display St.ttf", 75)
fps_font = pygame.font.Font("open_24_display/Open 24 Display St.ttf", 25)
input_font = pygame.font.Font("linear_beam/Linebeam.ttf", 50)
high_score_font = pygame.font.Font("open_24_display/Open 24 Display St.ttf", 22)

screen_dims = (800, 800)
game_running = False
game_ending = False
t = 0
game_end_time = 0

current_wave_size = 0
current_wave_number = 0
score = 0

screen = None

active_subscreen = None

hs_screen_width = 350

lives = 3

respawn_length = 3
respawn_timer = 0

def reset():
    global t, score, current_wave_number, game_ending, game_running
    global game_end_time

    t = 0
    score = 0
    current_wave_number = 0
    game_running = True
    game_end_time = False
    game_ending = False

def game_over():
    global game_ending, game_end_time, t, game_running

    game_running = False
    game_ending = True
    game_end_time = t

def get_game_state():
    global game_running, t, respawn_timer, active_subscreen

    if active_subscreen is not None:
        return active_subscreen
    elif not game_running:
        return 'title'
    else:
        if t < 3:
            return 'start-countdown'
        elif respawn_timer > 0:
            return 'respawn'
        else:
            return 'gameplay'

def change_score(delta):
    global score
    score += delta
