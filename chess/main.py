# chess/main.py
import sys
import os
import pygame as p
from chess.engine import GameState, Move
from chess.chessAi import findRandomMoves, findBestMove
from multiprocessing import Process, Queue

# Đường dẫn tuyệt đối đến thư mục gốc CHESS-AI
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

# Khởi tạo mixer âm thanh
p.mixer.init()
try:
    move_sound = p.mixer.Sound(os.path.join(BASE_DIR, "sounds", "move-sound.mp3"))
    capture_sound = p.mixer.Sound(os.path.join(BASE_DIR, "sounds", "capture.mp3"))
    promote_sound = p.mixer.Sound(os.path.join(BASE_DIR, "sounds", "promote.mp3"))
except FileNotFoundError as e:
    print(f"Sound file not found: {e}. Continuing without sound.")
    move_sound = None
    capture_sound = None
    promote_sound = None

BOARD_WIDTH = BOARD_HEIGHT = 512
MOVE_LOG_PANEL_WIDTH = 250
MOVE_LOG_PANEL_HEIGHT = BOARD_HEIGHT
DIMENSION = 8
SQ_SIZE = BOARD_HEIGHT // DIMENSION
MAX_FPS = 15
IMAGES = {}

SET_WHITE_AS_BOT = False
SET_BLACK_AS_BOT = True

# Màu sắc
LIGHT_SQUARE_COLOR = (237, 238, 209)
DARK_SQUARE_COLOR = (119, 153, 82)
MOVE_HIGHLIGHT_COLOR = (84, 115, 161)
POSSIBLE_MOVE_COLOR = (255, 255, 51)

def loadImages():
    pieces = ['bR', 'bN', 'bB', 'bQ', 'bK', 'bp', 'wR', 'wN', 'wB', 'wQ', 'wK', 'wp']
    for piece in pieces:
        try:
            image_path = os.path.join(BASE_DIR,"images1", piece + ".png")
            original_image = p.image.load(image_path)
            IMAGES[piece] = p.transform.smoothscale(original_image, (SQ_SIZE, SQ_SIZE))
        except FileNotFoundError as e:
            print(f"Image file not found: {e}. Exiting.")
            sys.exit(1)

def pawnPromotionPopup(screen, gs):
    print("Entering pawnPromotionPopup")
    font = p.font.SysFont("Times New Roman", 30, False, False)
    text = font.render("Choose promotion:", True, p.Color("black"))

    button_width, button_height = 100, 100
    buttons = [
        p.Rect(100, 200, button_width, button_height),
        p.Rect(200, 200, button_width, button_height),
        p.Rect(300, 200, button_width, button_height),
        p.Rect(400, 200, button_width, button_height)
    ]

    if gs.whiteToMove:
        button_images = [
            p.transform.smoothscale(p.image.load(os.path.join(BASE_DIR, "images1", "bQ.png")), (100, 100)),
            p.transform.smoothscale(p.image.load(os.path.join(BASE_DIR, "images1", "bR.png")), (100, 100)),
            p.transform.smoothscale(p.image.load(os.path.join(BASE_DIR, "images1", "bB.png")), (100, 100)),
            p.transform.smoothscale(p.image.load(os.path.join(BASE_DIR, "images1", "bN.png")), (100, 100))
        ]
    else:
        button_images = [
            p.transform.smoothscale(p.image.load(os.path.join(BASE_DIR,  "images1", "wQ.png")), (100, 100)),
            p.transform.smoothscale(p.image.load(os.path.join(BASE_DIR,  "images1", "wR.png")), (100, 100)),
            p.transform.smoothscale(p.image.load(os.path.join(BASE_DIR,  "images1", "wB.png")), (100, 100)),
            p.transform.smoothscale(p.image.load(os.path.join(BASE_DIR,  "images1", "wN.png")), (100, 100))
        ]

    while True:
        for e in p.event.get():
            if e.type == p.QUIT:
                p.quit()
                sys.exit()
            elif e.type == p.MOUSEBUTTONDOWN:
                mouse_pos = e.pos
                for i, button in enumerate(buttons):
                    if button.collidepoint(mouse_pos):
                        print(f"Selected promotion: {['Q', 'R', 'B', 'N'][i]}")
                        return ['Q', 'R', 'B', 'N'][i]

        screen.fill(p.Color(LIGHT_SQUARE_COLOR))
        screen.blit(text, (110, 150))

        for i, button in enumerate(buttons):
            p.draw.rect(screen, p.Color("white"), button)
            screen.blit(button_images[i], button.topleft)

        p.display.flip()

