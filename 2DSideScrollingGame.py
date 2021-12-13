# Import the pygame module
import os
import sys

import pygame

# Import random for random numbers
import random

# Import pygame.locals for easier access to key coordinates
# Updated to conform to flake8 and black standards
# from pygame.locals import *
from pygame.locals import (
    RLEACCEL,
    K_UP,
    K_DOWN,
    K_LEFT,
    K_RIGHT,
    K_ESCAPE,
    KEYDOWN,
    QUIT,
    K_SPACE
)

# Define constants for the screen width and height
SCREEN_WIDTH = 1920
SCREEN_HEIGHT = 1080


# We use this gradient func to display a gradient for the end screen. You can tune the color to have the grad you want
# We used a rect with a gradient instead of an image because gradients and inbuilt colour look crisp for any screen
# You can certainly use a picture instead and blit it as a bg however I wasn't able to find the one i liked
def fill_gradient(surface, color, gradient, rect=None, vertical=True, forward=True):
    """fill a surface with a gradient pattern
    Parameters:
    color -> starting color
    gradient -> final color
    rect -> area to fill; default is surface'enemies_hit_our_bullet_event rect
    vertical -> True=vertical; False=horizontal
    forward -> True=forward; False=reverse

    Pygame recipe: http://www.pygame.org/wiki/GradientCode
    """
    if rect is None: rect = surface.get_rect()
    x1, x2 = rect.left, rect.right
    y1, y2 = rect.top, rect.bottom
    if vertical:
        h = y2 - y1
    else:
        h = x2 - x1
    if forward:
        a, b = color, gradient
    else:
        b, a = color, gradient
    rate = (
        float(b[0] - a[0]) / h,
        float(b[1] - a[1]) / h,
        float(b[2] - a[2]) / h
    )
    fn_line = pygame.draw.line
    if vertical:
        for line in range(y1, y2):
            color = (
                min(max(a[0] + (rate[0] * (line - y1)), 0), 255),
                min(max(a[1] + (rate[1] * (line - y1)), 0), 255),
                min(max(a[2] + (rate[2] * (line - y1)), 0), 255)
            )
            fn_line(surface, color, (x1, line), (x2, line))
    else:
        for col in range(x1, x2):
            color = (
                min(max(a[0] + (rate[0] * (col - x1)), 0), 255),
                min(max(a[1] + (rate[1] * (col - x1)), 0), 255),
                min(max(a[2] + (rate[2] * (col - x1)), 0), 255)
            )
            fn_line(surface, color, (col, y1), (col, y2))


# --------------------HIGH-SCORE MANAGEMENT----------------------------------------------------------------------------
# HIGH_SCORE is the score retrieved from the database and PLAYER_SCORE is the score you currently have in the game
HIGH_SCORE = 0
PLAYER_SCORE = 0


# This function will check if the high score text file exist in the directory if not it will create one with a dummy value
def check_if_hs_file_exists():
    # if file exists on disk send it back else send dummy dat to prevent crash

    if os.path.exists('high_score.txt'):
        file = open("high_score.txt", "r+")
        high_score_on_disk = file.read()
        print("Current HighScore is: ", high_score_on_disk)
        global HIGH_SCORE
        HIGH_SCORE = int(high_score_on_disk)
    else:
        print('\nThere is so high-score file in the directory, creating one!')
        file = open("high_score.txt", "w+")
        dummy_highscore = '0'
        file.write(dummy_highscore)
        file.close()


check_if_hs_file_exists()  # when game launches we will see if we have the text file or not by calling this function

print('loaded high-score: ', HIGH_SCORE)


# This is called at the end of the game when we die to update our score in the database if it exceeds the current high score
def update_score(current_score, high_score):
    if current_score > high_score:
        file = open("high_score.txt", "w+")
        file.write(f'{current_score}')
        file.close()


