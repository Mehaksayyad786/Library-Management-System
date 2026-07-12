# 📚 Library Management System

A console‑based Library Management System built with **Python**, supporting both **MySQL (Relational)** and **MongoDB (NoSQL)** backends.  
This project demonstrates database CRUD operations, reporting, and error handling in Python.

---

## 🚀 Features
- Add and view books (title, author, ISBN, category, availability)
- Issue and return books with borrower tracking
- Generate reports:
  - Books by category
  - Issued books report
  - Overdue books report (books issued >14 days ago)
  - Availability summary
- Dual database support: switch between MySQL and MongoDB at runtime
- Error handling for invalid inputs, unavailable books, or missing transactions

---

## ⚙️ Tech Stack
- **Language:** Python 3
- **Databases:** MySQL, MongoDB
- **Libraries:**
  - `mysql-connector-python` → MySQL connectivity
  - `pymongo` → MongoDB connectivity
  - `tabulate` → Tabular report formatting
  - `datetime` → Date/time handling
- **Environment:** VS Code, Command-line interface

