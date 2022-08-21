Vue.component("tictactoe", {
  template: "#tictactoe",

  props: ["state"],

  methods: {
    cellClicked: function(x, y) {
      this.$emit("cell-clicked", {x: x, y: y})
    }
  }
});


const app = new Vue({
  el: "#app",

  data: {
    ws: null,
    gameId: null,
    user: null,
    state: {
      board: [],
    },
    players: [],
    next: "",
    winner: null,
    spectator: window.location.pathname.startsWith("/spectate"),
  },

  mounted: function () {
    this.gameId = window.location.pathname.split("/").slice(-1).pop();
    let websocketUrl = `ws://${window.location.host}/ws/game-room/${this.gameId}`;
    if (this.spectator) {
     websocketUrl = `ws://${window.location.host}/ws/spectate/${this.gameId}`;
    };

    this.ws = new WebSocket(websocketUrl);
    this.ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.type === "update_state") {
        this.state = data.state;
        this.next= data.next;
        if (data.winner) {
          this.winner = data.winner;
          function redirect() {
            window.location.replace("/");
          };
          setTimeout(redirect, 3000);
        }
      }
    };


    this.$http.get(`/api/game-room/${this.gameId}`).then(response => {
      this.state = response.body.state;
      this.next = response.body.next;
    }, response => {
      alert("Game not found");
    });

    this.$http.get("/api/user").then(response => {
      this.user = response.body.user;
    }, response => {
      // err
    })
  },

  methods: {
    move: function (event) {
      if (this.spectator) return;

      let data = {
        user: this.user,
        move: event
      };
      this.ws.send(JSON.stringify(data));
    }
  },

});