# Define the Player object extending pygame.sprite.Sprite
# Instead of a surface, we use an image for a better looking sprite
class Player(pygame.sprite.Sprite):
    def __init__(self):
        super(Player, self).__init__()
        self.surf = pygame.image.load("FIGHTER - JET (3).png").convert()
        self.surf.set_colorkey((255, 255, 255), RLEACCEL)
        self.rect = self.surf.get_rect()

        self.rect.y = 200  # initial y pos. you can change it to whatever you'd like
        # self.rect.y = random.randint(100,SCREEN_HEIGHT) # initial y pos. you can change it to whatever you'd like, or you can make it random too!

        # health
        self.hp = 15  # Max hp

        # shooting & scoring
        self.score = 0  # Current score is 0 when the game boots

        self.scoreFont = pygame.font.SysFont(name='timesnewroman',
                                             size=35)  # make a font for displaying score, you can choose any youd like from uncommenting the below
        # print(pygame.font.get_fonts())

        self.can_shoot = True  # A var that decides if we can shoot

        # We want some cool down for which we are allowed to shoot again, if we dont have it, if you press space it'll emit a stream of bullets
        self.cooldown = 50  # Max cooldown(cd) we have to count to, to be able to shoot again, bigger val = longer wait time

        self.current_cooldown_count = 0  # Var used to see where we are in our count to the cd, if curr cd == cd we can shoot again

        self.player_bullets = pygame.sprite.Group()  # sprite group for player bullets

    # Move the sprite based on keypresses
    def update(self, pressed_keys):
        if pressed_keys[K_UP]:
            self.rect.move_ip(0, -5)
            pygame.mixer.Channel(3).play(move_up_sound)  # multi channel audio support
        if pressed_keys[K_DOWN]:
            self.rect.move_ip(0, 5)
            pygame.mixer.Channel(3).play(move_down_sound)  # multi channel audio support
        if pressed_keys[K_LEFT]:
            self.rect.move_ip(-5, 0)
        if pressed_keys[K_RIGHT]:
            self.rect.move_ip(5, 0)

        # Keep player on the screen
        if self.rect.left < 0:
            self.rect.left = 0
        elif self.rect.right > SCREEN_WIDTH:
            self.rect.right = SCREEN_WIDTH
        if self.rect.top <= 0:
            self.rect.top = 0
        elif self.rect.bottom >= SCREEN_HEIGHT:
            self.rect.bottom = SCREEN_HEIGHT

        if pressed_keys[K_SPACE] and self.can_shoot:  # if space is pressed and you can shoot, SHOOT!
            self.shoot()

        if self.can_shoot == False:  # if we cant shoot we reload our gun
            self.reload()

    def show_score_and_hp(self):
        # score
        score_surface = self.scoreFont.render(f'Score: {self.score}', True, 'black')  # HP text
        score_rect = score_surface.get_rect(topleft=(0, 0))
        screen.blit(score_surface, score_rect)

        # hp
        # Our hp is 15 [initially] and we have 15 pics, based on hp, we blit the image bar at the position of our hp
        # if our hp is 1, we load the health bar 1 pic. Its basically getting data (imgs) at an idx, data is our hp bars
        # idx is our hp
        hp_surface = self.scoreFont.render('HP', True, 'black')
        hp_rect = hp_surface.get_rect(topright=(SCREEN_WIDTH - 210, 10))
        screen.blit(hp_surface, hp_rect)
        screen.blit(hps[self.hp], dest=(SCREEN_WIDTH - 200, 0))  # hp meter

    def reload(self):
        # so here we start our count from 0...cd, when we reach cd we can shoot again, you can
        # print(self.current_cooldown_count) to see the counting process
        if self.current_cooldown_count <= self.cooldown:
            self.current_cooldown_count += 1
            self.can_shoot = False
        else:
            self.can_shoot = True
            self.current_cooldown_count = False
            pygame.mixer.Channel(1).play(reload_sound)  # multi channel audio support
            print('reloaded')

    def shoot(self):
        # fire the bullet, add the bullet to the sprite group, pos is rect.center because we want the bullet to come
        # from the plane speed = speed at which the player bullet travels max width = the max dist after which to
        # kill the bullet you will see the pygame.mixer.Channel(2).play(XYZ) line again shortly, we need to have
        # channels to play out from if we have several sounds playing at once we wont hear them as they'll cancel out
        # hence we need different channels to play audio from so they don't cancel, default is 7
        print('fired bullet')
        self.player_bullets.add(Player_Bullet(pos=self.rect.center, speed=20, max_width_bullet_can_go=SCREEN_WIDTH))
        self.can_shoot = False
        pygame.mixer.Channel(2).play(gun_shot)  # multi channel audio support


