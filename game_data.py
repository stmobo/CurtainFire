screen_dims = (800, 800)
game_running = False
game_ending = False
t = 0
game_end_time = 0

current_wave_size = 0
current_wave_number = 0
score = 0

screen = None

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

def get_game_state():
    global game_running, t

    if not game_running:
        return 'title'
    else:
        if t < 3:
            return 'start-countdown'
        else:
            return 'gameplay'
