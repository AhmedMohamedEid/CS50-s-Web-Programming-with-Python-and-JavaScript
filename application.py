import os

from flask import Flask, session,render_template,redirect, request
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

from functools import wraps
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function

#######  Route #########
  # Home Page #
@app.route("/", methods=["POST", "GET"])
@login_required
def index():
    return render_template("index.html")


    # User Register Page #
@app.route("/registration", methods=['GET','POST'])
def register_page():

    if request.method == 'POST':
        name = request.form.get("name")
        email = request.form.get("email")
        password = generate_password_hash(request.form.get("password"))
        print (password)
        if db.execute("SELECT email FROM users WHERE email = :email", {"email": email}).rowcount == 0:
            db.execute("INSERT INTO users (name, email, password) VALUES(:name, :email, :password)", {"name":name, "email": email,"password":password})
            db.commit()

            # Get Username to store Session
            user = db.execute("SELECT id FROM users WHERE email = :email",{"email":email}).fetchone()
            session['user_id'] = user[0]
            # session['username'] = user[1]
            # redirect to Home
            return redirect("/")
    else:
        message = "Invalid Register"
        return render_template("register.html", message=message)



@app.route("/login", methods=['GET','POST'])
def login_page():
    # Forget All Session_id
    session.clear()

    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        print(password)
        # hash_password = generate_password_hash(password)
        # print(hash_password)
        result = db.execute("SELECT * FROM users WHERE email = :email",{"email":email}).fetchone()
        print(result)
        print(result[3])
        if result:
            # session["user_id"] = result[0]
            # session["user_name"] = result[1]
            # return redirect("/")
            print(check_password_hash(result[3], password))
            return render_template("login.html")
        else:
            print("Error")
            return render_template("login.html")
    else:
        return render_template("login.html")


@app.route("/logout")
def logout_page():

    # remove session_id
    session.clear()
    return redirect("/")
# @app.route("register")
