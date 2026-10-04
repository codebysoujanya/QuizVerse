import sqlite3
from werkzeug.security import generate_password_hash

DATABASE = "quizverse.db"


def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def column_exists(conn, table, column):
    columns = conn.execute(
        f"PRAGMA table_info({table})"
    ).fetchall()

    return any(row["name"] == column for row in columns)


def add_column_if_missing(conn, table, column, definition):
    if not column_exists(conn, table, column):
        conn.execute(
            f"ALTER TABLE {table} ADD COLUMN {column} {definition}"
        )


def create_tables():

    conn = get_db()

    # ==========================================
    # USERS
    # ==========================================

    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT DEFAULT 'student',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # ==========================================
    # QUESTIONS
    # ==========================================

    conn.execute("""
        CREATE TABLE IF NOT EXISTS questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question TEXT NOT NULL,
            option_a TEXT NOT NULL,
            option_b TEXT NOT NULL,
            option_c TEXT NOT NULL,
            option_d TEXT NOT NULL,
            correct_answer TEXT NOT NULL,
            category TEXT NOT NULL,
            difficulty TEXT DEFAULT 'Easy',
            explanation TEXT DEFAULT ''
        )
    """)

    # ==========================================
    # RESULTS
    # ==========================================

    conn.execute("""
        CREATE TABLE IF NOT EXISTS results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            score INTEGER NOT NULL,
            total INTEGER NOT NULL,
            percentage REAL NOT NULL,
            category TEXT DEFAULT 'General',
            difficulty TEXT DEFAULT 'Easy',
            xp INTEGER DEFAULT 0,
            submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # ==========================================
    # ATTEMPT ANSWERS
    # ==========================================

    conn.execute("""
        CREATE TABLE IF NOT EXISTS attempt_answers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            attempt_id INTEGER NOT NULL,
            question_id INTEGER NOT NULL,
            selected_answer TEXT,
            correct_answer TEXT NOT NULL,
            is_correct INTEGER DEFAULT 0
        )
    """)

    # ==========================================
    # MIGRATION FOR OLD DATABASE
    # ==========================================

    add_column_if_missing(
        conn,
        "questions",
        "difficulty",
        "TEXT DEFAULT 'Easy'"
    )

    add_column_if_missing(
        conn,
        "questions",
        "explanation",
        "TEXT DEFAULT ''"
    )

    add_column_if_missing(
        conn,
        "results",
        "category",
        "TEXT DEFAULT 'General'"
    )

    add_column_if_missing(
        conn,
        "results",
        "difficulty",
        "TEXT DEFAULT 'Easy'"
    )

    add_column_if_missing(
        conn,
        "results",
        "xp",
        "INTEGER DEFAULT 0"
    )

    # ==========================================
    # ADMIN ACCOUNT
    # ==========================================

    admin = conn.execute(
        "SELECT id FROM users WHERE username = ?",
        ("admin",)
    ).fetchone()

    if not admin:

        conn.execute("""
            INSERT INTO users
            (name, username, password, role)
            VALUES (?, ?, ?, ?)
        """, (
            "QuizVerse Administrator",
            "admin",
            generate_password_hash("admin123"),
            "admin"
        ))

    conn.commit()
    conn.close()


def seed_questions():

    conn = get_db()

    count = conn.execute(
        "SELECT COUNT(*) AS count FROM questions"
    ).fetchone()["count"]

    # Do not duplicate questions
    if count > 0:
        conn.close()
        return

    questions = [

        # ==========================================
        # PYTHON
        # ==========================================

        (
            "Which keyword is used to define a function in Python?",
            "function",
            "def",
            "define",
            "func",
            "B",
            "Python",
            "Easy",
            "Python uses the def keyword to define a function."
        ),

        (
            "Which data type is immutable in Python?",
            "List",
            "Dictionary",
            "Set",
            "Tuple",
            "D",
            "Python",
            "Easy",
            "Python tuples are immutable collections."
        ),

        (
            "Which symbol is used for comments in Python?",
            "//",
            "#",
            "/*",
            "--",
            "B",
            "Python",
            "Easy",
            "Python uses # for single-line comments."
        ),

        (
            "What is the output type of range(5)?",
            "List",
            "Tuple",
            "Range object",
            "Set",
            "C",
            "Python",
            "Medium",
            "range() returns a range object."
        ),

        (
            "Which library is commonly used for data analysis?",
            "NumPy",
            "Pandas",
            "Flask",
            "Socket",
            "B",
            "Python",
            "Easy",
            "Pandas is widely used for data manipulation and analysis."
        ),

        (
            "Which keyword handles exceptions?",
            "catch",
            "error",
            "try",
            "exception",
            "C",
            "Python",
            "Easy",
            "Python uses try and except for exception handling."
        ),

        (
            "What does len() return?",
            "Memory size",
            "Number of elements",
            "Data type",
            "Index",
            "B",
            "Python",
            "Easy",
            "len() returns the number of elements in a collection."
        ),

        (
            "Which collection stores key-value pairs?",
            "List",
            "Tuple",
            "Dictionary",
            "Set",
            "C",
            "Python",
            "Easy",
            "Dictionaries store data using key-value pairs."
        ),

        # ==========================================
        # JAVA
        # ==========================================

        (
            "Which keyword creates an object in Java?",
            "create",
            "object",
            "new",
            "instance",
            "C",
            "Java",
            "Easy",
            "The new keyword creates an object."
        ),

        (
            "Which method is the entry point of a Java program?",
            "start()",
            "main()",
            "run()",
            "execute()",
            "B",
            "Java",
            "Easy",
            "Java applications normally start execution from main()."
        ),

        (
            "Which concept allows one class to acquire another class's properties?",
            "Encapsulation",
            "Inheritance",
            "Abstraction",
            "Polymorphism",
            "B",
            "Java",
            "Easy",
            "Inheritance allows a class to inherit properties and methods."
        ),

        (
            "Which keyword prevents a class from being inherited?",
            "static",
            "private",
            "final",
            "protected",
            "C",
            "Java",
            "Medium",
            "A final class cannot be extended."
        ),

        (
            "Which principle hides implementation details?",
            "Inheritance",
            "Abstraction",
            "Compilation",
            "Execution",
            "B",
            "Java",
            "Medium",
            "Abstraction hides implementation details and exposes essential behavior."
        ),

        (
            "Which keyword is used to inherit a class?",
            "inherits",
            "extends",
            "implements",
            "super",
            "B",
            "Java",
            "Easy",
            "extends is used for class inheritance."
        ),

        # ==========================================
        # WEB
        # ==========================================

        (
            "What does HTML stand for?",
            "Hyper Text Markup Language",
            "High Text Machine Language",
            "Hyperlink Text Management Language",
            "Home Tool Markup Language",
            "A",
            "Web",
            "Easy",
            "HTML stands for Hyper Text Markup Language."
        ),

        (
            "Which language is used to style web pages?",
            "HTML",
            "Python",
            "CSS",
            "SQL",
            "C",
            "Web",
            "Easy",
            "CSS controls the presentation and styling of web pages."
        ),

        (
            "Which language provides browser-side programming?",
            "SQL",
            "JavaScript",
            "PHP",
            "C",
            "B",
            "Web",
            "Easy",
            "JavaScript is commonly used for client-side web programming."
        ),

        (
            "Which HTML tag creates a hyperlink?",
            "<link>",
            "<a>",
            "<href>",
            "<url>",
            "B",
            "Web",
            "Easy",
            "The anchor tag creates hyperlinks."
        ),

        (
            "Which HTTP method is commonly used to submit form data?",
            "GET",
            "POST",
            "SEND",
            "PUSH",
            "B",
            "Web",
            "Easy",
            "POST is commonly used to submit data to a server."
        ),

        (
            "Which status code means Not Found?",
            "200",
            "301",
            "404",
            "500",
            "C",
            "Web",
            "Easy",
            "HTTP 404 indicates that the requested resource was not found."
        ),

        # ==========================================
        # DATABASE
        # ==========================================

        (
            "What does SQL stand for?",
            "Structured Query Language",
            "Simple Query Language",
            "System Query Logic",
            "Structured Question Language",
            "A",
            "Database",
            "Easy",
            "SQL stands for Structured Query Language."
        ),

        (
            "Which command is used to retrieve data?",
            "GET",
            "SELECT",
            "FETCH",
            "READ",
            "B",
            "Database",
            "Easy",
            "SELECT retrieves data from database tables."
        ),

        (
            "Which key uniquely identifies a row?",
            "Foreign Key",
            "Primary Key",
            "Candidate Value",
            "Unique Column",
            "B",
            "Database",
            "Easy",
            "A primary key uniquely identifies each record."
        ),

        (
            "Which SQL command removes a table?",
            "DELETE TABLE",
            "DROP TABLE",
            "REMOVE TABLE",
            "CLEAR TABLE",
            "B",
            "Database",
            "Medium",
            "DROP TABLE removes a table structure."
        ),

        (
            "Which clause filters records?",
            "FILTER",
            "WHERE",
            "HAVING",
            "CHECK",
            "B",
            "Database",
            "Easy",
            "WHERE filters rows based on a condition."
        ),

        (
            "Which command modifies existing records?",
            "CHANGE",
            "MODIFY",
            "UPDATE",
            "ALTER",
            "C",
            "Database",
            "Easy",
            "UPDATE modifies existing records."
        ),

        # ==========================================
        # APTITUDE
        # ==========================================

        (
            "What is 20% of 250?",
            "25",
            "40",
            "50",
            "60",
            "C",
            "Aptitude",
            "Easy",
            "20% of 250 is 50."
        ),

        (
            "If a number is doubled and becomes 40, what was the number?",
            "10",
            "20",
            "30",
            "40",
            "B",
            "Aptitude",
            "Easy",
            "40 divided by 2 equals 20."
        ),

        (
            "What is the average of 10, 20 and 30?",
            "15",
            "20",
            "25",
            "30",
            "B",
            "Aptitude",
            "Easy",
            "Average = (10 + 20 + 30) / 3 = 20."
        ),

        (
            "A train travels 60 km in 1 hour. What is its speed?",
            "30 km/h",
            "45 km/h",
            "60 km/h",
            "90 km/h",
            "C",
            "Aptitude",
            "Easy",
            "Speed = Distance / Time = 60 km/h."
        ),

        (
            "If CP is ₹100 and SP is ₹120, profit percentage is?",
            "10%",
            "15%",
            "20%",
            "25%",
            "C",
            "Aptitude",
            "Medium",
            "Profit percentage = (20/100) × 100 = 20%."
        ),

        # ==========================================
        # DATA SCIENCE
        # ==========================================

        (
            "Which Python library is mainly used for numerical arrays?",
            "Flask",
            "NumPy",
            "Django",
            "BeautifulSoup",
            "B",
            "Data Science",
            "Easy",
            "NumPy provides powerful numerical array operations."
        ),

        (
            "Which library is widely used for data manipulation?",
            "Pandas",
            "React",
            "Express",
            "Socket.IO",
            "A",
            "Data Science",
            "Easy",
            "Pandas is widely used for data manipulation and analysis."
        ),

        (
            "What does ML stand for?",
            "Machine Learning",
            "Model Logic",
            "Memory Language",
            "Machine Logic",
            "A",
            "Data Science",
            "Easy",
            "ML stands for Machine Learning."
        ),

        (
            "Which algorithm is commonly used for classification?",
            "Linear Regression",
            "Logistic Regression",
            "K-Means only",
            "PCA",
            "B",
            "Data Science",
            "Medium",
            "Logistic Regression is commonly used for classification."
        ),

        (
            "Which metric measures the proportion of correct predictions?",
            "Recall",
            "Precision",
            "Accuracy",
            "F1",
            "C",
            "Data Science",
            "Easy",
            "Accuracy is the proportion of correct predictions."
        ),

        (
            "What is overfitting?",
            "Model performs well only on training data",
            "Model has no data",
            "Model trains instantly",
            "Model has no features",
            "A",
            "Data Science",
            "Medium",
            "Overfitting occurs when a model learns training data too closely."
        )
    ]

    conn.executemany("""
        INSERT INTO questions
        (
            question,
            option_a,
            option_b,
            option_c,
            option_d,
            correct_answer,
            category,
            difficulty,
            explanation
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, questions)

    conn.commit()
    conn.close()


def initialize_database():
    create_tables()
    seed_questions()


if __name__ == "__main__":
    initialize_database()
    print("QuizVerse database initialized successfully.")