# Complete your game here
import pygame as pg
from pygame.sprite import Sprite, Group, \
spritecollideany, spritecollide, collide_rect_ratio
from random import choices, choice, randint, random, randrange
from time import sleep

'''README
* The objective is to collect as many coins on your way to the final blue door as you can.
* You get points for coins collected and distance traversed. 
* When crossing water, you should step on the planks. The robot feet (the bottom of the icon)
is the 'contact point'
* I intentionally made it 'easier' for the robot to make contact with (collect) coins
and harder to make concact with the monsters
* Avoid monsters
* Try to reach the final blue door
* Enjoy :)
'''

'''External constants and variables, not connected to any classes'''

board_width, board_height = 3500, 500
levels = 70 # the number of vertical strip for the robot to walk across
end_levels = 6 # ending strips of land with coins
screen_width = 720
scroll_speed = 1
fps = 60
horizontal_unit = board_width / levels
vertical_unit = int(board_height / 10)
start_level = 6 # the number of vertical strips corresponding to the initial robot position

# a counter of how many pixels were scrolled
pixels_scrolled = 0 

water_color = (195, 221, 249)
grass_color = (50,205,50)
plank_brown = (181, 101, 29)

# a helper function to move any Sprite object backwards
def move_backwards(s: Sprite):
    global pixels_scrolled
    # we move the Sprite backward only if the background is still scrolling
    if pixels_scrolled < board_width - screen_width:
        s.rect.x -= scroll_speed

'''Classes'''

class Robot(Sprite):
    def __init__(self):
        super().__init__()
        self.current_level= start_level
        self.image = pg.image.load("robot.png")
        self.width  =self.image.get_width()
        self.height = self.image.get_height()
        self.score = 0
        # the robot spawns with some grass strips behind
        self.rect = self.image.get_rect(topleft = (horizontal_unit*start_level, board_height/2))

    def move(self, dx=0, dy=0):
        '''Moves the robot according to the player's keyboard input'''
        self.rect.x +=dx
        self.rect.y +=dy
        if dx >0:
            self.current_level +=1 # the robot advances to the next strip of land / water
            self.score = max(self.score, self.current_level - start_level)
        elif dx < 0:
            self.current_level -=1 # the robot returns to the previous strip
        
    def draw(self, screen):
        '''Draws the robot on the screen'''
        screen.blit(self.image, self.rect)
        pg.display.flip()

class WoodenPlank(Sprite):
    '''A wooden plank which floats on water'''
    def __init__(self, *groups, level_number):
        super().__init__(*groups)
        self.image = pg.Surface((horizontal_unit-4, 3*vertical_unit))
        self.image.fill(plank_brown)
        self.width = self.image.get_width()
        self.height = self.image.get_height()
        self.speed = choices([-2, -1, 1, 2], weights=[0.1, 0.4, 0.4, 0.1])[0] # the plank either moves down or up
        # the level number corresponds to the plank position on the x axis
        self.rect = self.image.get_rect(topleft = (horizontal_unit*level_number + 2, 
                                                      randint(0, board_height - self.height)))
    def update(self):
        # the plank has to move with the background
        move_backwards(self)
        # the plank cannot flow over the screen frame
        if self.rect.y <= 0 and self.speed <0:
            self.speed *= -1
        elif self.rect.y + self.height >= board_height and self.speed >0:
            self.speed *= -1
        
        # moving the plank vertically
        self.rect.y += self.speed

class Monster(Sprite):
    def __init__(self, *groups, x, y):
        super().__init__(*groups)
        self.image = pg.image.load("monster.png")
        self.rect = self.image.get_rect(topleft = (x,y))

    def update(self): move_backwards(self)

class Coin(Sprite):
    def __init__(self, *groups, x,y):
        super().__init__(*groups)
        self.image = pg.image.load("coin.png")
        self.rect = self.image.get_rect(topleft = (x,y))

    # the coin has to move backwards to remain stationary
    def update(self): move_backwards(self)   

