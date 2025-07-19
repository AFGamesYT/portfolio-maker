from flask import Flask, render_template

import sqlite3

app = Flask(__name__)

@app.route("/")
def homepage():
    connection = sqlite3.connect("data.db")
    cursor = connection.cursor()

    data = cursor.execute("SELECT * FROM portfolio").fetchall()
    print(data)
    connection.commit()
    connection.close()
    return render_template("index.html", data=data)


if __name__ == "__main__":
    app.run()
