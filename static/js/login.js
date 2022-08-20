const app = new Vue({
  el: "#app",

  data: {
    username: "",
    password: "",
  },

  methods: {
    login: function (e) {
      let body = {
        username: this.username,
        password: this.password
      };
      this.$http.post("/api/login", body).then(response => {
        window.location.replace("/");
      }, response => {
        alert("Invalid login/password");
      })
    }
  }
})
