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
    players: list[dict]
    next_player: dict
    code_name: str = ""
    display_name: str = ""
    state: dict = {}
    winner: dict = None

    class Config:
        arbitrary_types_allowed = True


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

    def apply_move(self, player_id, move):
        if self.next_player["id"] != player_id:
            return False

        x, y = move["x"], move["y"]
        self.state["board"][x][y] = self.next_player["char"]

        for player in self.players:
            if player["id"] != player_id:
                self.next_player = player

        if winning_char := self.check_winner():
            for player in self.players:
                if winning_char == player["char"]:
                    self.winner = player

        return True

    def check_winner(self):
        board = self.state["board"]
        for row in board:
            print(row)

        # check rows
        for row in board:
            if len(set(row)) == 1:
                return row[0]

        # check columns
        for col_idx in (0, 1, 2):
            col = [row[col_idx] for row in board]
            if len(set(col)) == 1:
                return col[0]

        # check diagonals
        diagonals = [
            [board[0][0], board[1][1], board[2][2]],
            [board[2][0], board[1][1], board[0][2]],
        ]
        for diag in diagonals:
            if len(set(diag)) == 1:
                return diag[0]

        return None
