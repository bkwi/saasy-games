conn = new Mongo();
db = conn.getDB("sassy_db");
db.users.createIndex({"username": 1}, {unique: true});
