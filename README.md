## Saasy-games

### Running it locally
```sh
docker compose build
docker compose up
```

App should now be available at `http://localhost:8000`


### Key concepts
* Only one game is available at the moment, but it should be fairly easy to add new ones. On the backend side, each game is represented by a Game class (for both db and game logic, at least for now). It has its game-specific state, list of players, name etc. It also has an `apply_move()` method, that consumes moves (data) comming from the browser. On the frontend side, it's a component that can display the game's state and produces moves compatible for specific game.
* Players see their and opponent's moves in real time. It's also possible to spectate a game. Frontend part gets updated via websockets (and redis pub/sub)
* When a player wants to play vs an AI player, they'll get instantly redirected to the game page. When the game is finished, they'll be redirected back to home page.
* When player A starts a game vs a live opponent, they'll get redirected to a waiting room. Player B can see this "penging" game on their home page. Once Player B joins this game, both players get redirected to the game page.
* All ongoing games can be spectated by other players.

### Tech used
* python + aiohttp for backend, vue.js on the front
* MongoDB for storing user and game data
* redis for storing temporary data (like pending games) and for PUB/SUB communication

### Things missing
* I just realised that I didn't limit the numer of games you can take part in (or spectate). This can be done by storing this information in Redis and not allowing to create/join new ones (or force-redirect to the one user is already playing/spectating)