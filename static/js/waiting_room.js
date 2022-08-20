const app = new Vue({
  el: "#app",

  mounted: function (e) {
    let gameId = window.location.pathname.split("/").slice(-1).pop();
    let ws = new WebSocket(`ws://localhost:8000/ws/waiting-room/${gameId}`);

    ws.onmessage = (event) => {
      if (event.data === "game_ready") {
        window.location.replace(`/game-room/${gameId}`);
      }
    };
  },

  methods: {
  }
})
