# chess/chessAi.py
import random
from .engine import GameState

# Định nghĩa giá trị quân cờ
pieceScore = {"K": 0, "Q": 9, "R": 5, "B": 3, "N": 3, "p": 1}

EXTENDED_CENTER_SQUARES = [(2, 2), (2, 3), (2, 4), (2, 5), (3, 2), (3, 5), (4, 2), (4, 5), (5, 2), (5, 3), (5, 4), (5, 5)]

# Điểm vị trí cho các quân cờ (giữ nguyên như mã gốc)
knightScores = [[1, 1, 1, 1, 1, 1, 1, 1],
                [1, 2, 2, 2, 2, 2, 2, 1],
                [1, 2, 3, 3, 3, 3, 2, 1],
                [1, 2, 3, 4, 4, 3, 2, 1],
                [1, 2, 3, 4, 4, 3, 2, 1],
                [1, 2, 3, 3, 3, 3, 2, 1],
                [1, 2, 2, 2, 2, 2, 2, 1],
                [1, 1, 1, 1, 1, 1, 1, 1]]

bishopScores = [[4, 3, 2, 1, 1, 2, 3, 4],
                [3, 4, 3, 2, 2, 3, 4, 3],
                [2, 3, 4, 3, 3, 4, 3, 2],
                [1, 2, 3, 4, 4, 3, 2, 1],
                [1, 2, 3, 4, 4, 3, 2, 1],
                [2, 3, 4, 3, 3, 4, 3, 2],
                [3, 4, 3, 2, 2, 3, 4, 3],
                [4, 3, 2, 1, 1, 2, 3, 4]]

queenScores = [[1, 1, 1, 3, 1, 1, 1, 1],
               [1, 2, 3, 3, 3, 1, 1, 1],
               [1, 4, 3, 3, 3, 4, 2, 1],
               [1, 2, 3, 3, 3, 2, 2, 1],
               [1, 2, 3, 3, 3, 2, 2, 1],
               [1, 4, 3, 3, 3, 4, 2, 1],
               [1, 1, 2, 3, 3, 1, 1, 1],
               [1, 1, 1, 3, 1, 1, 1, 1]]

rookScores = [[4, 3, 4, 4, 4, 4, 3, 4],
              [4, 4, 4, 4, 4, 4, 4, 4],
              [1, 1, 2, 3, 3, 2, 1, 1],
              [1, 2, 3, 4, 4, 3, 2, 1],
              [1, 2, 3, 4, 4, 3, 2, 1],
              [1, 1, 2, 2, 2, 2, 1, 1],
              [4, 4, 4, 4, 4, 4, 4, 4],
              [4, 3, 2, 1, 1, 2, 3, 4]]

whitePawnScores = [[8, 8, 8, 8, 8, 8, 8, 8],
                   [8, 8, 8, 8, 8, 8, 8, 8],
                   [5, 6, 6, 7, 7, 6, 6, 5],
                   [2, 3, 3, 5, 5, 3, 3, 2],
                   [1, 2, 3, 4, 4, 3, 2, 1],
                   [1, 1, 2, 3, 3, 2, 1, 1],
                   [1, 1, 1, 0, 0, 1, 1, 1],
                   [0, 0, 0, 0, 0, 0, 0, 0]]

blackPawnScores = [[0, 0, 0, 0, 0, 0, 0, 0],
                   [1, 1, 1, 0, 0, 1, 1, 1],
                   [1, 1, 2, 3, 3, 2, 1, 1],
                   [1, 2, 3, 4, 4, 3, 2, 1],
                   [2, 3, 3, 5, 5, 3, 3, 2],
                   [5, 6, 6, 7, 7, 6, 6, 5],
                   [8, 8, 8, 8, 8, 8, 8, 8],
                   [8, 8, 8, 8, 8, 8, 8, 8]]

piecePositionScores = {"N": knightScores, "B": bishopScores, "Q": queenScores,
                       "R": rookScores, "wp": whitePawnScores, "bp": blackPawnScores}

CHECKMATE = 1000
STALEMATE = 0
DEPTH = 4

