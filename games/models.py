import random

from bson import ObjectId
from pydantic import BaseModel, Field


class User(BaseModel):
    id: ObjectId = Field(default_factory=ObjectId, alias="_id")
    username: str
    pwd_salt: bytes
    pwd_hash: bytes
    games_played: int = 0
    games_won: int = 0

    class Config:
        arbitrary_types_allowed = True

    def db_dict(self):
        return self.dict(by_alias=True)

    def data_dict(self):
        return {"id": str(self.id), "username": self.username}


class Game(BaseModel):
    id: ObjectId = Field(default_factory=ObjectId, alias="_id")
    players: list[dict] = []
    next_player: dict = None
    code_name: str = ""
    display_name: str = ""
    state: dict = {}
    winner: dict = None
    moves_history: list[dict] = []
    finished: bool = False

    class Config:
        arbitrary_types_allowed = True

    def start(self, players: list):
        raise NotImplementedError


class TicTacToeGame(Game):
    state: dict = Field(
        default_factory=lambda: {"board": [["", "", ""] for _ in range(3)]}
    )

    def __init__(self, **data):
        super().__init__(**data)
        self.code_name = "tictactoe"
        self.display_name = "Tic Tac Toe"

    def db_dict(self):
        return self.dict(by_alias=True)

    def start(self, players: list[dict]):
        chars = ["X", "O"]
        random.shuffle(players)
        players[0]["char"] = chars.pop()
        players[1]["char"] = chars.pop()
        self.players = players
        self.next_player = players[0]

        if self.next_player["id"] == "cpu":
            self.make_cpu_move()

    def make_cpu_move(self):
        available_cells = []
        for x, row in enumerate(self.state["board"]):
            for y, cell in enumerate(row):
                if cell == "":
                    available_cells.append({"x": x, "y": y})

        move = random.choice(available_cells)
        return self.apply_move("cpu", move)

    def apply_move(self, player_id, move):
        if self.next_player["id"] != player_id:
            return False

        x, y = move["x"], move["y"]
        if self.state["board"][x][y] != "":
            return False

        self.state["board"][x][y] = self.next_player["char"]
        if player_id != "cpu":
            move["player_id"] = player_id
            self.moves_history.append(move)

        for player in self.players:
            if player["id"] != player_id:
                self.next_player = player

        if winning_char := self.check_winner():
            self.finished = True
            for player in self.players:
                if winning_char == player["char"]:
                    self.winner = player
                    return True

        if self.check_draw():
            self.finished = True
            return True

        if self.next_player["id"] == "cpu":
            return self.make_cpu_move()

        return True

    def check_draw(self):
        for row in self.state["board"]:
            for cell in row:
                if cell == "":
                    return False
        return True

    def check_winner(self):
        board = self.state["board"]

        # check rows
        for row in board:
            if all(row) and len(set(row)) == 1:
                return row[0]

        # check columns
        for col_idx in (0, 1, 2):
            col = [row[col_idx] for row in board]
            if all(col) and len(set(col)) == 1:
                return col[0]

        # check diagonals
        diagonals = [
            [board[0][0], board[1][1], board[2][2]],
            [board[2][0], board[1][1], board[0][2]],
        ]
        for diag in diagonals:
            if all(diag) and len(set(diag)) == 1:
                return diag[0]

        return None


GAME_TYPES = {"tictactoe": TicTacToeGame}
TicTacToeGame(_id=ObjectId())
