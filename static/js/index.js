const app = new Vue({
  el: "#app",

  data: {
    user: null,
    gamesAvailable: [
      {name: "Tic Tac Toe", codename: "tictactoe"},
      {name: "Cards", codename: "cards"},
    ],
    gameSelected: {name: "Tic Tac Toe", codename: "tictactoe"},
    opponentsAvailable: [
      {name: "another human", type: "human"},
      {name: "a computer", type: "cpu"},

    ],
    opponentSelected: {name: "another human", type: "human"},
    ws: null,
    pendingGames: [],
    gameStats: {}
  },

  computed: {
    visiblePendingGames: function () {
      return this.pendingGames.filter(game => game.host_username !== this.user.username);
    },
  },

  mounted: function (e) {
    this.ws = new WebSocket(`ws://${window.location.host}/ws`);
    this.$http.get("/api/user").then(response => {
      this.user = response.body.user;
      this.getPendingGames();
    }, response => {
      // err
    })

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

  }
})