class Player_Bullet(pygame.sprite.Sprite):
    def __init__(self, pos, speed, max_width_bullet_can_go):
        super(Player_Bullet, self).__init__()
        self.image = pygame.image.load('missile.png')  # get the img
        self.image = pygame.transform.flip(self.image, True, False)  # flip the img as its the other way round raw
        self.key = self.image.get_at((0, 0))  # get the mask to remove from the img (the white stuff) at the top corner
        self.image.set_colorkey(self.key)  # set the key from above to remove, the key color in the img gets deleted
        self.rect = self.image.get_rect(center=pos)  # get the rect of the img for collision detection
        self.speed = speed  # set the bullet speed which you get from params
        self.width_constraint = max_width_bullet_can_go  # max width after which the bullet is deleted

    def destroy(self):
        if self.rect.x > self.width_constraint:
            self.kill()

    def update(self):
        self.rect.x += self.speed  # move the bullet along
        self.destroy()


# Define the enemy object extending pygame.sprite.Sprite
# Instead of a surface, we use an image for a better looking sprite
class Enemy(pygame.sprite.Sprite):
    def __init__(self):
        super(Enemy, self).__init__()
        self.surf = pygame.image.load("ENEMY-FIGHTER(2).png").convert()
        self.surf.set_colorkey((255, 255, 255), RLEACCEL)
        # The starting position is randomly generated, as is the speed
        self.rect = self.surf.get_rect(
            center=(
                random.randint(SCREEN_WIDTH + 20, SCREEN_WIDTH + 100),
                random.randint(0, SCREEN_HEIGHT),
            )
        )
        self.speed = random.randint(5, 10) # random speed to move along X

        self.frame = 0 # current frame of the explosion image

        self.animation_speed = 3  # speed to flip through images, larger is slower

        self.was_hit = False  # flag to use to check if we tagged this plane, we only want tagged ones to explode

        self.can_hurt = True # if we destroy it, we make it false so it cant hurt us

        self.damage = 1 # collision damage of the place, if we touch it we lose this much hp

        self.points = 1 # if we kill it we get points added to our score

        self.hp = 0 # plane'enemies_hit_our_bullet_event hp, bullets to kill is = (1+hp) as we check for tagging as well

        self.can_play_explosion_audio = True # if its tagged, we play audio once and set it to false to avoid looping

    # Move the enemy based on speed
    # Remove it when it passes the left edge of the screen
    def update(self):
        self.rect.move_ip(-self.speed, 0)

        if self.was_hit and self.hp <= 0:
            #  We divide by animation speed then use round bec we cant use floats as arr idx'enemies_hit_our_bullet_event .
            # we then set the image and then update the current image to the new image at the idx

            self.surf = cells[round(self.frame / self.animation_speed)]

            self.frame += 1

            if self.can_play_explosion_audio:
                pygame.mixer.Channel(6).play(explosion_sound)  # multi channel audio support
                self.can_play_explosion_audio = False

            if self.frame >= (len(cells) - 1) * self.animation_speed:  # remove sprite after animation is completed
                self.explode = False
                self.frame = 0
                self.kill()

        if self.rect.right < 0:
            self.kill()

# same class as player bullet, with a new image for visual separation, and width constraint, its 0 and not screen width
# as its the opposite, since its travelling and doing stuff oppositely in regards to player bullet
# e.g. this goes leftwards, player bullet goes rightwards hence the flipped constraint
class Enemy_Bullet(pygame.sprite.Sprite):
    def __init__(self, pos, speed):
        super(Enemy_Bullet, self).__init__()
        self.image = pygame.image.load('enemy missle.png')
        self.image = pygame.transform.flip(self.image, True, False)
        self.key = self.image.get_at((0, 0))
        self.image.set_colorkey(self.key)
        self.image = pygame.transform.smoothscale(self.image, (20, 10))
        self.rect = self.image.get_rect(center=pos)
        self.speed = speed
        self.width_constraint = 0

    def destroy(self):
        if self.rect.x < self.width_constraint:
            self.kill()

    def update(self):
        self.rect.x += self.speed
        self.destroy()