class Door(Sprite):
    '''Door at the final level'''
    def __init__(self, *groups, x,y):
        super().__init__(*groups)  
        self.image = pg.image.load("door.png")
        self.rect = self.image.get_rect(center = (x,y)) 

    def update(self): move_backwards(self)  


class Game:
    '''The class representing the game'''
    def __init__(self):
        pg.init()
        pg.display.set_caption("Robot Runner")
        self.new_game()
        self.main_loop()       

    def new_game(self):
        '''Starts a new game'''
        # represents the width in px of the currently displayed window
        self.screen_width = screen_width 
        # the entire (moving) game board has this width
        self.board_width = board_width 
        # screen height is the same as board height as the board moves horizontally
        self.board_height = board_height 
        # randomly choosing whether each vertical strip is grass or water
        self.board_levels = ["ground"]*(start_level+1)+ choices(["ground", "water"], 
                    weights = [0.6, 0.4], k=levels-start_level-7) + ["ground"]*end_levels
        
        self.robot = Robot()
        # creating groups which hold information about game objects (needed for collisions)
        self.planks = Group( ) 
        self.monsters = Group()
        self.coins = Group()
        self.door = Group() # this holds only one object, not really needed but I find it convenient for collision detection

        # creating the entire board
        self.board_surface = self.create_board_surface()
        
        # the screen - only a portion of the board
        self.screen = pg.display.set_mode((screen_width, board_height))

    def create_board_surface(self):
        '''Creates the entire board'''
        board_surface = pg.Surface((self.board_width, self.board_height))
        # level corresponds to a single vertical strip of either grass or water
        for i, level in enumerate(self.board_levels):
            color = grass_color if level == "ground" else water_color 
            # fill a chunk of the board with green or blue
            board_surface.fill(color, pg.Rect((i*horizontal_unit, 0), (horizontal_unit, self.board_height)))
            if level == "water":
                # for each water strip, we create a wooden plank
                # the plank object is automatically added to the planks group upon creation
                WoodenPlank(self.planks, level_number=i)

            else:
                # final levels with coins in a line
                if i >= levels - end_levels and i != levels -1:
                    Coin(self.coins, x=i*horizontal_unit, y = board_height//2)
                
                # normal levels
                elif i > start_level and i != levels -1:
                    monster_y = -1
                    # for grass strips, we sometimes generate a stationary monster
                    if random() < 0.2:
                        monster_y = randrange(0, board_height, vertical_unit)
                        # the monster is automatically added to the group
                        Monster(self.monsters, x=i*horizontal_unit, y=monster_y)
                    
                    # we also sometimes generate coins
                    if random() < 0.5:
                        # the coins cannot overlap with monsters
                        coin_y = choice([y for y in range(0, board_height, vertical_unit) if y != monster_y])
                        Coin(self.coins, x=i*horizontal_unit, y=coin_y)
        
        # adding the final door
        Door(self.door, x= board_width - horizontal_unit/2, y= board_height/2)

        return board_surface
    
    def check_robot_position(self):
        '''Verifies the robot position'''
        robot_x = self.robot.rect.x
        robot_y = self.robot.rect.y

        # is the robot within the current screen frame?
        if robot_x + self.robot.width < 0 or robot_x + 0.5*self.robot.width > screen_width  \
            or robot_y + self.robot.height <= 0 or robot_y + 0.5*self.robot.height > board_height:
            print("Beyond the frame")
            self.blit_game_over()
            exit()
        
        # is the robot on a water strip?
        elif self.board_levels[self.robot.current_level] == "water":
            # is the robot standing on a plank? 
            current_plank = spritecollideany(
                self.robot, 
                self.planks, 
                # we check whether the **point** where the robot is standing is on the plank rect
                collided= lambda robot, plank: 
                plank.rect.collidepoint(robot_x+3, robot_y + self.robot.height-2) 
                )
            if current_plank is not None:
                # the robot moves together with the plank, vertically
                self.robot.move(dy=current_plank.speed)
            else:
                # the robot is walking on water
                print("Walking on water?!")
                self.blit_game_over()
                exit()
        
        # the robot is on a grass strip
        else:
            # collision with a monster
            if spritecollideany(
                self.robot, 
                self.monsters, collided=collide_rect_ratio(ratio=0.5)) is not None:
                print("Collision with monster!")

                # blitting the 'Game over' text
                self.blit_game_over()
                exit()

            # collision with a coin
            # the use of spritecollide with dotkill=True removes the collected coin
            elif spritecollide(self.robot, self.coins, True) != []:
                print("Coin collected!")
                self.robot.score+=1

            # collision with the final door
            elif spritecollideany(self.robot, self.door) is not None:
            # self.door.get_rect().colliderect(self.robot.rect):
                self.game_won()
    
    def update_score(self):
        '''Method for blitting the current score'''
        font = pg.font.SysFont('freesanbold.ttf', 25)
        score_txt = font.render(f"Current score: {self.robot.score}", True, (0,0,0))
        self.screen.blit(score_txt, score_txt.get_rect(topleft = (screen_width - 150, 30)))
        pg.display.flip()

    def blit_game_over(self):
        font = pg.font.SysFont('freesanbold.ttf', 50)
        txt = font.render(f"Game over! Score: {self.robot.score}", True, (255,0,0))
        self.screen.blit(txt, txt.get_rect(center = (screen_width//2, board_height//2)))
        pg.display.flip()
        sleep(2)

    def game_won(self):
        font = pg.font.SysFont('freesanbold.ttf', 50)
        txt = font.render(f"You won! Score: {self.robot.score}", True, (255,0,0))
        self.screen.blit(txt, txt.get_rect(center = (screen_width//2, board_height//2)))
        pg.display.flip()
        sleep(2)
        exit()
                
    def main_loop(self):
        clock = pg.time.Clock()

        while True:
            # while checking for pygame events we may also get robot movement
            robot_dx, robot_dy = self.check_events()
            # moving the robot
            self.robot.move(robot_dx, robot_dy)  
            self.draw_window()
            # moving all Sprites backwards together with background
            move_backwards(self.robot)
            self.check_robot_position()
            self.planks.update()
            self.monsters.update()
            self.coins.update()
            self.door.update()
            self.update_score()
            clock.tick(fps)

    def draw_window(self):

        # blitting the board
        self.screen.blit(self.board_surface, (0,0))
        
        # moving the board horizontally
        global pixels_scrolled
        if pixels_scrolled < board_width - screen_width:
            self.board_surface.scroll(dx=-scroll_speed, dy=0)
            pixels_scrolled+=scroll_speed

        # drawing the moving planks
        self.planks.draw(self.screen)
        # drawing the monsters and coins
        self.monsters.draw(self.screen)
        self.coins.draw(self.screen)
        self.door.draw(self.screen)
        # drawing the robot
        self.robot.draw(self.screen)
        pg.display.flip()

    def check_events(self):
        # by default the robot does not move
        (robot_dx, robot_dy) = (0,0)

        for event in pg.event.get():
            if event.type == pg.QUIT:
                exit()

            # moving the robot 
            elif event.type == pg.KEYDOWN:
                if event.key == pg.K_LEFT:
                    robot_dx, robot_dy = -horizontal_unit, 0
                elif event.key == pg.K_RIGHT:
                    robot_dx, robot_dy = horizontal_unit, 0
                elif event.key == pg.K_DOWN:
                    robot_dx, robot_dy = 0, vertical_unit
                elif event.key == pg.K_UP:
                    robot_dx, robot_dy = 0, -vertical_unit

        return (robot_dx, robot_dy)
           

if __name__ == "__main__":
    Game()