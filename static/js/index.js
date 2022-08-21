const app = new Vue({
  el: "#app",

  data: {
    user: null,
    gamesAvailable: [
      {name: "Tic Tac Toe", codename: "tictactoe"},
    ],
    gameSelected: {name: "Tic Tac Toe", codename: "tictactoe"},
    opponentsAvailable: [
      {name: "another human", type: "human"},
      {name: "a computer", type: "cpu"},

    ],
    opponentSelected: {name: "another human", type: "human"},
    ws: null,
    pendingGames: [],
    pendingFilter: "",
    ongoingGames: [],
    ongoingFilter: "",
    gameStats: {}
  },

  computed: {
    visiblePendingGames: function () {
      return this.pendingGames
        .filter(game => game.host_username !== this.user.username)
        .filter(game => game.host_username.toLowerCase().includes(this.pendingFilter.toLowerCase()));
    },
    visibleOngoingGames: function () {
      if (this.ongoingFilter === "") return this.ongoingGames;

      let visibleGames = [];
      this.ongoingGames.forEach(game => {
        game.players.forEach(player => {
          if (player.toLowerCase().includes(this.ongoingFilter.toLowerCase())) {
            visibleGames.push(game);
            return;
          }
        })
      });
      return visibleGames;
    },
  },

  mounted: function (e) {
    this.ws = new WebSocket(`ws://${window.location.host}/ws/main`);
    this.ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.type === "games_added") {
        if (data.pending_games) {
          data.pending_games.forEach(game => this.pendingGames.push(game));
        }

        if (data.ongoing_games) {
          data.ongoing_games.forEach(game => this.ongoingGames.push(game));
        }
      }

      if (data.type === "games_removed") {
        if (data.pending_games) {
          const removedIds = data.pending_games;
          let gamesLeft = [];
          this.pendingGames.forEach(game => {
            if (!removedIds.includes(game.game_id)) {
              gamesLeft.push(game);
            }
          });
          this.pendingGames = gamesLeft;
        }

        if (data.ongoing_games) {
          const removedIds = data.ongoing_games;
          let gamesLeft = [];
          this.ongoingGames.forEach(game => {
            if (!removedIds.includes(game.game_id)) {
              gamesLeft.push(game);
            }
          });
          this.ongoingGames = gamesLeft;
        }
      }
    }


    this.$http.get("/api/user").then(response => {
      this.user = response.body.user;
      this.getPendingGames();
    }, response => {
      // err
    });

    this.getOngoingGames();

    this.$http.get("/api/stats").then(response => {
      this.gameStats = response.body;
    }, response => {
      // err
    })
  },

  methods: {

    startNewGame: function () {
      let body = {
        game: this.gameSelected,
        opponent: this.opponentSelected,
      };
      this.$http.post("/api/new-game", body).then(response => {
        window.location.replace(response.body.redirect_url);
      }, response => {
        // err
      })
    },

    joinGame: function (gameId) {
      let body = {
        game_id: gameId,
      };
      this.$http.post("/api/join-game", body).then(response => {
        window.location.replace(`/game-room/${gameId}`);
      }, response => {
        // err
      })
    },

    getPendingGames: function () {
      this.$http.get("/api/pending-games").then(response => {
        this.pendingGames = response.body.games;
      }, response => {
        // err
      })

    },

    getOngoingGames: function () {
      this.$http.get("/api/ongoing-games").then(response => {
        this.ongoingGames = response.body.games;
      }, response => {
        // err
      })
    },

    spectate: function(gameId) {
      window.location.replace(`/spectate/${gameId}`);
    }

  }
})
