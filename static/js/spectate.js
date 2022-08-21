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
    state: {
      board: [],
    },
    players: [],
    next: "",
    winner: null
  },

  mounted: function () {
    this.gameId = window.location.pathname.split("/").slice(-1).pop();
    this.ws = new WebSocket(`ws://${window.location.host}/ws/game-room/${this.gameId}`);

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
      // err
    });
  },

});
