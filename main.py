from flask import render_template, Flask, request, redirect, url_for, session, flash
import datetime as dt
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.secret_key = "SDFKLJASDADS"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///users.sqlite3"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.permanent_session_lifetime = dt.timedelta(minutes=30)

db = SQLAlchemy(app)
app.app_context().push()

class User(db.Model):
    username = db.Column(db.String(30), primary_key=True)
    password = db.Column(db.String(20), nullable=False)
    tasks = db.relationship("Task", backref="user", cascade="all, delete-orphan")

    def __init__(self, username, password):
        self.username = username
        self.password = password

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    content = db.Column(db.String(40), nullable=False)
    date_created = db.Column(db.DateTime, nullable=False, default=dt.datetime.now())
    user_username = db.Column(db.Integer, db.ForeignKey("user.username"), nullable=False)

    def __init__(self, content, user_username):
        self.content = content
        self.user_username = user_username



@app.route("/register", methods=["POST", "GET"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        if len(username) < 8:
            flash("Username should be at least 8 characters long.")
        elif len(password) < 4:
            flash("Password should be at least 4 characters long.")
        else:
            user = User(username, password)
            try:
                db.session.add(user)
                db.session.commit()
                return redirect(url_for("login"))
            except:
                flash("This username already exists!")
        
    elif "user" in session:
        return redirect("tasks")

    return render_template("register.html")

@app.route("/", methods=["POST", "GET"])
@app.route("/login", methods=["POST", "GET"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        try:
            user = db.session.execute(db.select(User).filter_by(username=username, password=password)).scalar_one()
            session["user"] = user.username
            session.permanent = True
            return redirect(url_for("tasks"))
        except:
            flash("Your username or password is incorrect.")      
        
    elif "user" in session:
        return redirect(url_for("tasks"))

    return render_template("login.html")

@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("login"))

@app.route("/tasks")
def tasks():
    if "user" in session:
        username = session["user"]
        tasks = db.session.execute(db.select(Task).filter_by(user_username=username)).scalars()

        exists = db.session.execute(db.select(Task).filter_by(user_username=username)).first()
        if not exists:
            flash("You do not have any task.")

        return render_template("tasks.html", username=username, tasks=tasks)

    else:
        return redirect(url_for("login"))
        

@app.route("/new_task", methods=["POST", "GET"])
def new_task():
    if "user" in session:
        username = session["user"]

        if request.method == "POST":
            content = request.form["content"]

            if len(content) == 0:
                flash("Please enter a proper task!")
            elif len(content) > 40:
                flash("A task can be at most 40 characters long.")
            else:    
                task = Task(content=content, user_username=username)
                db.session.add(task)
                db.session.commit()

                return redirect(url_for("tasks"))
    
    else:
        return redirect(url_for("login"))
    
    return render_template("new_task.html")

@app.route("/<task_id>/delete_task", methods=["POST", "GET"])
def delete_task(task_id):
    if "user" in session:
        if request.method == "POST":
            task = db.session.execute(db.select(Task).filter_by(id=task_id)).scalar_one()
            db.session.delete(task)
            db.session.commit()

        return redirect(url_for("tasks"))

    else:
        return redirect(url_for("login"))

@app.route("/delete_all_tasks")
def delete_all_tasks():
    if "user" in session:
        username = session["user"]

        try:
            tasks = db.session.execute(db.select(Task).filter_by(user_username=username)).scalars()

            for task in tasks:
                db.session.delete(task)
            db.session.commit()
            
        finally:
            return redirect(url_for("tasks"))
    
    else:
        return redirect(url_for("login"))
    
@app.route("/delete_account")
def delete_account():
    if "user" in session:
        username = session["user"]
        user = db.session.execute(db.select(User).filter_by(username=username)).scalar_one()
        db.session.delete(user)
        db.session.commit()
        session.pop("user", None)

    return redirect(url_for("login"))



if __name__ == "__main__":
    db.create_all()
    app.run(debug=True)