# Định nghĩa các ô trung tâm (d4, d5, e4, e5)
CENTER_SQUARES = [(3, 3), (3, 4), (4, 3), (4, 4)]

def findRandomMoves(validMoves):
    return validMoves[random.randint(0, len(validMoves) - 1)]

def findBestMove(gs, validMoves, returnQueue):
    global nextMove, whitePawnScores, blackPawnScores
    nextMove = None
    random.shuffle(validMoves)

    if gs.playerWantsToPlayAsBlack:
        whitePawnScores, blackPawnScores = blackPawnScores, whitePawnScores

    turnMultiplier = 1 if gs.whiteToMove else -1
    findMoveNegaMaxAlphaBeta(gs, validMoves, DEPTH, -CHECKMATE, CHECKMATE, turnMultiplier)
    returnQueue.put(nextMove)

def findMoveNegaMaxAlphaBeta(gs, validMoves, depth, alpha, beta, turnMultiplier):
    global nextMove
    if depth == 0:
        return turnMultiplier * scoreBoard(gs)

    maxScore = -CHECKMATE
    for move in validMoves:
        gs.makeMove(move)
        nextMoves = gs.getValidMoves()
        score = -findMoveNegaMaxAlphaBeta(gs, nextMoves, depth-1, -beta, -alpha, -turnMultiplier)
        if score > maxScore:
            maxScore = score
            if depth == DEPTH:
                nextMove = move
        gs.undoMove()
        if maxScore > alpha:
            alpha = maxScore
        if alpha >= beta:
            break
    return maxScore

