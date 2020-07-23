import csv 
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

engine = create_engine(os.getenv('DATABASE_URL'))
db = scoped_session(sessionmaker(bind=engine))

def main():
    f = open("books.csv")
    reader = csv.reader(f)
    for ISBN, bookname, author, publication_year in reader:
        books = db.execute("INSERT INTO books (ISBN, bookname, author, publication_year) VALUES (:ISBN, :bookname, :author, :publication_year)", {"ISBN": ISBN, "bookname": bookname, "author": author, "publication_year": publication_year})
    db.commit()


if __name__ == "__main__":
    main()         