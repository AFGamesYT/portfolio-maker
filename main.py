import requests
from flask import Flask, render_template, request, redirect, url_for

import uuid
from werkzeug.utils import secure_filename

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

tool_icons = {
        "Python": "🐍", "Flask": "🌶", "HTML": "📄", "CSS": "🎨",
        "HTML/CSS": "🖌️", "Git": "🔧", "GitHub": "🐙", "Telegram": "✈️",
        "Телеграм": "✈️", "SQL": "🗄️", "SQLite": "📘", "JavaScript": "⚡",
        "JS": "⚡", "Jinja": "🧩", "PyGame": "🎮", "Pygame": "🎮", "Java": "☕"
    }

@app.route("/")
def homepage():
    global tool_icons
    connection = sqlite3.connect("data.db")
    cursor = connection.cursor()

    data = cursor.execute("SELECT * FROM portfolio").fetchall()

    connection.close()

    portfolios = []
    filter_skill = request.args.get('skill')
    if filter_skill:
        filter_skill = filter_skill.lower().strip()
    else:
        portfolios = data
    
    for id, uuid, name, bio, github, telegram, avatar, skills_str in data:
        skills = [s.strip() for s in skills_str.split(",") if s.strip()]

        skills_lower = [s.lower() for s in skills]

        if filter_skill is None or filter_skill in skills_lower:
            portfolios.append((id, uuid, name, bio, github, telegram, avatar, skills))
        

    return render_template("index.html", data=portfolios, tool_icons=tool_icons, current_skill=filter_skill or '')

@app.route("/create/", methods=["GET", "POST"])
def create_portfolio():
    if request.method == "GET":
        return render_template("form.html")

    if request.method == "POST":
        error = False
        errors = []

        try:
            connection = sqlite3.connect("data.db")
            cursor = connection.cursor()


            existing_portfolios = cursor.execute("SELECT * FROM portfolio").fetchall()
            existing_names = []
            existing_uuids = []

            for existing_portfolio in existing_portfolios:
                existing_names.append(existing_portfolio[2])
                existing_uuids.append(existing_portfolio[1])

            data = request.form

            username = data['username']
            if username in existing_names:
                error = True
                errors.append("This username is taken.")


            bio = data['bio']
            skills = data['skills']
            github_username = data['github_username'].strip().replace("https://github.com/", '').replace('/', '')

            if github_username:
                check_req = requests.get(f"https://api.github.com/users/{github_username}/repos")
                if check_req.status_code == 404:
                    error = True
                    errors.append("This GitHub username does not exist. Please write the link to it, or the GitHub username directly.")

            telegram = data['telegram'].strip().replace("https://", "")

            if telegram:
                telegram_username = telegram.replace("t.me/", "").replace("/", "")
                try:
                    tg_check = requests.get(f"https://t.me/{telegram_username}")
                    if tg_check.status_code != 200 or "If you have Telegram, you can contact" not in tg_check.text:
                        error = True
                        errors.append("This Telegram username does not exist.")
                except Exception:
                    error = True
                    errors.append("Could not verify Telegram username. Please try again later.")


            uid = str(uuid.uuid4())
            if uid in existing_uuids:
                uid = str(uuid.uuid4())


            avatar = request.files.get('avatar')
            if not error and avatar and avatar.filename:
                filename = secure_filename(f"{uid}_{avatar.filename}")
                while "/" in filename:
                    filename.replace("/", "")

                avatar_path = f"static/uploads/{filename}"
                avatar.save(avatar_path)

                avatar_filename = avatar_path.replace("static/", "")
            else:
                avatar_filename = 'placeholder.png'

            if not error:
                cursor.execute("""
                INSERT INTO portfolio (uuid, name, bio, github, telegram, avatar, skills) 
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (uid, username, bio, github_username, telegram, avatar_filename, skills))
            else:
                print(errors)

            connection.commit()
            connection.close()

            return redirect(url_for("homepage"))


        except Exception as e:
            error = True
            errors.append("Something went wrong. Please try again later. Error: "+str(e))
            print(errors)
        
        return redirect(url_for('homepage'))


@app.route('/portfolio/<user_uuid>')
def view_portfolio(user_uuid):
    global tool_icons
    connection = sqlite3.connect("data.db")
    cursor = connection.cursor()

    data = cursor.execute("SELECT * FROM portfolio WHERE uuid = ?", (user_uuid,)).fetchone()
    if not data:
        return "404: This portfolio doesn't exist.", 404

    skills = str(data[7]).split(", ")

    gh_repos = []

    gh_username = data[4]
    if gh_username:
        gh_data = requests.get(f"https://api.github.com/users/{gh_username}/repos")
        if not gh_data.ok:
            return "Something went wrong. Please check your connection and try again."


        for repo in gh_data.json():
            if repo["id"] and repo["name"]:
                if not repo["private"]:
                    gh_repos.append({"name": repo["name"], "description": repo["description"], "link": repo["html_url"]})

    connection.close()

    data_dict = {
        "id": data[0],
        "uuid": data[1],
        "name": data[2],
        "bio": data[3],
        "github": data[4],
        "telegram": data[5],
        "avatar": data[6],
        "skills": skills,
        "gh_repos": gh_repos
    }

    return render_template("portfolio_template.html", **data_dict, tool_icons=tool_icons)

if __name__ == "__main__":
    app.run()