def main():
    p.init()
    screen = p.display.set_mode((BOARD_WIDTH + MOVE_LOG_PANEL_WIDTH, BOARD_HEIGHT))
    clock = p.time.Clock()
    screen.fill(p.Color(LIGHT_SQUARE_COLOR))
    moveLogFont = p.font.SysFont("Times New Roman", 12, False, False)
    infoFont = p.font.SysFont("Times New Roman", 20, False, False)
    gs = GameState()
    if gs.playerWantsToPlayAsBlack:
        gs.board = gs.board1
    validMoves = gs.getValidMoves()
    print(f"Initial valid moves: {len(validMoves)}")
    moveMade = False
    animate = False
    loadImages()
    running = True
    squareSelected = ()
    playerClicks = []
    gameOver = False
    playerWhiteHuman = not SET_WHITE_AS_BOT
    playerBlackHuman = not SET_BLACK_AS_BOT
    AIThinking = False
    moveFinderProcess = None
    moveUndone = False
    pieceCaptured = False
    positionHistory = ""
    previousPos = ""
    countMovesForDraw = 0
    COUNT_DRAW = 0

    while running:
        humanTurn = (gs.whiteToMove and playerWhiteHuman) or (not gs.whiteToMove and playerBlackHuman)
        print(f"Human turn: {humanTurn}, White to move: {gs.whiteToMove}")
        for e in p.event.get():
            if e.type == p.QUIT:
                running = False
            elif e.type == p.MOUSEBUTTONDOWN:
                if not gameOver:
                    location = p.mouse.get_pos()
                    col = location[0] // SQ_SIZE
                    row = location[1] // SQ_SIZE
                    print(f"Mouse clicked at: row={row}, col={col}")
                    if squareSelected == (row, col) or col >= 8:
                        squareSelected = ()
                        playerClicks = []
                    else:
                        squareSelected = (row, col)
                        playerClicks.append(squareSelected)
                    if len(playerClicks) == 2 and humanTurn:
                        print(f"Player clicks: {playerClicks}")
                        move = Move(playerClicks[0], playerClicks[1], gs.board)
                        print(f"Attempting move: {move}")
                        for i in range(len(validMoves)):
                            if move == validMoves[i]:
                                if gs.board[validMoves[i].endRow][validMoves[i].endCol] != '--':
                                    pieceCaptured = True
                                gs.makeMove(validMoves[i])
                                print("Move made successfully")
                                if move.isPawnPromotion:
                                    promotion_choice = pawnPromotionPopup(screen, gs)
                                    gs.board[move.endRow][move.endCol] = move.pieceMoved[0] + promotion_choice
                                    if promote_sound:
                                        promote_sound.play()
                                    pieceCaptured = False
                                if pieceCaptured or move.isEnpassantMove:
                                    if capture_sound:
                                        capture_sound.play()
                                elif not move.isPawnPromotion:
                                    if move_sound:
                                        move_sound.play()
                                pieceCaptured = False
                                moveMade = True
                                animate = True
                                squareSelected = ()
                                playerClicks = []
                                print("Move completed, resetting clicks")
                                break
                        if not moveMade:
                            playerClicks = [squareSelected]
                            print("Move not valid, keeping last click")
            elif e.type == p.KEYDOWN:
                if e.key == p.K_z:
                    gs.undoMove()
                    moveMade = True
                    animate = False
                    gameOver = False
                    if AIThinking:
                        if moveFinderProcess:
                            moveFinderProcess.terminate()
                        AIThinking = False
                    moveUndone = True
                    print("Undo move")
                if e.key == p.K_r:
                    gs = GameState()
                    validMoves = gs.getValidMoves()
                    squareSelected = ()
                    playerClicks = []
                    moveMade = False
                    animate = False
                    gameOver = False
                    if AIThinking:
                        if moveFinderProcess:
                            moveFinderProcess.terminate()
                        AIThinking = False
                    moveUndone = True
                    print("Reset game")

        if not gameOver and not humanTurn and not moveUndone:
            print("AI turn starting")
            if not AIThinking:
                AIThinking = True
                returnQueue = Queue()
                moveFinderProcess = Process(target=findBestMove, args=(gs, validMoves, returnQueue))
                moveFinderProcess.start()
                print("AI process started")
            if not moveFinderProcess.is_alive():
                print("AI process finished")
                try:
                    AIMove = returnQueue.get(timeout=1)
                    print(f"AI move: {AIMove}")
                except Queue.Empty:
                    print("AI move retrieval timed out, selecting random move")
                    AIMove = findRandomMoves(validMoves)
                if AIMove is None:
                    AIMove = findRandomMoves(validMoves)
                    print("AI returned None, selected random move")
                if gs.board[AIMove.endRow][AIMove.endCol] != '--':
                    pieceCaptured = True
                gs.makeMove(AIMove)
                print("AI move made")
                if AIMove.isPawnPromotion:
                    promotion_choice = pawnPromotionPopup(screen, gs)
                    gs.board[AIMove.endRow][AIMove.endCol] = AIMove.pieceMoved[0] + promotion_choice
                    if promote_sound:
                        promote_sound.play()
                    pieceCaptured = False
                if pieceCaptured or AIMove.isEnpassantMove:
                    if capture_sound:
                        capture_sound.play()
                elif not AIMove.isPawnPromotion:
                    if move_sound:
                        move_sound.play()
                pieceCaptured = False
                AIThinking = False
                moveMade = True
                animate = True
                squareSelected = ()
                playerClicks = []
                print("AI move completed")

        if moveMade:
            print("Processing moveMade")
            if countMovesForDraw in [0, 1, 2, 3]:
                countMovesForDraw += 1
            if countMovesForDraw == 4:
                positionHistory += gs.getBoardString()
                if previousPos == positionHistory:
                    COUNT_DRAW += 1
                    positionHistory = ""
                    countMovesForDraw = 0
                else:
                    previousPos = positionHistory
                    positionHistory = ""
                    countMovesForDraw = 0
                    COUNT_DRAW = 0
            if animate:
                print("Animating move")
                animateMove(gs.moveLog[-1], screen, gs.board, clock)
                print("Animation complete")
            validMoves = gs.getValidMoves()
            print(f"Updated valid moves: {len(validMoves)}")
            moveMade = False
            animate = False
            moveUndone = False

        drawGameState(screen, gs, validMoves, squareSelected, moveLogFont, infoFont)

        if COUNT_DRAW == 1:
            gameOver = True
            text = 'Draw due to repetition'
            drawEndGameText(screen, text)
        if gs.stalemate:
            gameOver = True
            text = 'Stalemate'
            drawEndGameText(screen, text)
        elif gs.checkmate:
            gameOver = True
            text = 'Black wins by checkmate' if gs.whiteToMove else 'White wins by checkmate'
            drawEndGameText(screen, text)

        clock.tick(MAX_FPS)
        p.display.flip()

