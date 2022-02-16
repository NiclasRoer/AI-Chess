"""
Responsible for handling user input and displaying the current GameState object.
"""

import pygame as p
from Chess.Chess import ChessEngine, ChessAI
from multiprocessing import Process, Queue

p.init()
WIDTH = HEIGHT = 512
LOG_WIDTH = 250
LOG_HEIGHT = HEIGHT
DIMENSION = 8
SQ_SIZE = HEIGHT // DIMENSION
MAX_FPS = 15
IMAGES = {}

"""
initialize a global dictionary of images. This will be called exactly once in the main
"""


def loadImages():
    pieces = ['wp', 'wR', 'wN', 'wB', 'wQ', 'wK', 'bp', 'bR', 'bN', 'bB', 'bQ', 'bK']
    for piece in pieces:
        IMAGES[piece] = p.transform.scale(p.image.load("images/" + piece + ".png"), (SQ_SIZE, SQ_SIZE))
        # now we can access an image by saying 'IMAGES['wp']'

"""
This main driver for out code. This will handle user input and updating the graphics
"""


def main():
    p.init()
    screen = p.display.set_mode((WIDTH + LOG_WIDTH, HEIGHT))
    clock = p.time.Clock()
    screen.fill(p.Color("white"))
    gs = ChessEngine.GameState()

    moveLogFont = p.font.SysFont("Arial", 12, False, False)
    validMoves = gs.getValidMoves()
    moveMade = False  # flag variable for when a move is made
    animate = False
    gameOver = False

    playerOne = True  # if a human is playing white, then this will be True, AI is False
    playerTwo = True  # same as above but for black
    AIThinking = False
    moveFinderProcess = None
    LVLW = 0
    LVLB = 0
    loadImages()
    running = True
    sqSelected = ()  # no square is selected, keep track of the last click of the user (tuple: (row, col))
    playerClicks = []  # keep track of player clicks (two tuples: [(6, 4), (4, 4)])

    while running:
        humanTurn = (gs.whiteToMove and playerOne) or (not gs.whiteToMove and playerTwo)

        for e in p.event.get():
            if e.type == p.QUIT:
                running = False
            elif e.type == p.MOUSEBUTTONDOWN:
                location = p.mouse.get_pos()
                menu_col = location[0] // SQ_SIZE
                menu_row = location[1] // SQ_SIZE
                if menu_row >= 4:
                    playerTwo, playerOne, LVLB, LVLW = menu(menu_row, menu_col, playerTwo, playerOne, LVLB, LVLW)
                    print(LVLB, LVLW)
                if not gameOver and humanTurn:
                    location = p.mouse.get_pos()
                    col = location[0] // SQ_SIZE
                    row = location[1] // SQ_SIZE

                    if sqSelected == (row, col) or col >= 8:  # the user clicked the same square twice
                        sqSelected = ()  # deselect
                        playerClicks = []
                    else:
                        sqSelected = (row, col)
                        playerClicks.append(sqSelected) # append for both 1st and 2nd clicks
                    if len(playerClicks) == 2:
                        move = ChessEngine.Move(playerClicks[0], playerClicks[1], gs.board)
                        for i in range(len(validMoves)):
                            if move == validMoves[i]:
                                gs.makeMove(validMoves[i])
                                moveMade = True
                                animate = True
                                sqSelected = ()
                                playerClicks = []
                        if not moveMade:
                            playerClicks = [sqSelected]

            elif e.type == p.KEYDOWN:
                if e.key == p.K_z:
                    gs.undoMove()
                    moveMade = True
                    animate = False
                    # gs.CheckMate = False
                    gameOver = False
                if e.key == p.K_r:
                    gs = ChessEngine.GameState()
                    validMoves = gs.getValidMoves()
                    sqSelected = ()
                    playerClicks = []
                    moveMade = False
                    animate = False
                    # gs.CheckMate = False
                    gameOver = False

        # AI move finder logic
        if not gameOver and not humanTurn:

            if gs.whiteToMove:
                if LVLW == 0:
                    AIMove = ChessAI.findRandomMove(validMoves)
                elif LVLW == 1:
                    AIMove = ChessAI.findBestMoveMinMax(gs, validMoves)
            # AIMove = ChessAI.findBestMove(gs, validMoves)

            elif not gs.whiteToMove:
                if LVLB == 0:
                    AIMove = ChessAI.findRandomMove(validMoves)
                elif LVLB == 1:
                    AIMove = ChessAI.findBestMoveMinMax(gs, validMoves)

            gs.makeMove(AIMove)
            moveMade = True
            animate = True

        if moveMade:
            if animate:
                animateMove(gs.moveLog[-1], screen, gs.board, clock)
            validMoves = gs.getValidMoves()
            moveMade = False
            if validMoves == []:
                gs.checkMate = True

        drawGameState(screen, gs, validMoves, sqSelected, moveLogFont)

        if gs.checkMate or gs.staleMate:
            gameOver = True
            drawEndGameText(screen, 'Stalemate' if gs.staleMate else 'Black wins by checkmate' if gs.whiteToMove else 'White wins by checkmate')


        clock.tick(MAX_FPS)
        p.display.flip()

