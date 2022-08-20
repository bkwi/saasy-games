const app = new Vue({
  el: "#app",

  data: {
    username: "",
    password: "",
  },

  methods: {
    register: function (e) {
      let body = {
        username: this.username,
        password: this.password
      };
      if (this.password.length < 8) {
        alert("Password needs to be at least 8 characters long");
        return
      };
      this.$http.post("/api/register", body).then(response => {
        window.location.replace("/");
      }, response => {
        alert("Registration failed");
      })
    }
  }
})
