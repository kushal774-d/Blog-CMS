# Blog CMS (MSSQL Edition)

A modern, fast, and beautiful Content Management System (CMS) platform built with Python (Flask) and connected to Microsoft SQL Server (MSSQL), featuring a dark-themed glassmorphism UI using HTML and Vanilla CSS.

## Prerequisites
- Python 3.7+ installed.
- Microsoft SQL Server installed (e.g. SQL Server Express).
- `ODBC Driver 17 for SQL Server` installed in Windows.

## Setup Instructions

1. **Configure your Database connection**
Open `app.py` in your text editor. At the top of the file, search for the `CONNECTION_STRING` variable.
Update the properties to match your MSSQL environment:
- `Server`: e.g., `localhost\SQLEXPRESS` or `.` 
- `Database`: Provide a database name you want to use.

2. **Install required dependencies**
Run the following command in the termial:
```bash
pip install -r requirements.txt
```

3. **Start the application**
Run the Flask server:
```bash
python app.py
```
*(If the connection string is correct, you will see a success message about DB initialization in the terminal).*

4. **View the Website**
Open your browser and navigate to:
[http://127.0.0.1:5000](http://127.0.0.1:5000)

5. **Access the Admin Dashboard**
Click on **Dashboard** in the top navigation or navigate to:
[http://127.0.0.1:5000/admin](http://127.0.0.1:5000/admin) to start writing your first post!
