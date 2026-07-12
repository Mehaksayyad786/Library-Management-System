import mysql.connector
from pymongo import MongoClient
from tabulate import tabulate
from datetime import datetime ,timedelta

# ------------------ Helps to generate next id in mongodb ------------------
def get_next_id(collection, id_field):
    last = collection.find_one(sort=[(id_field, -1)])
    return (last[id_field] + 1) if last and id_field in last else 1


# ------------------ DB CONNECTION ------------------
def connect_mysql():
    try:
        return mysql.connector.connect(
            host="localhost",
            user="root",
            password="Sayyadmehak80@",
            database="librarydb"
        )
    except mysql.connector.Error as e:
        print("MySQL Connection Error:", e)
        return None

def connect_mongo():
    try:
        client = MongoClient("mongodb://localhost:27017/")
        return client["librarydb"]
    except Exception as e:
        print("MongoDB Connection Error:", e)
        return None

# ------------------ BUSINESS LOGIC ------------------
def calculate_fine(issue_date, return_date):
    days = (return_date - issue_date).days
    return max(0, (days - 14) * 5)  # ₹5 per day after 14 days

# ------------------ CRUD OPERATIONS ------------------
def add_book(db, db_type):
    try:
        if db_type == "mysql":
            cursor = db.cursor()
            title = input("Enter Title: ")
            author = input("Enter Author: ")
            isbn = input("Enter ISBN: ")
            category = input("Enter Category: ")
            cursor.execute("INSERT INTO books (title, author, isbn, category, available) VALUES (%s,%s,%s,%s,%s)",
                           (title, author, isbn, category, True))
            db.commit()
            print("✅ Book added.")
        else:  # MongoDB
            title = input("Enter Title: ")
            author = input("Enter Author: ")
            isbn = input("Enter ISBN: ")
            category = input("Enter Category: ")
            new_id = get_next_id(db.books, "book_id")
            db.books.insert_one({
                "book_id": new_id,
                "title": title,
                "author": author,
                "isbn": isbn,
                "category": category,
                "available": True
            })
            print("✅ Book added with ID:", new_id)
    except Exception as e:
        print("Error adding book:", e)



def view_books(db, db_type):
    try:
        if db_type == "mysql":
            cursor = db.cursor()
            cursor.execute("SELECT * FROM books")
            rows = cursor.fetchall()
            headers = [i[0] for i in cursor.description]
            print(tabulate(rows, headers=headers, tablefmt="grid"))

        else:  # MongoDB
            books = list(db.books.find({}, {"_id": 0}))  # exclude _id for clarity
            if books:
                print(tabulate(books, headers="keys", tablefmt="grid"))  # ✅ fixed
            else:
                print("No books found.")
    except Exception as e:
        print("Error viewing books:", e)


def issue_book(db, db_type):
    try:
        if db_type == "mysql":
            cursor = db.cursor()
            book_id = int(input("Enter Book ID: "))
            borrower = input("Enter Borrower Name: ")
            cursor.execute("SELECT available FROM books WHERE id=%s", (book_id,))
            result = cursor.fetchone()
            if result and result[0]:
                cursor.execute("UPDATE books SET available=%s WHERE id=%s", (False, book_id))
                cursor.execute("INSERT INTO transactions (book_id, borrower, issue_date, fine) VALUES (%s,%s,CURDATE(),%s)",
                               (book_id, borrower, 0.00))
                db.commit()
                print("✅ Book issued.")
            else:
                print("❌ Book not available!")
        else:  # MongoDB
            book_id = int(input("Enter Book ID: "))
            borrower = input("Enter Borrower Name: ")
            book = db.books.find_one({"book_id": book_id})
            if book and book["available"]:
                db.books.update_one({"book_id": book_id}, {"$set": {"available": False}})
                new_tid = get_next_id(db.transactions, "transaction_id")
                db.transactions.insert_one({
                    "transaction_id": new_tid,
                    "book_id": book_id,
                    "borrower": borrower,
                    "issue_date": datetime.today(),
                    "return_date": None,
                    "fine": 0.00
                })
                print("✅ Book issued with Transaction ID:", new_tid)
            else:
                print("❌ Book not available!")
    except Exception as e:
        print("Error issuing book:", e)


def return_book(db, db_type):
    try:
        if db_type == "mysql":
            cursor = db.cursor()
            tid = int(input("Enter Transaction ID: "))
            cursor.execute("SELECT book_id, issue_date FROM transactions WHERE id=%s AND return_date IS NULL", (tid,))
            result = cursor.fetchone()
            if result:
                book_id, issue_date = result
                cursor.execute("UPDATE books SET available=%s WHERE id=%s", (True, book_id))
                cursor.execute("UPDATE transactions SET return_date=CURDATE(), fine=%s WHERE id=%s",
                               (0.00, tid))
                db.commit()
                print("✅ Book returned.")
            else:
                print("❌ Transaction not found!")
        else:  # MongoDB
            tid = int(input("Enter Transaction ID: "))
            txn = db.transactions.find_one({"transaction_id": tid, "return_date": None})
            if txn:
                db.books.update_one({"book_id": txn["book_id"]}, {"$set": {"available": True}})
                db.transactions.update_one({"transaction_id": tid}, {"$set": {
                    "return_date": datetime.today(),
                    "fine": 0.00
                }})
                print("✅ Book returned.")
            else:
                print("❌ Transaction not found!")
    except Exception as e:
        print("Error returning book:", e)


# ------------------ REPORT FUNCTIONS ------------------

