import pygame
import numpy as np
import math
import sys
import random
import entities
import waves

screen_dims = (800, 800)

pygame.init()

screen = pygame.display.set_mode(screen_dims)
clk = pygame.time.Clock()

pygame.time.set_timer(pygame.USEREVENT+1, 25)
game_running = False
t = 0

title_font = pygame.font.Font("aldo_the_apache/AldotheApache.ttf", 150)
display_font = pygame.font.Font("open_24_display/Open 24 Display St.ttf", 50)
prompt_font = pygame.font.Font("open_24_display/Open 24 Display St.ttf", 75)
fps_font = pygame.font.Font("open_24_display/Open 24 Display St.ttf", 25)

while True:
    dt = clk.tick(60) / 1000

    if game_running:
        t += dt

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            sys.exit()
        elif event.type == pygame.USEREVENT+1:
            if game_running and t > 3:
                waves.update()
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                sys.exit()

            if not game_running and event.key == pygame.K_SPACE:
                # Start a new game.
                entities.all_bullets.empty()
                entities.player.reset()
                waves.reset()

                game_running = True
                t = 0

    # Clear the screen.
    screen.fill((0, 0, 0))

    if game_running and t >= 3:
        # Normal game flow-- update bullets and check for invalid positions.
        entities.player.update(dt)
        entities.all_bullets.update(dt)

        for sprite in entities.all_bullets.sprites():
            if (
                sprite.pos[0] < 0 or sprite.pos[0] > screen_dims[0]
                or sprite.pos[1] < 0 or sprite.pos[1] > screen_dims[1]
            ):
                # Bullet went out of bounds; remove it and increment score.
                waves.score += 1
                sprite.kill()

    # Blit bullets and the player below everything else.
    if hasattr(entities.player, 'rect'):
        # Bit of a dirty hack-- only display player position if it's valid.
        screen.blit(entities.player.image, entities.player.rect)
    entities.all_bullets.draw(screen)

    if game_running and t < 3:
        # Countdown to game start.
        entities.player.update(dt)
        countdown_display = prompt_font.render(
            "{:.3f}".format(3 - t), True, (255, 0, 0)
        )
        w, h = countdown_display.get_size()

        screen.blit(
            countdown_display,
            (400 - (w/2), 350 - (h/2))
        )
    elif not game_running:
        # Starting key prompt and title
        title_display = title_font.render(
            "CurtainFire", True, (0, 255, 0)
        )

        w, h = title_display.get_size()

        screen.blit(
            title_display,
            (400 - (w/2), 200 - (h/2))
        )

        if pygame.time.get_ticks() % 1000 > 500:
            prompt_display = prompt_font.render(
                "Press SPACE", True, (255, 255, 255)
            )

            w, h = prompt_display.get_size()

            screen.blit(
                prompt_display,
                (400 - (w/2), 400 - (h/2))
            )

    # Display interesting info at the bottom of the screen.
    score_display = display_font.render(
        "Wave: {:02n} Score: {:05n} Wave Size: {:04n}".format(
            waves.current_wave_number, waves.score, waves.current_wave_size+1
        ), True, (255, 255, 255)
    )

    sw, sh = score_display.get_size()
    screen.blit(score_display, (400 - (sw/2), 800-sh))

    if waves.current_wave is not None:
        pattern_display = None

        if len(waves.wave_queue) >= 1:
            pattern_display = fps_font.render(
                "Pattern: {}    Next Pattern: {}".format(
                    waves.current_wave.name,
                    waves.wave_queue[-1].name
                ), True, (255, 255, 255)
            )
        else:
            pattern_display = fps_font.render(
                "Pattern: {}".format(
                    waves.current_wave.name
                ), True, (255, 255, 255)
            )

        pw, ph = pattern_display.get_size()
        screen.blit(pattern_display, (400 - (pw/2), 800-sh-ph))

    fps_display = fps_font.render(
        "{:02n}".format(clk.get_fps()), True, (255, 255, 255)
    )

    screen.blit(fps_display, (0, 0))

    if t > 3:
        time_display = display_font.render(
            "Time: {:.3f}".format(t - 3), True, (255, 255, 255)
        )

        tw, th = time_display.get_size()
        screen.blit(time_display, (400-(tw/2), 0))

    pygame.display.flip()

    if game_running:
        collision_check_list = pygame.sprite.spritecollide(entities.player, entities.all_bullets, False)
        bullet_collided = False

        for bullet in collision_check_list:
            if pygame.sprite.collide_mask(entities.player, bullet) is not None:
                bullet_collided = True
                break

        if bullet_collided:
            print("Time: {:.3f}\nScore: {}".format(t - 3, waves.score))

            game_running = False
