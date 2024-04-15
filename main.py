from abc import ABC, abstractmethod
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn


class MoveRequest(BaseModel):
    player: str
    position_from: list[int]
    position_to: list[int]


class Piece(ABC):
    def __init__(self, color):
        self.color = color

    @abstractmethod
    def move(self, position_from, position_to):
        pass


class King(Piece):
    def move(self, position_from, position_to):
        from_x, from_y = position_from
        to_x, to_y = position_to
        return abs(from_x - to_x) <= 1 and abs(from_y - to_y) <= 1


class Rook(Piece):
    def move(self, position_from, position_to):
        from_x, from_y = position_from
        to_x, to_y = position_to
        return from_x == to_x or from_y == to_y


class Knight(Piece):
    def move(self, position_from, position_to):
        from_x, from_y = position_from
        to_x, to_y = position_to
        dx = abs(from_x - to_x)
        dy = abs(from_y - to_y)
        return (dx == 2 and dy == 1) or (dx == 1 and dy == 2)


class Bishop(Piece):
    def move(self, position_from, position_to):
        from_x, from_y = position_from
        to_x, to_y = position_to
        return abs(from_x - to_x) == abs(from_y - to_y)


class Queen(Piece):
    def move(self, position_from, position_to):
        return Rook().move(position_from, position_to) or Bishop().move(position_from, position_to)


class Pawn(Piece):
    def move(self, position_from, position_to):
        from_x, from_y = position_from
        to_x, to_y = position_to
        return from_x == to_x and abs(from_y - to_y) == 1


class Board:
    def __init__(self):
        self.board = [[None for _ in range(8)] for _ in range(8)]
        self.initialize_board()

    def initialize_board(self):
        self.board[0] = [Rook("black"), Knight("black"), Bishop("black"), Queen("black"), King("black"),
                         Bishop("black"), Knight("black"), Rook("black")]
        self.board[1] = [Pawn("black") for _ in range(8)]
        self.board[6] = [Pawn("white") for _ in range(8)]
        self.board[7] = [Rook("white"), Knight("white"), Bishop("white"), Queen("white"), King("white"),
                         Bishop("white"), Knight("white"), Rook("white")]

    def move_piece(self, position_from, position_to):
        piece = self.get_piece_at(position_from)
        if piece:
            if self.is_valid_move(piece, position_from, position_to):
                self.board[position_to[0]][position_to[1]] = piece
                self.board[position_from[0]][position_from[1]] = None
                return True
            else:
                raise HTTPException(status_code=400, detail="Invalid move!")
        else:
            raise HTTPException(status_code=404, detail="No piece at the specified position!")

    def get_piece_at(self, position):
        return self.board[position[0]][position[1]]

    def is_valid_move(self, piece, position_from, position_to):
        from_x, from_y = position_from
        to_x, to_y = position_to

        if not (0 <= to_x < 8 and 0 <= to_y < 8):
            raise HTTPException(status_code=400, detail="Piece cannot move outside the board!")

        if self.get_piece_at(position_to) and self.get_piece_at(position_to).color == piece.color:
            raise HTTPException(status_code=400, detail="There is a piece of the same color at the destination position!")

        return piece.move(position_from, position_to)

    def serialize_board(self):
        serialized_board = []
        for row in self.board:
            serialized_row = []
            for piece in row:
                serialized_row.append(piece.__class__.__name__ if piece is not None else None)
            serialized_board.append(serialized_row)
        return serialized_board


class Game:
    def __init__(self):
        self.board = Board()
        self.current_player = "white"

    def start_game(self):
        print("Game started!")

    def move(self, player, position_from, position_to):
        if player == self.current_player:
            try:
                if self.board.move_piece(position_from, position_to):
                    print(f"{player} moved a piece from {position_from} to {position_to}")
                    self.current_player = "black" if player == "white" else "white"
                    return True
            except HTTPException as e:
                print(f"Error: {e}")
                return False
        else:
            print("It's not your turn!")
            return False

    def end_game(self):
        print("Game ended!")

    def validate_move(self, player, position_from, position_to):
        try:
            piece = self.board.get_piece_at(position_from)
            return self.board.is_valid_move(piece, position_from, position_to)
        except HTTPException as e:
            print(f"Error: {e}")
            return False

# Ініціалізація FastAPI
app = FastAPI()
game = Game()


@app.post("/start_game")
def start_game():
    game.start_game()
    return {"message": "Game started"}

@app.post("/move")
def move(move: MoveRequest):
    if game.move(move.player, tuple(move.position_from), tuple(move.position_to)):
        return {"message": "Move successful"}
    else:
        return {"message": "Invalid move"}

@app.post("/end_game")
def end_game():
    game.end_game()
    return {"message": "Game ended"}

@app.get("/get_board")
def get_board():
    return {"board": game.board.serialize_board()}


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
