const app = new Vue({
  el: "#app",

  data: {
    user: null,
    gamesAvailable: [
      {name: "Tic Tac Toe", type: 1},
      {name: "Cards", type: 2},
    ],
    gameTypeSelected: 1,
    opponentsAvailable: [
      {name: "another human", type: "human"},
      {name: "a computer", type: "cpu"},
    ],
    opponentTypeSelected: "human",
    ws: null,
    pendingGames: [],
  },

  computed: {
    visiblePendingGames: function () {
      return this.pendingGames.filter(game => game.host_username !== this.user.username);
    },
  },

  mounted: function (e) {
    this.ws = new WebSocket(`ws://localhost:8000/ws`);
    this.$http.get("/api/user").then(response => {
      this.user = response.body.user;
      this.getPendingGames();
    }, response => {
      // err
    })
  },

  methods: {

    startNewGame: function () {
      let body = {
        game_type: this.gameTypeSelected,
        opponent_type: this.opponentTypeSelected,
      };
      this.$http.post("/api/new-game", body).then(response => {
        window.location.replace(`/waiting-room/${response.body.waiting_room_id}`);
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
