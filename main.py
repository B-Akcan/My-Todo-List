from flask import render_template, Flask, request, redirect, url_for, session, flash
from datetime import timedelta
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.secret_key = "batuhan"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///users.sqlite3"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.permanent_session_lifetime = timedelta(days=1)

db = SQLAlchemy(app)
app.app_context().push()

class User(db.Model):
    name = db.Column(db.String(100), primary_key=True, unique=True)
    tasks = db.Column(db.String(1000))

    def __init__(self, name, tasks):
        self.name = name
        self.tasks = tasks

@app.route("/", methods=["POST", "GET"])
@app.route("/login", methods=["POST", "GET"])
def login():
    if request.method == "POST":
        name = request.form["name"]
        session["user"] = name
        session.permanent = True
        if name == "":
            return render_template("login.html")

        found_user = User.query.filter_by(name=name).first()
        if found_user:
            session["tasks"] = found_user.tasks
        else:
            usr = User(name, "")
            db.session.add(usr)
            db.session.commit()
        
        return redirect(url_for("tasks"))
    elif "user" in session:
        return redirect(url_for("tasks"))

    return render_template("login.html")

@app.route("/logout")
def logout():
    session.pop("user", None)
    session.pop("tasks", None)
    return redirect(url_for("login"))

@app.route("/tasks")
def tasks():
    if "user" not in session:
        return redirect(url_for("login"))
    if "tasks" not in session:
        session["tasks"] = ""

    
    name = session["user"]
    tasks = session["tasks"]
    return render_template("tasks.html", name=name, tasks=tasks)

@app.route("/new_task", methods=["POST", "GET"])
def new_task():
    if "user" in session:
        name = session["user"]
        if request.method == "POST":
            task = request.form["task"]
            if session["tasks"] == "":
                session["tasks"] = "|"
            session["tasks"] += task + "|"
            found_user = User.query.filter_by(name=name).first()
            if found_user:
                found_user.tasks = session["tasks"]
            else:
                usr = User(name, session["tasks"])
                db.session.add(usr)
            db.session.commit()
            return redirect(url_for("tasks"))
        
        return render_template("new_task.html")
    
    else:
        return redirect(url_for("login"))

@app.route("/delete_task/<task_to_be_deleted>", methods=["POST", "GET"])
def delete_task(task_to_be_deleted):
    if "user" in session:
        name = session["user"]
        user = db.session.execute(db.select(User).filter_by(name=name)).scalar()
        if request.method == "POST":
            task_to_be_deleted = "|" + task_to_be_deleted + "|"
            user.tasks = user.tasks.replace(task_to_be_deleted, "|", 1)
            if user.tasks == "|":
                user.tasks = ""
            db.session.commit()
            session["tasks"] = session["tasks"].replace(task_to_be_deleted, "|", 1)
            if session["tasks"] == "|":
                session["tasks"] = ""
        return redirect(url_for("tasks"))

    else:
        return redirect(url_for("login"))

@app.route("/delete_all_tasks")
def delete_all_tasks():
    if "user" in session:
        if "tasks" in session:
            User.query.filter_by(tasks=session["tasks"]).delete()
            db.session.commit()
            session.pop("tasks")
        return redirect(url_for("tasks"))
    else:
        return redirect(url_for("login"))






if __name__ == "__main__":
    db.create_all()
    app.run(debug=True)
