from flask import Flask, render_template

import sqlite3

app = Flask(__name__)


"""
0: user id
1: uuid
2: name
3: bio
4: github
5: telegram
6: image
7: skills
"""
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
