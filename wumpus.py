# Wormy (a Nibbles clone)
# By Al Sweigart al@inventwithpython.com
# http://inventwithpython.com/pygame
# Released under a "Simplified BSD" license

import random, pygame, sys,math
from pygame.locals import *

FPS = 6
CELLSIZE = 150
WINDOWWIDTH = 5 * CELLSIZE
WINDOWHEIGHT = 5 * CELLSIZE

RADIUS = math.floor(CELLSIZE/2.5)
assert WINDOWWIDTH % CELLSIZE == 0, "Window width must be a multiple of cell size."
assert WINDOWHEIGHT % CELLSIZE == 0, "Window height must be a multiple of cell size."
CELLWIDTH = int(WINDOWWIDTH / CELLSIZE)
CELLHEIGHT = int(WINDOWHEIGHT / CELLSIZE)

#             R    G    B
WHITE     = (255, 255, 255)
BLACK     = (  0,   0,   0)
RED       = (255,   0,   0)
GREEN     = (  0, 255,   0)
DARKGREEN = (  0, 155,   0)
DARKGRAY  = ( 40,  40,  40)
YELLOW = (255,255,0)
BGCOLOR = BLACK

UP = 'up'
DOWN = 'down'
LEFT = 'left'
RIGHT = 'right'

def main():
    global FPSCLOCK, DISPLAYSURF, BASICFONT

    pygame.init()
    FPSCLOCK = pygame.time.Clock()
    DISPLAYSURF = pygame.display.set_mode((WINDOWWIDTH, WINDOWHEIGHT))
    BASICFONT = pygame.font.Font('freesansbold.ttf', 18)
    pygame.display.set_caption('Snake Game')

    showStartScreen()
    while True:
        runGame()
        showGameOverScreen()


def runGame():
    #generate locations then add them to list of locations so next generation doesnt overlap
    currentLocations = []
    player = {'x': 1, 'y': 0}
    currentLocations.append(player)
    wumpus = {'alive':True, 'location':getRandomLocation(currentLocations)}
    currentLocations.append(wumpus['location'])
    treasure = getRandomLocation(currentLocations)
    currentLocations.append(treasure)
    pit1 = getRandomLocation(currentLocations)
    currentLocations.append(pit1) 
    pit2 = getRandomLocation(currentLocations)
    pits = [pit1,pit2]

    gotTreasure = False
    playerDirection = 90
    percepts = []
    danger = []
    safe = []
    safe.append({'location':player.copy(), 'left': 10})

    while True: # main game loop
        DISPLAYSURF.fill(BGCOLOR)
        for event in pygame.event.get(): # event handling loop
            if event.type == QUIT:
                terminate()
            elif event.type == KEYDOWN:
                if (event.key == K_LEFT): 
                    playerDirection = rotatePlayer(LEFT, playerDirection)
                elif (event.key == K_RIGHT):
                    playerDirection = rotatePlayer(RIGHT, playerDirection)
                elif (event.key == K_UP):
                    safe = movePlayer(playerDirection, player, percepts, pits, wumpus, treasure, safe, danger)
                    if safe == -1:
                        return
                    print(safe)
                elif event.key == K_ESCAPE:
                    terminate()
                elif event.key == 32:
                    shoot(player, playerDirection, wumpus)
                # else:
                #     print(event.key)
        
        
        #agent decision making
        
        # move back towards the beginning if you have the treasure
        # if there is a wumpus stench diagonal to another shoot at the wumpus
        # if there is a breeze diagonal to another do not move to the 
        # try not to move to safe cells again
        wander(playerDirection, player, percepts, pits, wumpus, treasure, safe, danger)
            

        
        drawPlayer(player, playerDirection)
        drawWumpus(wumpus)
        drawPit(pit1)
        drawPit(pit2)
        drawTreasure(treasure)
        drawGrid()
        pygame.display.update()
        FPSCLOCK.tick(FPS)


def rotatePlayer(direction, playerDirection):
    if direction == RIGHT:
        playerDirection = playerDirection + 90
        if playerDirection >= 360:
            playerDirection = playerDirection - 360
    elif direction == LEFT:
        playerDirection = playerDirection - 90
        if playerDirection < 0:
            playerDirection = playerDirection + 360
    return playerDirection