# Define the ship enemy object extending pygame.sprite.Sprite
# Instead of a surface, we use an image for a better looking sprite
class Ship(pygame.sprite.Sprite):
    def __init__(self):
        super(Ship, self).__init__()
        self.surf = pygame.image.load('ship.png') #  get image
        self.key = self.surf.get_at((0, 0))  # remove the bg colour
        self.surf.set_colorkey(self.key)   # remove the bg colou
        self.surf.convert_alpha()  # removed the bg colour

        # The starting position is randomly generated, as is the speed
        self.rect = self.surf.get_rect(
            center=(
                random.randint(SCREEN_WIDTH + 20, SCREEN_WIDTH + 100),
                random.randint(0, SCREEN_HEIGHT),
            )
        )
        self.speed = random.randint(5, 8)  # since we want it to be slow, we set it lesser than the max of enemy

        self.frame = 0  # same concept as enemy

        self.animation_speed = 3  # speed /  same concept as enemy

        self.was_hit = False  # same concept as enemy

        self.can_hurt = True  # same concept as enemy

        self.damage = 5  # collision damage

        self.bullet_damage = 2  # since our ships can shoot, this is their bullet damage as it hits us

        self.points = 5  # collision damage, its more since the craft is bigger, slower, spawns less

        self.hp = 1  # 2 shots to kill - remember shots to kill = 1+hp = 1+1 = 2

        self.bullets = pygame.sprite.Group()  # same concept as enemy

        # ----- firing -----
        # ----- concept -----

        #  can shoot is conceptually same as the player, its a flag which allows the ship to shoot
        #  we've made it dynamic by having it randomly choose if it can or cant shoot
        #  you can change the probabilty of making it shoot more or making it shoot less by increasing True or False
        # in the below collection. Right now since it can either be true or false its 50/50, if we had true, false,false
        # the probability of it shooting would've been 1/3 and so on . . .

        # ----- where to shoot -----

        # we want to have some way to make the ship shoot, we've achieved so by checking if its reached certain pos (2)
        # if it has, we fire. The positions are x coords, and we see if its crossed them, and its respective flag is T
        # we fire. Note you need to cross the pos, and have the flag=True(T) for it to be able to fire. Flag is F when
        # you fire and cross that pos. It fires twice, so we have 2 pos, randomly generate based on X (screen width)

        self.can_shoot = random.choice([True, False])

        self.shoot_again = random.choice([True, False])

        self.point_to_shoot_from1 = random.randint(1000, SCREEN_WIDTH)

        self.point_to_shoot_from2 = random.randint(300, 1100)

        self.can_play_explosion_audio = True  # same concept as enemy

    # Move the enemy based on speed
    # Remove it when it passes the left edge of the screen
    def update(self):
        self.rect.move_ip(-self.speed, 0)

        if self.was_hit and self.hp <= 0:

            self.surf = cells[round(self.frame / self.animation_speed)]  # explosion system same as enemy

            self.frame += 1

            if self.can_play_explosion_audio:
                pygame.mixer.Channel(6).play(explosion_sound)  # multi channel audio support
                self.can_play_explosion_audio = False

            if self.frame >= (len(cells) - 1) * self.animation_speed:
                self.explode = False
                self.frame = 0
                self.kill()

        if self.rect.x < self.point_to_shoot_from1 and self.can_shoot:
            self.can_shoot = False

            pygame.mixer.Channel(4).play(gun_shot)  # multi channel audio support

        if self.rect.x < self.point_to_shoot_from2 and self.shoot_again:
            obj = Enemy_Bullet(pos=self.rect.center, speed=-20)
            self.bullets.add(obj)
            self.shoot_again = False
            pygame.mixer.Channel(4).play(gun_shot)  # multi channel audio support

        if self.rect.right < 0:
            self.kill()


# Define the cloud object extending pygame.sprite.Sprite
# Use an image for a better looking sprite
class Cloud(pygame.sprite.Sprite):
    def __init__(self):
        super(Cloud, self).__init__()
        self.surf = pygame.image.load("cloud.png").convert()
        self.surf.set_colorkey((0, 0, 0), RLEACCEL)
        # The starting position is randomly generated
        self.rect = self.surf.get_rect(
            center=(
                random.randint(SCREEN_WIDTH + 20, SCREEN_WIDTH + 100),
                random.randint(0, SCREEN_HEIGHT),
            )
        )

    # Move the cloud based on a constant speed
    # Remove it when it passes the left edge of the screen
    def update(self):
        self.rect.move_ip(-5, 0)
        if self.rect.right < 0:
            self.kill()