def drawGameState(screen, gs, validMoves, squareSelected, moveLogFont, infoFont):
    drawSquare(screen)
    highlightSquares(screen, gs, validMoves, squareSelected)
    drawPieces(screen, gs.board)
    drawMoveLog(screen, gs, moveLogFont)
    drawGameInfo(screen, gs, infoFont)

def drawSquare(screen):
    global colors
    colors = [p.Color(LIGHT_SQUARE_COLOR), p.Color(DARK_SQUARE_COLOR)]
    for row in range(DIMENSION):
        for col in range(DIMENSION):
            color = colors[((row + col) % 2)]
            p.draw.rect(screen, color, p.Rect(col * SQ_SIZE, row * SQ_SIZE, SQ_SIZE, SQ_SIZE))

def highlightSquares(screen, gs, validMoves, squareSelected):
    if squareSelected != ():
        row, col = squareSelected
        if gs.board[row][col][0] == ('w' if gs.whiteToMove else 'b'):
            s = p.Surface((SQ_SIZE, SQ_SIZE))
            s.set_alpha(100)
            s.fill(p.Color(MOVE_HIGHLIGHT_COLOR))
            screen.blit(s, (col * SQ_SIZE, row * SQ_SIZE))
            s.fill(p.Color(POSSIBLE_MOVE_COLOR))
            for move in validMoves:
                if move.startRow == row and move.startCol == col:
                    screen.blit(s, (move.endCol * SQ_SIZE, move.endRow * SQ_SIZE))

