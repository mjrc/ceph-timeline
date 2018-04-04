const sqlite3 = require('sqlite3').verbose();
var util = require('util');
var fs = require("fs");


const databaseLocation = '../ceph_timeline.db'


// Connect to the database - there are three modes 

let db = new sqlite3.Database(databaseLocation, sqlite3.OPEN_READONLY, (err) => {
    if (err) {
        return console.error(err.message);
      }
    console.log(`Connected to the databse ${databaseLocation}`);
});


// List all tables 

db.serialize(function () {

    let table = db.all(`SELECT * FROM ceph_objects`, function(err, table) {
        var table_json = JSON.stringify(table);
        fs.writeFileSync('./data.json', table_json , 'utf-8'); 
        console.log(table)
    });

});


db.close();
