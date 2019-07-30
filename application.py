import os
import requests

from flask import Flask, session, render_template, redirect, request, flash
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

# goodreads KEY
key = "ZxMmcrnrMa7n8bT6kYXFaQ"

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


@app.route("/book", methods=["GET","POST"])
def book():

    if request.method == "POST":
        search = request.form.get("search")


                # return render_template("index.html", )

        if search != "":
            search_result = db.execute("SELECT * FROM books WHERE LOWER(isbn) LIKE :book OR title LIKE :book OR author LIKE :book", {"book": '%'+search+'%'}).fetchall()
            if not search_result:
                message = "No Books ware found. Please search again"
                return render_template("book.html", message=message, search=search)

            for book in search_result:
                isbn = book[1]
                goodreadsapi(isbn)
                # res = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": key, "isbns": isbn})
                # print(res)
                # res = res.json()
                # print(res)
                print(book[1])


            return render_template("book.html", books=search_result, search=search)
        else:
            message =  "Please Enter Search Key."
            return render_template("index.html", message=message)




    else:
        return redirect("/")

@app.route("/book/<string:isbn_book>", methods=["GET","POST"])
def book_detail(isbn_book):
    if request.method == "GET":
        rating_detail = []

        book = db.execute("SELECT isbn FROM books WHERE isbn = :isbn_book", { "isbn_book": isbn_book }).fetchone()
        # print(book)
        # check if book is exisr or no
        if book:
            res = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": key, "isbns": isbn_book})
            if res.status_code == 200:
                res = res.json()
                res_book_goodreads = res["books"][0]

                isbn13 = res_book_goodreads["isbn13"]
                avg_rating = res_book_goodreads["average_rating"]
                reviews_count = res_book_goodreads["reviews_count"]

                db.execute("UPDATE books SET average_score = :average_score, reviews_count = :review_count, isbn13 = :isbn13  WHERE isbn =:isbn",{"average_score":avg_rating, "review_count": reviews_count, "isbn13":isbn13, "isbn": isbn_book})
                db.commit()
                # print(res_book_goodreads)
            book_detail = db.execute("SELECT * FROM books WHERE isbn = :isbn_book", { "isbn_book": isbn_book }).fetchone()
            # review = db.execute("SELECT * FROM reviews WHERE isbn = :isbn", { "isbn": book[1] }).fetchall()
            reviews = db.execute("SELECT reviews.*, users.name FROM reviews INNER JOIN users ON reviews.user_id = users.id WHERE isbn = :isbn", { "isbn": isbn_book }).fetchall()
            star_and_avg_count = {}
            if reviews :
                rating_detail = db.execute("SELECT AVG(rating), COUNT(*) FROM reviews WHERE isbn = :isbn", { "isbn": isbn_book }).fetchone()
            # print(rating_detail)
                star_and_avg_count = {"avg1":[], "avg2":[], "avg3":[], "avg4":[], "avg5":[]}

                for review in reviews:
                    print(round(review[3]))
                    if round(review[3]) == 5:
                        star_and_avg_count["avg5"].append(review[3])
                    elif  round(review[3]) == 4:
                        # star_and_avg_count["s4"] +=1
                        star_and_avg_count["avg4"].append(review[3])
                    elif  round(review[3]) == 3:
                        # star_and_avg_count["s3"] +=1
                        star_and_avg_count["avg3"].append(review[3])
                    elif  round(review[3]) == 2:
                        # star_and_avg_count["s2"] +=1
                        star_and_avg_count["avg2"].append(review[3])
                    elif  round(review[3]) == 1:
                        # star_and_avg_count["s1"] +=1
                        star_and_avg_count["avg1"].append(review[3])
                print(star_and_avg_count)
            return render_template("book.html", book_detail=book_detail, reviews=reviews, rating_detail=rating_detail, star_val=star_and_avg_count)
        else:
            return redirect("/error/404")

    if request.method == "POST":
        isbn_review = request.form.get("book_id_review")
        book_id_review = request.form.get("book_id")

        rating = request.form.get("rating")
        review = request.form.get("review")
        message = ""
        if isbn_review or rating or review:
            # check if entry exist
            result = db.execute("SELECT * FROM reviews WHERE isbn = :isbn AND user_id = :user ",{"isbn":isbn_review, "user": session["user_id"] }).fetchone()

            if not result:
                db.execute("INSERT INTO reviews (isbn, user_id, rating, rating_text) VALUES (:isbn, :user_id, :rating, :review)",{"isbn":isbn_review, "user_id": session["user_id"], "rating": rating, "review": review})
                db.commit()
            else:
                db.execute("UPDATE reviews SET rating = :rating , rating_text =:text WHERE id =:id",{"rating": rating, "text": review, "id": result[0]})
                db.commit()
            return redirect("/book/"+isbn_review)



@app.route("/api/<string:isbn>", methods=["GET"])
def goodreadsapi(isbn):

    if request.method == "GET":
        res = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": key, "isbns": isbn})
        print(res)
        if res.status_code == 200:
            res = res.json()
        print(res)
        """
        {'books':
            [{
            'id': 846984,
            'isbn': '0375913750',
            'isbn13': '9780375913754',
            'ratings_count': 34899,
            'reviews_count': 57730,
            'text_reviews_count': 2773
            'work_ratings_count': 37040,
            'work_reviews_count': 61709,
            'work_text_reviews_count': 3083,
            'average_rating': '3.82',
            }]
        }

        """
        return redirect("")
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
