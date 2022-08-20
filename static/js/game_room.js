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
    next: ""
  },

  mounted: function () {
    this.gameId = window.location.pathname.split("/").slice(-1).pop();
    this.ws = new WebSocket(`ws://localhost:8000/ws/game-room/${this.gameId}`);

    this.ws.onmessage = (event) => {
      console.log("NEW EVENT", event);
      const data = JSON.parse(event.data);
      console.log("DATA", data)
      if (data.type === "update_state") {
        this.state = data.state;
        this.next= data.next;
        if (data.winner) {
          alert(`Winner: ${data.winner.username}`)
          window.location.replace("/");
        }
      }
    };

    this.$http.get(`/api/game-room/${this.gameId}`).then(response => {
      this.state = response.body.state;
      this.next = response.body.next;
    }, response => {
      // err
    });

    this.$http.get("/api/user").then(response => {
      this.user = response.body.user;
    }, response => {
      // err
    })
  },

  methods: {
    move: function (event) {
      let data = {
        user: this.user,
        move: event
      };
      this.ws.send(JSON.stringify(data));
    }
  },

});
