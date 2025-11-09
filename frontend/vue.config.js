// vue.config.js
module.exports = {
  devServer: {
    proxy: "http://localhost:8000"
  }
  // headers: {
  //   'Access-Control-Allow-Headers': "*",
  //   'Access-Control-Allow-Origin': "*",
  //   'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE'
  // }
}