def drawPieces(screen, board):
    for row in range(DIMENSION):
        for col in range(DIMENSION):
            piece = board[row][col]
            if piece != "--":
                screen.blit(IMAGES[piece], p.Rect(col * SQ_SIZE, row * SQ_SIZE, SQ_SIZE, SQ_SIZE))

def drawMoveLog(screen, gs, font):
    moveLogRect = p.Rect(BOARD_WIDTH, 0, MOVE_LOG_PANEL_WIDTH, MOVE_LOG_PANEL_HEIGHT)
    p.draw.rect(screen, p.Color(LIGHT_SQUARE_COLOR), moveLogRect)
    moveLog = gs.moveLog
    moveTexts = []

    for i in range(0, len(moveLog), 2):
        moveString = " " + str(i // 2 + 1) + ". " + str(moveLog[i]) + " "
        if i + 1 < len(moveLog):
            moveString += str(moveLog[i + 1])
        moveTexts.append(moveString)

    movesPerRow = 3
    padding = 10
    lineSpacing = 5
    textY = padding + 50

    for i in range(0, len(moveTexts), movesPerRow):
        text = ""
        for j in range(movesPerRow):
            if i + j < len(moveTexts):
                text += moveTexts[i + j]
        textObject = font.render(text, True, p.Color('black'))
        textLocation = moveLogRect.move(padding, textY)
        screen.blit(textObject, textLocation)
        textY += textObject.get_height() + lineSpacing

def drawGameInfo(screen, gs, font):
    from chess.chessAi import scoreBoard
    infoRect = p.Rect(BOARD_WIDTH, 0, MOVE_LOG_PANEL_WIDTH, 50)
    p.draw.rect(screen, p.Color(LIGHT_SQUARE_COLOR), infoRect)

    turn_text = f"Turn: {'White' if gs.whiteToMove else 'Black'}"
    turn_object = font.render(turn_text, True, p.Color('black'))
    screen.blit(turn_object, (BOARD_WIDTH + 10, 10))

    score = scoreBoard(gs)
    score_text = f"Score: {score:.1f}"
    score_object = font.render(score_text, True, p.Color('black'))
    screen.blit(score_object, (BOARD_WIDTH + 10, 30))

def animateMove(move, screen, board, clock):
    global colors
    deltaRow = move.endRow - move.startRow
    deltaCol = move.endCol - move.startCol
    framesPerSquare = 5
    frameCount = (abs(deltaRow) + abs(deltaCol)) * framesPerSquare
    for frame in range(frameCount + 1):
        row, col = (move.startRow + deltaRow * frame / frameCount, move.startCol + deltaCol * frame / frameCount)
        drawSquare(screen)
        drawPieces(screen, board)
        color = colors[(move.endRow + move.endCol) % 2]
        endSquare = p.Rect(move.endCol * SQ_SIZE, move.endRow * SQ_SIZE, SQ_SIZE, SQ_SIZE)
        p.draw.rect(screen, color, endSquare)
        if move.pieceCaptured != '--':
            if move.isEnpassantMove:
                enPassantRow = move.endRow + 1 if move.pieceCaptured[0] == 'b' else move.endRow - 1
                endSquare = p.Rect(move.endCol * SQ_SIZE, enPassantRow * SQ_SIZE, SQ_SIZE, SQ_SIZE)
            screen.blit(IMAGES[move.pieceCaptured], endSquare)
        screen.blit(IMAGES[move.pieceMoved], p.Rect(col * SQ_SIZE, row * SQ_SIZE, SQ_SIZE, SQ_SIZE))
        p.display.flip()
        clock.tick(240)

def drawEndGameText(screen, text):
    font = p.font.SysFont("Times New Roman", 30, False, False)
    textObject = font.render(text, True, p.Color('black'))
    text_width = textObject.get_width()
    text_height = textObject.get_height()
    textLocation = p.Rect(0, 0, BOARD_WIDTH, BOARD_HEIGHT).move(
        BOARD_WIDTH / 2 - text_width / 2, BOARD_HEIGHT / 2 - text_height / 2)
    screen.blit(textObject, textLocation)
    textObject = font.render(text, 0, p.Color('Black'))
    screen.blit(textObject, textLocation.move(1, 1))

if __name__ == "__main__":
    main()