# Setup for sounds, defaults are good
pygame.mixer.init()

# Initialize pygame
pygame.init()

# Setup the clock for a decent framerate
clock = pygame.time.Clock()

# Create the screen object
# The size is determined by the constant SCREEN_WIDTH and SCREEN_HEIGHT
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))

# Create custom events for adding a new enemy and cloud
ADDENEMY = pygame.USEREVENT + 1
pygame.time.set_timer(ADDENEMY, 250)
ADDCLOUD = pygame.USEREVENT + 2
pygame.time.set_timer(ADDCLOUD, 1000)
ADDSHIP = pygame.USEREVENT + 3
pygame.time.set_timer(ADDSHIP, 2000)

# Create our 'player'
player = Player()

# Create groups to hold enemy sprites, cloud sprites, and all sprites
# - enemies is used for collision detection and position updates
# - clouds is used for position updates
# - all_sprites isused for rendering
enemies = pygame.sprite.Group()
clouds = pygame.sprite.Group()
ships = pygame.sprite.Group()
all_sprites = pygame.sprite.Group()
all_sprites.add(player)

player_group = pygame.sprite.Group()  # custom sprite group for player, needed so we can check for collisions
player_group.add(player)

# Load and play our background music
# Sound source: http://ccmixter.org/files/Apoxode/59262
# License: https://creativecommons.org/licenses/by/3.0/
pygame.mixer.music.load("RetroPlatformer.mp3")
pygame.mixer.music.play(loops=-1)

# Load all our sound files
# Sound sources: Jon Fincher
move_up_sound = pygame.mixer.Sound("Rising_putter.ogg")
move_down_sound = pygame.mixer.Sound("Falling_putter.ogg")
collision_sound = pygame.mixer.Sound("Collision.ogg")

reload_sound = pygame.mixer.Sound('reload.wav')
gun_shot = pygame.mixer.Sound('shot.mp3')

explosion_sound = pygame.mixer.Sound('explosion.wav')
# Set the base volume for all sounds
move_up_sound.set_volume(0.5)
move_down_sound.set_volume(0.5)
collision_sound.set_volume(0.5)
reload_sound.set_volume(0.5)
gun_shot.set_volume(0.5)
explosion_sound.set_volume(0.5)

# ---------------------Image retrieval and transform-----------------------------------
# ---- explosion ----

sheet = pygame.image.load('Explosion.png').convert_alpha()  # 1152 x 96

cells = []  # container for explosions

for n in range(12):
    width, height = (96, 96)
    rect = pygame.Rect(n * width, 0, width, height)
    image = pygame.Surface(rect.size).convert()
    image.blit((sheet), (0, 0), rect)
    alpha = image.get_at((0, 0))
    image.set_colorkey(alpha)
    cells.append(image)  # add img to arr

# ---- hp ----

hps = []  # container for hps
for n in range(16):
    hp_img = pygame.image.load(f'Health bar/Health bar{n}.png').convert_alpha()
    hp_img = pygame.transform.smoothscale(hp_img, (hp_img.get_width() / 2, hp_img.get_height() / 2))  # has as big
    hps.append(hp_img)  # add img to arr

# Variable to keep our main loop running
running = True


# ------- END-SCREEN FONTS and Func -------
Current_Score_font = pygame.font.SysFont(name='timesnewroman', size=30)
hs_font = pygame.font.SysFont(name='timesnewroman', size=60)

#  End game screen loop
def show_end_screen():
    run = True
    while run:

        screen.fill((0, 0, 0))

        for event in pygame.event.get():
            # Did the user hit a key?
            if event.type == KEYDOWN:
                run = False
                pygame.quit()
                sys.exit()
            if event.type == pygame.QUIT:
                run = False
                pygame.quit()
                sys.exit()
        end_scren_bg = pygame.Rect(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT)
        pygame.draw.rect(screen, (0, 0, 0), end_scren_bg)
        fill_gradient(screen, (0, 0, 139), (216, 191, 216), end_scren_bg)

        # show high score from retrieved data, and current score

        HIGH_score_surface = hs_font.render(f'High Score: {HIGH_SCORE}', True, 'white')
        score_rect = HIGH_score_surface.get_rect()
        score_rect.center = (SCREEN_WIDTH / 2 + -50, SCREEN_HEIGHT / 2 - 300)
        screen.blit(HIGH_score_surface, score_rect)

        Current_Score_surface = hs_font.render(f'Score This Game: {PLAYER_SCORE}', True, 'white')
        score_rect_curr = Current_Score_surface.get_rect()
        score_rect_curr.center = (SCREEN_WIDTH / 2 + -50, SCREEN_HEIGHT / 2)
        screen.blit(Current_Score_surface, score_rect_curr)

        pygame.display.flip()
        clock.tick(1)