"""
Highlight square selected and moves for piece selected
"""
def highlightSquares(screen, gs, validMoves, sqSelected):
    if sqSelected != ():
        r, c = sqSelected
        if gs.board[r][c][0] == ('w' if gs.whiteToMove else 'b'):
            # highlight selected square
            s = p.Surface((SQ_SIZE, SQ_SIZE))
            s.set_alpha(100)  # 0 transparent, 255 solid
            s.fill(p.Color('blue'))
            screen.blit(s, (c*SQ_SIZE, r*SQ_SIZE))

            # highlight moves
            s.fill(p.Color('yellow'))
            for move in validMoves:
                if move.startRow == r and move.startCol == c:
                    screen.blit(s, (move.endCol*SQ_SIZE, move.endRow*SQ_SIZE))

"""
Responsible for all the graphics within a current game state.
"""


def drawGameState(screen, gs, validMoves, sqSelected, moveLogFont):
    drawBoard(screen)
    highlightSquares(screen, gs, validMoves, sqSelected)
    drawPieces(screen, gs.board)
    drawMoveLog(screen, gs, moveLogFont)
    drawMenu(screen)

def drawBoard(screen):
    global colors
    colors = [p.Color("white"), p.Color("grey")]
    for r in range(DIMENSION):
        for c in range(DIMENSION):
            color = colors[((r+c) % 2)]
            p.draw.rect(screen, color, p.Rect(c*SQ_SIZE, r*SQ_SIZE, SQ_SIZE, SQ_SIZE))
    p.draw.rect(screen, "grey", p.Rect(WIDTH, HEIGHT/2, LOG_WIDTH/2, LOG_HEIGHT/4))
    p.draw.rect(screen, "grey", p.Rect(WIDTH + LOG_WIDTH/2, HEIGHT/2 + HEIGHT/4, LOG_WIDTH/2, LOG_HEIGHT/2))


def drawPieces(screen, board):
    for r in range(DIMENSION):
        for c in range(DIMENSION):
            piece =  board[r][c]
            if piece != "--":
                screen.blit(IMAGES[piece], p.Rect(c*SQ_SIZE, r*SQ_SIZE, SQ_SIZE, SQ_SIZE))

