import pygame
import numpy as np
import math
import sys
import random

pygame.init()

import entities
import effects
import waves
import game_data
import scores


actual_dims = (
    game_data.screen_dims[0] + game_data.hs_screen_width,
    game_data.screen_dims[1]
)

screen = pygame.display.set_mode(actual_dims)
game_data.screen = screen

clk = pygame.time.Clock()

pygame.time.set_timer(pygame.USEREVENT+1, 25)

while True:
    dt = clk.tick(60) / 1000

    if game_data.game_running:
        game_data.t += dt

        # Decrement respawn timer if necessary:
        if game_data.get_game_state() == 'respawn':
            game_data.respawn_timer -= dt

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            sys.exit()
        elif event.type == pygame.USEREVENT+1:
            if game_data.get_game_state() == 'gameplay':
                waves.update()
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                sys.exit()

            if game_data.get_game_state() == 'title' and event.key == pygame.K_SPACE:
                # Start a new game.
                entities.all_bullets.empty()
                entities.player.reset()
                waves.reset()
                game_data.reset()
            elif game_data.get_game_state() == 'hs-name-input':
                scores.name_input_screen.keypress(event)

    if game_data.get_game_state() != 'hs-name-input':
        pygame.key.set_repeat()

    # Clear the screen.
    screen.fill((0, 0, 0))

    effects.all_effects.update(dt)

    if game_data.get_game_state() == 'respawn' and entities.player.dead and game_data.respawn_timer < 2.5:
        entities.player.reset()

    # Normal game flow-- update bullets and check for invalid positions.
    entities.player.update(dt)
    entities.all_bullets.update(dt)
    entities.all_beams.update(dt)

    for sprite in entities.all_bullets.sprites():
        if (
            sprite.pos[0] < 0 or sprite.pos[0] > game_data.screen_dims[0]
            or sprite.pos[1] < 0 or sprite.pos[1] > game_data.screen_dims[1]
        ):
            # Bullet went out of bounds; remove it and increment score.
            sprite.kill()

            if game_data.get_game_state() == 'gameplay':
                game_data.change_score(1)

    # Blit bullets and the player below everything else.
    if hasattr(entities.player, 'rect') and not entities.player.dead:
        # Bit of a dirty hack-- only display player position if it's valid.

        if game_data.get_game_state() == 'respawn' and (pygame.time.get_ticks() % 1000 > 500):
            entities.player.set_color((255, 255, 255, 255))
        else:
            entities.player.set_color((0, 255, 0, 255))

        screen.blit(entities.player.image, entities.player.rect)

    entities.all_bullets.draw(screen)
    entities.all_beams.draw(screen)
    effects.all_effects.draw(screen)

    if game_data.get_game_state() == 'start-countdown':
        # Countdown to game start.
        countdown_display = game_data.prompt_font.render(
            "{:.3f}".format(3 - game_data.t), True, (255, 0, 0)
        )
        w, h = countdown_display.get_size()

        screen.blit(
            countdown_display,
            (400 - (w/2), 350 - (h/2))
        )
    elif game_data.get_game_state() == 'title':
        # Starting key prompt and title
        title_display = game_data.title_font.render(
            "CurtainFire", True, (0, 255, 0)
        )

        w, h = title_display.get_size()

        screen.blit(
            title_display,
            (400 - (w/2), 200 - (h/2))
        )

        if pygame.time.get_ticks() % 1000 > 500:
            prompt_display = game_data.prompt_font.render(
                "Press SPACE", True, (255, 255, 255)
            )

            w, h = prompt_display.get_size()

            screen.blit(
                prompt_display,
                (400 - (w/2), 400 - (h/2))
            )
    elif game_data.get_game_state() == 'hs-name-input':
        scores.name_input_screen.update(dt)
        screen.blit(scores.name_input_screen.screen, (0, 0))

    # Display interesting info at the bottom of the screen.
    score_display = game_data.display_font.render(
        "Wave: {:02n} Score: {:05n} Wave Size: {:04n}".format(
            game_data.current_wave_number, game_data.score, game_data.current_wave_size+1
        ), True, (255, 255, 255)
    )

    sw, sh = score_display.get_size()
    screen.blit(score_display, (400 - (sw/2), 800-sh))

    if waves.current_wave is not None:
        pattern_display = None

        if len(waves.wave_queue) >= 1:
            pattern_display = game_data.fps_font.render(
                "Pattern: {}    Next Pattern: {}".format(
                    waves.current_wave.name,
                    waves.wave_queue[-1].name
                ), True, (255, 255, 255)
            )
        else:
            pattern_display = game_data.fps_font.render(
                "Pattern: {}".format(
                    waves.current_wave.name
                ), True, (255, 255, 255)
            )

        pw, ph = pattern_display.get_size()
        screen.blit(pattern_display, (400 - (pw/2), 800-sh-ph))

    fps_display = game_data.fps_font.render(
        "{:02n}".format(clk.get_fps()), True, (255, 255, 255)
    )

    screen.blit(fps_display, (0, 0))

    if game_data.get_game_state() == 'gameplay':
        time_display = game_data.display_font.render(
            "Time: {:.3f}".format(game_data.t - 3), True, (255, 255, 255)
        )

        tw, th = time_display.get_size()
        screen.blit(time_display, (400-(tw/2), 0))

    hs_display = scores.render_high_scores()
    screen.blit(hs_display, (800, 0))

    if scores.is_high_score() and game_data.get_game_state() == 'gameplay' and len(scores.saved_scores) != 0:
        hs_display = effects.render_striped_text(
            "High Score", game_data.display_font,
            (255, 255, 255, 255), (255, 0, 0, 255), 2, 150
        )

        w, h = hs_display.get_size()
        screen.blit(
            hs_display, (800 + (game_data.hs_screen_width / 2) - (w / 2), 790 - h)
        )

    if game_data.game_running:
        # Render display segment title
        t = game_data.display_font.render(
            "Lives: ", True, (255, 255, 255)
        )

        w, h = t.get_size()
        screen.blit(t, (815, 740-h))

        # Render lives count in white normally, use red if last lift
        color = (255, 255, 255, 255)
        if game_data.lives == 0:
            color = (255, 0, 0, 255)

        # Blit lives count to screen.
        c = game_data.display_font.render(
            "{:01n}".format(game_data.lives), True, color
        )
        screen.blit(c, (815+h+65, 740-h))

    pygame.display.flip()

    if game_data.get_game_state() == 'gameplay':
        collision_check_list = pygame.sprite.spritecollide(entities.player, entities.all_bullets, False)
        bullet_collided = False

        for bullet in collision_check_list:
            if pygame.sprite.collide_mask(entities.player, bullet) is not None:
                bullet_collided = True
                break

        if bullet_collided:
            print("Time: {:.3f}\nScore: {}".format(game_data.t - 3, game_data.score))

            effects.ExplosionEffect(entities.player.pos, 0, .5, 1)
            entities.player.kill()

            game_data.lives -= 1
            game_data.respawn_timer = game_data.respawn_length

            if game_data.lives < 0:
                game_data.game_over()

                if scores.is_high_score():
                    scores.name_input_screen.reset()
                    game_data.active_subscreen = 'hs-name-input'