def scoreBoard(gs):
    if gs.checkmate:
        if gs.whiteToMove:
            gs.checkmate = False
            return -CHECKMATE
        else:
            gs.checkmate = False
            return CHECKMATE
    elif gs.stalemate:
        return STALEMATE

    # Tính giai đoạn ván cờ (0: mở đầu, 1: trung cuộc, 2: tàn cuộc)
    total_material = 0
    for row in range(len(gs.board)):
        for col in range(len(gs.board[row])):
            square = gs.board[row][col]
            if square != "--" and square[1] != "K":
                total_material += pieceScore[square[1]]
    game_phase = 0  # Mở đầu
    if total_material < 40:
        game_phase = 1  # Trung cuộc
    if total_material < 20:
        game_phase = 2  # Tàn cuộc

    score = 0
    center_control = {"w": 0, "b": 0}
    extended_center_control = {"w": 0, "b": 0}
    pawn_structure = {"w": 0, "b": 0}
    king_safety = {"w": 0, "b": 0}
    mobility = {"w": 0, "b": 0}
    piece_coordination = {"w": 0, "b": 0}

    # Lưu trữ vị trí các tốt
    white_pawns = [[] for _ in range(8)]
    black_pawns = [[] for _ in range(8)]
    # Đếm số Tượng để tính điểm đôi Tượng
    white_bishops = 0
    black_bishops = 0
    # Đếm số quân trên các cột để tính cột mở
    pieces_on_files = [[] for _ in range(8)]

    # Tính giá trị vật chất và các yếu tố khác
    for row in range(len(gs.board)):
        for col in range(len(gs.board[row])):
            square = gs.board[row][col]
            if square != "--":
                piecePositionScore = 0
                if square[1] != "K":
                    if square[1] == "p":
                        piecePositionScore = piecePositionScores[square][row][col]
                        if square[0] == 'w':
                            white_pawns[col].append(row)
                        else:
                            black_pawns[col].append(row)
                    else:
                        piecePositionScore = piecePositionScores[square[1]][row][col]
                        if square[1] == "B":
                            if square[0] == 'w':
                                white_bishops += 1
                            else:
                                black_bishops += 1
                if square[1] != "K":
                    pieces_on_files[col].append(square)

                # Kiểm soát trung tâm
                if (row, col) in CENTER_SQUARES:
                    weight = pieceScore[square[1]]
                    center_control[square[0]] += weight
                if (row, col) in EXTENDED_CENTER_SQUARES:
                    weight = pieceScore[square[1]]
                    extended_center_control[square[0]] += weight / 2

                # Tính điểm vật chất và vị trí
                if square[0] == 'w':
                    score += pieceScore[square[1]] + piecePositionScore * 0.1
                elif square[0] == 'b':
                    score -= pieceScore[square[1]] + piecePositionScore * 0.1

    # Điểm thưởng cho kiểm soát trung tâm
    score += (center_control["w"] - center_control["b"]) * 0.1
    score += (extended_center_control["w"] - extended_center_control["b"]) * 0.05

    # Đánh giá cấu trúc tốt
    for col in range(8):
        # Tốt trắng
        if white_pawns[col]:
            # Tốt cô lập
            if col > 0 and not white_pawns[col-1] and col < 7 and not white_pawns[col+1]:
                pawn_structure["w"] -= 0.5
            else:
                pawn_structure["w"] += 0.2
            # Tốt thông thoáng
            is_passed = True
            for enemy_row in range(min(white_pawns[col]), 8):
                if col > 0 and enemy_row in black_pawns[col-1]:
                    is_passed = False
                    break
                if enemy_row in black_pawns[col]:
                    is_passed = False
                    break
                if col < 7 and enemy_row in black_pawns[col+1]:
                    is_passed = False
                    break
            if is_passed:
                pawn_structure["w"] += 1.0 if game_phase == 2 else 0.5
        # Tốt đen
        if black_pawns[col]:
            if col > 0 and not black_pawns[col-1] and col < 7 and not black_pawns[col+1]:
                pawn_structure["b"] -= 0.5
            else:
                pawn_structure["b"] += 0.2
            is_passed = True
            for enemy_row in range(max(black_pawns[col]), -1, -1):
                if col > 0 and enemy_row in white_pawns[col-1]:
                    is_passed = False
                    break
                if enemy_row in white_pawns[col]:
                    is_passed = False
                    break
                if col < 7 and enemy_row in white_pawns[col+1]:
                    is_passed = False
                    break
            if is_passed:
                pawn_structure["b"] += 1.0 if game_phase == 2 else 0.5
    score += (pawn_structure["w"] - pawn_structure["b"])

    # Đánh giá an toàn của vua
    white_king_pos = gs.whiteKinglocation
    black_king_pos = gs.blackKinglocation
    # Phạt nếu vua ở trung tâm
    if 2 <= white_king_pos[0] <= 5 and 2 <= white_king_pos[1] <= 5:
        king_safety["w"] -= 0.5 if game_phase < 2 else 0.0
    if 2 <= black_king_pos[0] <= 5 and 2 <= black_king_pos[1] <= 5:
        king_safety["b"] -= 0.5 if game_phase < 2 else 0.0
    # Thưởng nếu vua đã nhập thành
    if not gs.whiteCastleKingside and not gs.whiteCastleQueenside:
        king_safety["w"] += 0.5
    if not gs.blackCastleKingside and not gs.blackCastleQueenside:
        king_safety["b"] += 0.5
    score += (king_safety["w"] - king_safety["b"])

    # Đánh giá tính di động (chỉ tính cho Mã, Tượng, Xe, Hậu)
    valid_moves = gs.getValidMoves()
    for move in valid_moves:
        piece = move.pieceMoved
        if piece[0] == 'w' and piece[1] in ['N', 'B', 'R', 'Q']:
            mobility["w"] += 0.1
        elif piece[0] == 'b' and piece[1] in ['N', 'B', 'R', 'Q']:
            mobility["b"] += 0.1
    score += (mobility["w"] - mobility["b"])

    # Đánh giá tương tác giữa các quân cờ
    # Đôi Tượng
    if white_bishops >= 2:
        piece_coordination["w"] += 0.5
    if black_bishops >= 2:
        piece_coordination["b"] += 0.5
    # Xe trên cột mở
    for col in range(8):
        if not white_pawns[col] and not black_pawns[col]:  # Cột mở
            for piece in pieces_on_files[col]:
                if piece[1] == 'R':
                    piece_coordination[piece[0]] += 0.5
    score += (piece_coordination["w"] - piece_coordination["b"])

    return score