def drawMoveLog(screen, gs, font):
    moveLogRect = p.Rect(WIDTH, 0, LOG_WIDTH, LOG_HEIGHT/2)
    p.draw.rect(screen, p.Color("black"), moveLogRect)
    moveLog = gs.moveLog
    moveTexts = []
    for i in range(0, len(moveLog), 2):
        moveString = str(i//2 + 1) + ". " + moveLog[i].getChessNotation() + " "
        if i+1 < len(moveLog):
            moveString += moveLog[i+1].getChessNotation()
        moveTexts.append(moveString)

    padding = 5
    textY = HEIGHT/2 - 14*len(moveTexts)
    for i in range(len(moveTexts)):
        text = moveTexts[i]
        textObject = font.render(text, True, p.Color('white'))
        textLocation = moveLogRect.move(padding, textY)
        screen.blit(textObject, textLocation)
        # print(textObject.get_height())
        textY += textObject.get_height()
"""
Animation of the move
"""
def animateMove(move, screen, board, clock):
    global colors
    dR = move.endRow - move.startRow
    dC = move.endCol - move.startCol
    framesPerSquare = 5
    frameCount = (abs(dR) + abs(dC)) * framesPerSquare
    for frame in range(frameCount + 1):
        r, c = (move.startRow + dR*frame/frameCount, move.startCol + dC*frame/frameCount)
        drawBoard(screen)
        drawPieces(screen, board)
        # erase the piece moved from its ending square
        color = colors[(move.endRow + move.endRow) % 2]
        endSquare = p.Rect(move.endCol*SQ_SIZE, move.endRow*SQ_SIZE, SQ_SIZE, SQ_SIZE)
        p.draw.rect(screen, color, endSquare)

        if move.pieceCaptured != '--':
            if move.isEnpassantMove:
                enPassantRow = move.endRow+1 if move.pieceCaptured[0] == 'b' else move.endRow-1
                endSquare = p.Rect(move.endCol*SQ_SIZE, enPassantRow*SQ_SIZE, SQ_SIZE, SQ_SIZE)
            screen.blit(IMAGES[move.pieceCaptured], endSquare)
        screen.blit(IMAGES[move.pieceMoved], p.Rect(c*SQ_SIZE, r*SQ_SIZE, SQ_SIZE, SQ_SIZE))
        p.display.flip()
        clock.tick(60)


def drawEndGameText(screen, text):
    font = p.font.SysFont("Helvitica", 32, True, False)
    textObject = font.render(text, True, p.Color('Black'))
    textLocation = p.Rect(0, 0, WIDTH, HEIGHT).move(WIDTH/2 - textObject.get_width()/2, HEIGHT/2 - textObject.get_height()/2)
    screen.blit(textObject, textLocation)

def drawMenu(screen):
    font = p.font.SysFont("Helvitica", 24, True, False)
    textObject = font.render("AI B", True, p.Color('Black'))
    textLocation = p.Rect(0, 0, WIDTH, HEIGHT).move((9*SQ_SIZE - textObject.get_width()/2, 5*SQ_SIZE - textObject.get_height()/2))
    screen.blit(textObject, textLocation)

    font = p.font.SysFont("Helvitica", 24, True, False)
    textObject = font.render("AI W", True, p.Color('Black'))
    textLocation = p.Rect(0, 0, WIDTH, HEIGHT).move((11*SQ_SIZE - textObject.get_width()/2, 5*SQ_SIZE - textObject.get_height()/2))
    screen.blit(textObject, textLocation)

    font = p.font.SysFont("Helvitica", 24, True, False)
    textObject = font.render("LVL B", True, p.Color('Black'))
    textLocation = p.Rect(0, 0, WIDTH, HEIGHT).move((9*SQ_SIZE - textObject.get_width()/2, 7*SQ_SIZE - textObject.get_height()/2))
    screen.blit(textObject, textLocation)

    font = p.font.SysFont("Helvitica", 24, True, False)
    textObject = font.render("LVL W", True, p.Color('Black'))
    textLocation = p.Rect(0, 0, WIDTH, HEIGHT).move((11*SQ_SIZE - textObject.get_width()/2, 7*SQ_SIZE - textObject.get_height()/2))
    screen.blit(textObject, textLocation)

def menu(row, col, playerTwo, playerOne, LVLB, LVLW):
    if 8 <= col < 10 and 4 <= row < 6:
        playerTwo = not playerTwo
    elif 10 <= col < 12 and 4 <= row < 6:
        playerOne = not playerOne
    elif 8 <= col < 10 and 6 <= row < 8:
        LVLB = (LVLB + 1) % 2
    elif 10 <= col < 12 and 6 <= row < 8:
        LVLW = (LVLW + 1) % 2
    return playerTwo, playerOne, LVLB, LVLW


if __name__ == '__main__':
    main()