def movePlayer(playerDirection, player, percepts, pits, wumpus, treasure, safe, danger):
    switcher = {
        0: UP,
        90: RIGHT,
        180: DOWN,
        270: LEFT,
    }
    

    direction = switcher.get(playerDirection, "nothing")

    if (direction == LEFT) and player['x'] > 0:
        player['x'] = player['x']-1
    elif (direction == RIGHT) and player['x'] < 4:
        player['x'] = player['x'] + 1
    elif (direction == UP) and player['y'] > 0:
        player['y'] = player['y'] - 1
    elif (direction == DOWN) and player['y'] < 4:
        player['y'] = player['y'] + 1
    # else:
    #     print(playerDirection)

    stench = False
    breeze = False
    gotTreasure = False

    #check if player is near or in pits
    for pit in pits:
        if pit['x'] == player['x']:
            if abs(pit['y'] - player['y']) == 1:
                breeze = True
            elif pit['y'] == player['y']:
                print("fell into pit")
                return -1
        elif pit['y'] == player['y']:
            if abs(pit['x'] - player['x']) == 1:
                breeze = True
    
    #check if player is near or in wumpus cell
    if wumpus['location']['x'] == player['x']:
            if abs(wumpus['location']['y'] - player['y']) == 1:
                stench = True
            elif wumpus['location']['y'] == player['y']:
                if wumpus['alive']:
                    print("wumpus ate you")
                    return -1
                else:
                    print("the wumpus is dead")
    elif wumpus['location']['y'] == player['y']:
        if abs(wumpus['location']['x'] - player['x']) == 1:
            stench = True

    #check if in same cell as treasure
    if player == treasure:
        gotTreasure = True
        glitter = True

    if player['x'] == 0 and player['y'] == 0 and gotTreasure:
        print("You Won!")

    #add percepts to queue
    if stench:
        percepts.append({'location':player, 'type':"stench", 'left': 10})
    if breeze:
        percepts.append({'location':player, 'type':"breeze", 'left': 10})
    
    #update percepts
    result = []
    for percept in percepts:
        if percept['left'] > 0:
            percept['left'] = percept['left'] - 1 
            result.append(percept)
    percepts = result

    #update known safe cells
    contained = False
    result = []

    for cell in safe:
        if cell['left'] > 0:
            cell['left'] = cell['left'] -1
            result.append(cell)
        
        #check if cell is already in list
        if cell['location'] == player:
            contained = True
    safe = result

    #if cell is not already in list, add it 
    if not contained:
        safe.append({'location':player.copy(), 'left': 10})
    return safe