# Our main loop
while running:
    # Look at every event in the queue
    for event in pygame.event.get():
        # Did the user hit a key?
        if event.type == KEYDOWN:
            # Was it the Escape key? If so, stop the loop
            if event.key == K_ESCAPE:
                running = False

        # Did the user click the window close button? If so, stop the loop
        elif event.type == QUIT:
            running = False

        # Should we add a new enemy?
        elif event.type == ADDENEMY:
            # Create the new enemy, and add it to our sprite groups
            new_enemy = Enemy()
            enemies.add(new_enemy)
            all_sprites.add(new_enemy)

        # Should we add a new cloud?
        elif event.type == ADDCLOUD:
            # Create the new cloud, and add it to our sprite groups
            new_cloud = Cloud()
            clouds.add(new_cloud)
            all_sprites.add(new_cloud)

        # Should we add a new cloud?
        elif event.type == ADDSHIP:
            # Create the new ship, and add it to our sprite groups
            new_ship = Ship()
            enemies.add(new_ship)
            all_sprites.add(new_ship)

    # Get the set of keys pressed and check for user input
    pressed_keys = pygame.key.get_pressed()
    player.update(pressed_keys)

    # Update the position of our enemies and clouds
    enemies.update()
    clouds.update()
    ships.update()
    # Fill the screen with sky blue
    screen.fill((135, 206, 250))

    # Draw all our sprites
    for entity in all_sprites:
        screen.blit(entity.surf, entity.rect)

    # Check if bullet has collided with enemy

    # draw the bullet
    player.player_bullets.draw(screen)
    player.player_bullets.update()

    for i in enemies:
        if type(i) == Ship:

            ship_bullet_damage = i.bullet_damage  # grab the damage of ship bullet to use later

            i.bullets.draw(screen)  # draw ship bullets
            i.bullets.update()

            x = pygame.sprite.groupcollide(player_group, i.bullets, False, True)  # collision b/w us and ship bullets

            for _ in x:
                player.hp -= ship_bullet_damage  # subtract damage from hp and play audio
                pygame.mixer.Channel(7).play(collision_sound)

    player.show_score_and_hp()  # blit hp meter


    enemies_hit_our_bullet_event = pygame.sprite.groupcollide(enemies, player.player_bullets, False, True)
    for i in enemies_hit_our_bullet_event:
        if i.hp <= 0:  # if we reduced their hp AKA killed them give us their points and add it to our score
            player.score += i.points
            i.was_hit = True  # tag the enemy
            i.can_hurt = False  # if it hurts us once, it cant hurt us again
        else:
            i.hp -= 1  # we reduce the enemy's hp by 1


    # Check if any enemies have collided with the player

    we_hit_enemies_by_collision = pygame.sprite.groupcollide(enemies, player_group, False, False)
    for i in we_hit_enemies_by_collision:
        if not i.was_hit and player.hp <= 1:

            update_score(current_score=player.score, high_score=HIGH_SCORE)  # call the data manager func to check score
            # is score is > than High score we save this score

            PLAYER_SCORE = player.score

            player.kill()

            # Stop any moving sounds and play the collision sound
            move_up_sound.stop()
            move_down_sound.stop()
            collision_sound.play()

            # Stop the loop
            running = False


        elif i.can_hurt:

            i.can_hurt = False
            player.hp -= i.damage  # collision damage

    # Flip everything to the display
    pygame.display.flip()

    # Ensure we maintain a 30 frames per second rate
    clock.tick(60)

# At this point, we're done, so we can stop and quit the mixer
show_end_screen()

pygame.mixer.music.stop()
pygame.mixer.quit()
