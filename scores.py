import pygame
import numpy as np
import math
import sys
import csv
import time
import game_data
import effects

score_cutoff = 10
score_fields = [
    'name',
    'timestamp',
    'score',
    'time',
    'waves'
]

def read_scores(f='./scores.csv'):
    global score_cutoff
    try:
        with open(f, newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            return sorted(
                [{
                    'name': row['name'],
                    'timestamp': row['timestamp'],
                    'score': int(row['score']),
                    'time': float(row['time']),
                    'waves': int(row['waves'])
                } for row in reader],
                key=lambda v: v['score'],
                reverse=True
            )[:score_cutoff]
    except FileNotFoundError as e:
        print("Could not find scores file!")
        return []

saved_scores = read_scores()

def sort_scores():
    global saved_scores, score_cutoff
    saved_scores = sorted(
        saved_scores,
        key=lambda v: v['score'],
        reverse=True
    )[:score_cutoff]

def write_scores(score_list, f='./scores.csv'):
    with open(f, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, score_fields)

        writer.writeheader()
        writer.writerows(score_list)

def current_score_object(name):
    return {
        'name': name,
        'timestamp': time.ctime(),
        'score': game_data.score,
        'time': game_data.t,
        'waves': game_data.current_wave_number
    }

def is_high_score():
    global saved_scores
    if len(saved_scores) == 0:
        return True

    threshold = min([s['score'] for s in saved_scores])

    return game_data.score > threshold

def render_high_scores():
    global saved_scores

    surface = pygame.Surface(
        (game_data.hs_screen_width, game_data.screen_dims[1])
    )

    surface.fill(
        (255, 255, 255),
        pygame.Rect((0, 0), (5, game_data.screen_dims[1]))
    )

    line_spacing = int(2 * game_data.high_score_font.get_height())

    start_w = 15
    start_h = 25

    margin = 35

    disp = game_data.high_score_font.render(
        "High Scores", True, (255, 255, 255)
    )

    w, h = disp.get_size()
    surface.blit(disp, ((game_data.hs_screen_width / 2) - (w/2), start_h))

    if len(saved_scores) == 0:
        disp2 = game_data.high_score_font.render(
            "No Saved Scores!", True, (255, 255, 255)
        )
    else:
        disp2 = game_data.high_score_font.render(
            "Score - Time - Waves", True, (255, 255, 255)
        )

    w, h = disp2.get_size()
    surface.blit(
        disp2, (
            (game_data.hs_screen_width / 2) - (w/2),
            start_h + game_data.high_score_font.get_height()
        )
    )

    if len(saved_scores) > 0:
        current_h = start_h + game_data.high_score_font.get_height() + margin

        for i, s in enumerate(saved_scores):
            listing_1 = game_data.high_score_font.render(
                "{}. {}".format(
                    i+1, s['name'], s['score'], s['time'], s['waves']
                ), True, (255, 255, 255)
            )
            surface.blit(listing_1, (start_w, current_h))

            listing_2 = game_data.high_score_font.render(
                "{:05n} - {:.3f} - {:02n}".format(
                    s['score'], s['time'], s['waves']
                ), True, (255, 255, 255)
            )
            w2, h2 = listing_2.get_size()

            surface.blit(listing_2, (start_w, current_h + h2))

            current_h += line_spacing

    return surface


class NameInputScreen:
    current_name = ""
    t = 0

    def __init__(self):
        self.screen = pygame.surface.Surface(game_data.screen_dims, flags=pygame.SRCALPHA)

    def reset(self):
        pygame.key.set_repeat(500, 100)
        self.current_name = ""

    def keypress(self, ev):
        global saved_scores
        if ev.key == pygame.K_BACKSPACE:
            self.current_name = self.current_name[:-1]
        elif ev.key == pygame.K_RETURN:
            saved_scores.append(current_score_object(self.current_name))
            sort_scores()
            write_scores(saved_scores)
            game_data.active_subscreen = None
        elif ev.unicode is not None and ev.unicode != '':
            self.current_name += ev.unicode

    def update(self, dt):
        self.t += dt

        self.screen.fill((0, 0, 0, 0))

        hs_display = effects.render_striped_text(
            "High Score", game_data.prompt_font,
            (255, 255, 255, 255), (255, 0, 0, 255), 2, 150
        )

        w, h = hs_display.get_size()

        self.screen.blit(
            hs_display,
            (400 - (w/2), 200 - (h/2))
        )

        prompt_display = game_data.prompt_font.render(
            "Enter Name", True, (255, 255, 255)
        )

        w, h = prompt_display.get_size()
        self.screen.blit(
            prompt_display,
            (400 - (w/2), 300 - (h/2))
        )

        prompt2_display = game_data.display_font.render(
            "Press Enter When Ready", True, (255, 255, 255)
        )

        w2, h2 = prompt2_display.get_size()
        self.screen.blit(
            prompt2_display,
            (400 - (w2 / 2), 300 + (h2/2))
        )


        rendered_text = self.current_name
        offset = 0
        if pygame.time.get_ticks() % 1000 > 500:
            rendered_text = self.current_name + '|'
        else:
            offset = game_data.input_font.size('|')[0]

        name_display = game_data.input_font.render(
            rendered_text, True, (255, 255, 255)
        )

        w, h = name_display.get_size()

        self.screen.blit(
            name_display,
            (400 - ((w + offset) / 2), 500 - (h/2))
        )



name_input_screen = NameInputScreen()