def wander(playerDirection, player, percepts, pits, wumpus, treasure, safe, danger):
    direction = [LEFT, UP, DOWN, RIGHT]
    if player['y'] == 0:
        direction.remove(UP)
    if player['x'] == 0:
        direction.remove(LEFT)
    if player['y'] == 4:
        direction.remove(DOWN)
    if player['x'] == 4:
        direction.remove(RIGHT)

    switcher = {
        UP: 0,
        RIGHT: 90,
        DOWN: 180,
        LEFT: 270,
    }
    
    notSafe = direction

    keepGoing = True
    while keepGoing:
        #if all directions have been tried, just pick one
        if len(notSafe) > 0:
            goTo = direction[random.randint(0,len(direction)-1)]
        else:
            goTo = notSafe[random.randint(0,len(direction)-1)]
            playerDirection = switcher.get(goTo, "nothing")
            movePlayer(playerDirection, player, percepts, pits, wumpus, treasure, safe)
            keepGoing = False
            break
            
        # print(goTo)
        keepGoing = False
        if (goTo == LEFT):
            #check if going left is already in safe list
            for cell in safe:
                #if in safe list remove this direction and try again
                if cell['location'] == {'x': player['x']-1, 'y':player['y']}:
                    notSafe.remove(LEFT)
                    keepGoing = True
            #if not in safe list go there
            if not keepGoing:
                playerDirection = 270
                movePlayer(playerDirection, player, percepts, pits, wumpus, treasure, safe, danger)
                keepGoing = False
                break

        elif (goTo == RIGHT):
            for cell in safe:
                #if in safe list remove this direction and try again
                if cell['location'] == {'x': player['x']+1, 'y':player['y']}:
                    notSafe.remove(RIGHT)
                    keepGoing = True
            #if not in safe list go there
            if not keepGoing:
                playerDirection = 90
                movePlayer(playerDirection, player, percepts, pits, wumpus, treasure, safe, danger)
                keepGoing = False
                break
        elif (goTo == UP):
            for cell in safe:
                #if in safe list remove this direction and try again
                if cell['location'] == {'x': player['x'], 'y':player['y']-1}:
                    notSafe.remove(UP)
                    keepGoing = True
            #if not in safe list go there
            if not keepGoing:
                playerDirection = 0
                movePlayer(playerDirection, player, percepts, pits, wumpus, treasure, safe, danger)
                keepGoing = False
                break
        elif (goTo == DOWN):
            for cell in safe:
                #if in safe list remove this direction and try again
                if cell['location'] == {'x': player['x'], 'y':player['y']+1}:
                    notSafe.remove(DOWN)
                    keepGoing = True
            #if not in safe list go there
            if not keepGoing:
                playerDirection = 180
                movePlayer(playerDirection, player, percepts, pits, wumpus, treasure, safe, danger)
                keepGoing = False
                break
        else:
            print(goTo)

def shoot(player, playerDirection, wumpus):
    switcher = {
        0: UP,
        90: RIGHT,
        180: DOWN,
        270: LEFT,
    }

    direction = switcher.get(playerDirection, "nothing")

    if (direction == LEFT) and player['x'] > 0:
        player['x'] = player['x']-1
    elif (direction == RIGHT) and player['x'] < 4:
        player['x'] = player['x'] + 1
    elif (direction == UP) and player['y'] > 0:
        player['y'] = player['y'] - 1
    elif (direction == DOWN) and player['y'] < 4:
        player['y'] = player['y'] + 1
    # else:
    #     print(playerDirection)


def drawPlayer(player, playerDirection):
    offset = 62
    xOffset = 0
    yOffset = 0
    if playerDirection == 0:
        yOffset = -offset
    elif playerDirection == 180:
        yOffset = offset
    elif playerDirection == 90:
        xOffset = offset
    elif playerDirection == 270:
        xOffset = -offset

    x = player['x'] * CELLSIZE
    y = player['y'] * CELLSIZE

    #render the C for character
    font = pygame.font.Font('freesansbold.ttf', CELLSIZE-20)
    C = font.render('C', True, WHITE)
    CRect = C.get_rect()
    CRect.topleft = (x+(CELLSIZE/6),y+(CELLSIZE/8))

    #rednder the dot that indicates the direction the character is facing
    pygame.draw.circle(DISPLAYSURF, RED, (x+(CELLSIZE/2)+xOffset,y+(CELLSIZE/2)+yOffset),10)
    DISPLAYSURF.blit(C, CRect)


def drawWumpus(wumpus):
    location = wumpus['location']
    font = pygame.font.Font('freesansbold.ttf', CELLSIZE)
    x = location['x'] * CELLSIZE
    y = location['y'] * CELLSIZE
    W = font.render('W', True, WHITE)
    WRect = W.get_rect()
    WRect.topleft = (x+5,y)
    DISPLAYSURF.blit(W, WRect)


def drawPit(pit):
    font = pygame.font.Font('freesansbold.ttf', CELLSIZE)
    x = pit['x'] * CELLSIZE
    y = pit['y'] * CELLSIZE
    P = font.render('P', True, WHITE)
    PRect = P.get_rect()
    PRect.topleft = (x+(CELLSIZE/7),y)
    DISPLAYSURF.blit(P, PRect)


def drawTreasure(treasure):
    font = pygame.font.Font('freesansbold.ttf', CELLSIZE)
    x = treasure['x'] * CELLSIZE
    y = treasure['y'] * CELLSIZE
    T = font.render('T', True, WHITE)
    TRect = T.get_rect()
    TRect.topleft = (x+(CELLSIZE/5),y)
    DISPLAYSURF.blit(T, TRect)