def report_menu(db, db_type):
    while True:
        print("\n--- Reports Menu ---")
        print("1. Books by Category")
        print("2. Issued Books Report")
        print("3. Overdue Books Report")
        print("4. Availability Summary")
        print("5. Back to Main Menu")

        choice = input("Enter choice: ")

        if choice == "1":
            books_by_category(db, db_type)
        elif choice == "2":
            issued_books_report(db, db_type)
        elif choice == "3":
            overdue_books_report(db, db_type)
        elif choice == "4":
            availability_summary(db, db_type)
        elif choice == "5":
            break
        else:
            print("❌ Invalid choice. Try again.")

# ------------------ REPORT FUNCTIONS ------------------
def books_by_category(db, db_type):
    try:
        if db_type == "mysql":
            cursor = db.cursor()
            cursor.execute("SELECT category, COUNT(*) FROM books GROUP BY category")
            rows = cursor.fetchall()
        else:
            pipeline = [{"$group": {"_id": "$category", "count": {"$sum": 1}}}]
            rows = list(db.books.aggregate(pipeline))
            rows = [(r["_id"], r["count"]) for r in rows]
        print(tabulate(rows, headers=["Category","Count"]))
    except Exception as e:
        print("Error generating report:", e)

def issued_books_report(db, db_type):
    try:
        if db_type == "mysql":
            cursor = db.cursor()
            cursor.execute("SELECT t.id, b.title, t.borrower, t.issue_date FROM transactions t JOIN books b ON t.book_id=b.id WHERE t.return_date IS NULL")
            rows = cursor.fetchall()
        else:
            rows = list(db.transactions.find({"return_date": None}, {"_id":0}))
        print(tabulate(rows, headers="keys",tablefmt="grid"))
    except Exception as e:
        print("Error generating report:", e)



def overdue_books_report(db, db_type):
    try:
        if db_type == "mysql":
            cursor = db.cursor()
            cursor.execute("SELECT * FROM transactions WHERE return_date IS NULL AND issue_date < CURDATE() - INTERVAL 14 DAY")
            rows = cursor.fetchall()
            headers = [i[0] for i in cursor.description]
            print(tabulate(rows, headers=headers, tablefmt="grid"))
        else:  # MongoDB
            today = datetime.today()
            cutoff = today - timedelta(days=14)
            overdue = list(db.transactions.find({
                "return_date": None,
                "issue_date": {"$lt": cutoff}
            }, {"_id": 0}))
            if overdue:
                print(tabulate(overdue, headers="keys", tablefmt="grid"))
            else:
                print("✅ No overdue books.")
    except Exception as e:
        print("Error generating report:", e)


def availability_summary(db, db_type):
    try:
        if db_type == "mysql":
            cursor = db.cursor()
            cursor.execute("SELECT COUNT(*) FROM books WHERE available=TRUE")
            available = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM books WHERE available=FALSE")
            issued = cursor.fetchone()[0]
        else:
            available = db.books.count_documents({"available": True})
            issued = db.books.count_documents({"available": False})
        print(tabulate([("Available", available), ("Issued", issued)], headers=["Status","Count"]))
    except Exception as e:
        print("Error generating report:", e)

# ------------------ MAIN MENU UPDATE ------------------
def main():
    print("Choose Database: 1. MySQL  2. MongoDB")
    choice = input("Enter choice: ")
    db_type = "mysql" if choice == "1" else "mongo"

    db = connect_mysql() if db_type == "mysql" else connect_mongo()
    if db is None:
        print("❌ Could not connect to database.")
        return
    if db_type == "mysql":
        setup_mysql()# ✅ creates DB + tables
        db = connect_mysql()
    else:
        setup_mongo(db) # ✅ ensures collections exist

    while True:
        print("\n--- Library Management System ---")
        print("1. Add Book")
        print("2. View Books")
        print("3. Issue Book")
        print("4. Return Book")
        print("5. Reports")
        print("6. Exit")

        option = input("Enter choice: ")

        if option == "1": add_book(db, db_type)
        elif option == "2": view_books(db, db_type)
        elif option == "3": issue_book(db, db_type)
        elif option == "4": return_book(db, db_type)
        elif option == "5": report_menu(db, db_type)
        elif option == "6": break
        else: print("❌ Invalid choice. Try again.")
        

# ------------------ connecting to MySQL ------------------
def setup_mysql():
    try:
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="Sayyadmehak80@",
        
        )
        cursor = conn.cursor()
        cursor.execute("CREATE DATABASE IF NOT EXISTS librarydb")
        cursor.execute("USE librarydb")

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS books (
            id INT PRIMARY KEY AUTO_INCREMENT,
            title VARCHAR(100),
            author VARCHAR(100),
            isbn VARCHAR(20) UNIQUE,
            category VARCHAR(50),
            available BOOLEAN DEFAULT TRUE
        )
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INT PRIMARY KEY AUTO_INCREMENT,
            book_id INT,
            borrower VARCHAR(100),
            issue_date DATE,
            return_date DATE,
            fine DECIMAL(10,2),
            FOREIGN KEY (book_id) REFERENCES books(id)
        )
        """)
        conn.commit()
        print("✅ MySQL setup complete.")
    except Exception as e:
        print("Error setting up MySQL:", e)



# ------------------ connecting to MongoDB ------------------

def setup_mongo(db):
    try:
        db.create_collection("books")
    except:
        pass
    try:
        db.create_collection("transactions")
    except:
        pass
    print("✅ MongoDB setup complete.")





if __name__ == "__main__":
    main()