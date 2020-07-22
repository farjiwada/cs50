import os, json


from flask import Flask, render_template, request, session, redirect, flash, url_for, jsonify
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from werkzeug.security import check_password_hash, generate_password_hash
from flask_session import Session
from urllib.parse import unquote
import requests

app = Flask(__name__)
key = os.getenv("GOOD_KEY")
engine = create_engine(os.getenv('DATABASE_URL'))
db = scoped_session(sessionmaker(bind=engine))
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)



@app.route("/")
def index():
    session['user_id']=[]
    return render_template("register.html")

@app.route("/register", methods=['POST', 'GET'])
def register():
    
    if request.method == "POST":
      username = request.form.get("username")
      password = request.form.get("password")
      member = db.execute("SELECT * FROM members WHERE username = :username", {"username": username}).fetchone()
      if not member:
        if not username:
            flash('Enter details correctly!')
            return redirect(url_for('index'))
        if not password:
            flash('Enter details correctly!')
            return redirect(url_for('index'))    
        else:
            db.execute("INSERT INTO members (username, password) VALUES (:username, :password)",{"username": username, "password":generate_password_hash(password)})
            db.commit()
            return render_template("login.html")
      else:
        flash('Already registered !')
        return redirect(url_for('index'))        

    return render_template("login.html")  

@app.route("/login", methods=['POST', 'GET'])
def login():
    
    if request.method == 'POST':
     username = request.form.get("username")
     password = request.form.get("password")
     if not username or not password:
         flash('Enter details correctly!')
         return redirect(url_for('register')) 
     else:     
       member = db.execute("SELECT * FROM members WHERE username = :username", {"username": username}).fetchone()
       session["user_id"] = member['id']
       if member is None:
           flash('User not found!')
           return redirect(url_for('register'))
       elif not check_password_hash(member['password'], password):
           flash('Enter password correctly!') 
           return redirect(url_for('register'))
       else:
           return render_template("front.html")

    return redirect(url_for('register'))

@app.route("/search", methods = ['POST', 'GET'])
def search():

    if request.method == 'POST':   
      search_data ='%'+request.form.get('search_data')+'%'
      if not request.form.get('search_data'):
          flash('Enter a valid character!')
          return redirect(url_for('search'))
      else:  
        books = db.execute("SELECT * FROM books WHERE isbn || bookname || author LIKE :search_data",{"search_data": search_data}).fetchall()
        return render_template("search.html", books=books)
      
    return render_template("front.html")  
        

@app.route("/books/<isbn>")
def book(isbn):
    key = os.getenv("GOOD_KEY")
    books = db.execute("SELECT * FROM books WHERE isbn = :isbn",{"isbn": isbn}).fetchall()
    reviews = db.execute("SELECT username, review, rating, book_id FROM members JOIN reviews ON reviews.user_id=members.id WHERE book_id=:book_id",{"book_id": books[0][0]}).fetchall()
    return render_template("book.html", books=books, reviews=reviews)


@app.route("/reviews/<bookname>", methods = ['POST', 'GET'])
def review(bookname):
    
    if request.method == 'POST':
      review = request.form.get('review')
      rating = request.form.get('rating')
      books = db.execute("SELECT * FROM books WHERE bookname= :bookname",{"bookname": bookname}).fetchone()
      review_check = db.execute("SELECT bookname, user_id FROM books JOIN reviews ON reviews.book_id=books.id WHERE bookname = :bookname",{"bookname": bookname}).fetchall()
   
      for check in review_check:
           if session["user_id"] == check.user_id or not review_check:
             flash('Review aleardy present!')  
             return redirect(url_for('search'))
             break
      else:
           db.execute("INSERT INTO reviews (book_id, review, rating, user_id) VALUES (:book_id, :review, :rating, :user_id)",{"book_id": books['id'], "review": review, "rating": rating, "user_id": session["user_id"]})
           db.commit()
           return redirect(url_for('book',book=books['isbn']))

    return render_template("register.html")


@app.route("/api/<isbn>", methods = ['GET'])
def api(isbn):
    res = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": key, "isbns": isbn})
    if res.status_code != 200:
        return "<h2>404:Error, API not successful!<h2>"

    data = res.json()    
    return data


@app.route("/logout")
def logout():
    if not session['user_id']:
      return '<h1>You haven\'t logged in.</h1>'
    else:
      session.pop('user_id')
      session.clear()
      return '<h1>Successfully logout!</h1>'
      

   
if __name__ == "__main__":
    app.run(debug=True)