def drawPressKeyMsg():
    pressKeySurf = BASICFONT.render('Press a key to play.', True, YELLOW)
    pressKeyRect = pressKeySurf.get_rect()
    pressKeyRect.topleft = (WINDOWWIDTH - 200, WINDOWHEIGHT - 30)
    DISPLAYSURF.blit(pressKeySurf, pressKeyRect)


def checkForKeyPress():
    if len(pygame.event.get(QUIT)) > 0:
        terminate()

    keyUpEvents = pygame.event.get(KEYUP)
    if len(keyUpEvents) == 0:
        return None
    if keyUpEvents[0].key == K_ESCAPE:
        terminate()
    return keyUpEvents[0].key


def showStartScreen():
    titleFont = pygame.font.Font('freesansbold.ttf', 100)
    titleSurf1 = titleFont.render('Griffin', True, RED, YELLOW)
    titleSurf2 = titleFont.render('Hackley', True, WHITE)

    degrees1 = 0
    degrees2 = 0
    while True:
        DISPLAYSURF.fill(BGCOLOR)
        rotatedSurf1 = pygame.transform.rotate(titleSurf1, degrees1)
        rotatedRect1 = rotatedSurf1.get_rect()
        rotatedRect1.center = (math.floor(WINDOWWIDTH / 2), math.floor(WINDOWHEIGHT / 2))
        DISPLAYSURF.blit(rotatedSurf1, rotatedRect1)

        rotatedSurf2 = pygame.transform.rotate(titleSurf2, degrees2)
        rotatedRect2 = rotatedSurf2.get_rect()
        rotatedRect2.center = (math.floor(WINDOWWIDTH / 2), math.floor(WINDOWHEIGHT / 2))
        DISPLAYSURF.blit(rotatedSurf2, rotatedRect2)

        drawPressKeyMsg()

        if checkForKeyPress():
            pygame.event.get() # clear event queue
            return
        pygame.display.update()
        FPSCLOCK.tick(FPS)
        degrees1 += 3 # rotate by 3 degrees each frame
        degrees2 += 7 # rotate by 7 degrees each frame


def terminate():
    pygame.quit()
    sys.exit()


def getRandomLocation(currentLocations):
    temp = {'x': random.randint(0, CELLWIDTH - 1), 'y': random.randint(0, CELLHEIGHT - 1)}
    overlap = True
    while overlap:
        overlap = False
        for location in currentLocations:
            if temp == location:
                overlap = True
                temp = {'x': random.randint(0, CELLWIDTH - 1), 'y': random.randint(0, CELLHEIGHT - 1)}
    return temp


def showGameOverScreen():
    gameOverFont = pygame.font.Font('freesansbold.ttf', 150)
    gameSurf = gameOverFont.render('Game', True, WHITE)
    overSurf = gameOverFont.render('Over', True, WHITE)
    gameRect = gameSurf.get_rect()
    overRect = overSurf.get_rect()
    gameRect.midtop = (math.floor(WINDOWWIDTH / 2), 10)
    overRect.midtop = (math.floor(WINDOWWIDTH / 2), gameRect.height + 10 + 25)

    DISPLAYSURF.blit(gameSurf, gameRect)
    DISPLAYSURF.blit(overSurf, overRect)
    drawPressKeyMsg()
    pygame.display.update()
    pygame.time.wait(500)
    checkForKeyPress() # clear out any key presses in the event queue

    while True:
        if checkForKeyPress():
            pygame.event.get() # clear event queue
            return


def drawGrid():
    for x in range(0, WINDOWWIDTH, CELLSIZE): # draw vertical lines
        pygame.draw.line(DISPLAYSURF, DARKGRAY, (x, 0), (x, WINDOWHEIGHT))
    for y in range(0, WINDOWHEIGHT, CELLSIZE): # draw horizontal lines
        pygame.draw.line(DISPLAYSURF, DARKGRAY, (0, y), (WINDOWWIDTH, y))


if __name__ == '__main__':
    main()