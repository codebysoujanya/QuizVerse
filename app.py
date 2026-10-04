import os
import random
import sqlite3
from functools import wraps
from datetime import datetime

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash,
    send_file
)

from flask_socketio import SocketIO

from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

from database import (
    get_db,
    initialize_database
)


# =========================================================
# APP CONFIGURATION
# =========================================================

app = Flask(__name__)

app.secret_key = os.environ.get(
    "SECRET_KEY",
    "quizverse-secret-key-change-this"
)

socketio = SocketIO(
    app,
    cors_allowed_origins="*"
)


# =========================================================
# INITIALIZE DATABASE
# =========================================================

initialize_database()


# =========================================================
# CONSTANTS
# =========================================================

QUESTIONS_PER_EXAM = 10

DIFFICULTIES = [
    "Easy",
    "Medium",
    "Hard"
]


# =========================================================
# LOGIN DECORATOR
# =========================================================

def login_required(function):

    @wraps(function)
    def decorated_function(*args, **kwargs):

        if "username" not in session:

            flash(
                "Please login to continue.",
                "warning"
            )

            return redirect(
                url_for("login")
            )

        return function(*args, **kwargs)

    return decorated_function


# =========================================================
# ADMIN DECORATOR
# =========================================================

def admin_required(function):

    @wraps(function)
    def decorated_function(*args, **kwargs):

        if "username" not in session:

            flash(
                "Please login first.",
                "warning"
            )

            return redirect(
                url_for("login")
            )

        if session.get("role") != "admin":

            flash(
                "Administrator access required.",
                "danger"
            )

            return redirect(
                url_for("dashboard")
            )

        return function(*args, **kwargs)

    return decorated_function


# =========================================================
# HOME
# =========================================================

@app.route("/")
def index():

    conn = get_db()

    question_count = conn.execute("""
        SELECT COUNT(*) AS count
        FROM questions
    """).fetchone()["count"]

    category_count = conn.execute("""
        SELECT COUNT(DISTINCT category) AS count
        FROM questions
    """).fetchone()["count"]

    student_count = conn.execute("""
        SELECT COUNT(*) AS count
        FROM users
        WHERE role = 'student'
    """).fetchone()["count"]

    attempt_count = conn.execute("""
        SELECT COUNT(*) AS count
        FROM results
    """).fetchone()["count"]

    conn.close()

    return render_template(
        "index.html",
        question_count=question_count,
        category_count=category_count,
        student_count=student_count,
        attempt_count=attempt_count
    )


# =========================================================
# REGISTER
# =========================================================

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        name = request.form.get("name", "").strip()
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        confirm_password = request.form.get(
            "confirm_password",
            ""
        )

        if not name or not username or not password:

            flash(
                "Please fill all required fields.",
                "danger"
            )

            return redirect(
                url_for("register")
            )

        if len(password) < 6:

            flash(
                "Password must contain at least 6 characters.",
                "danger"
            )

            return redirect(
                url_for("register")
            )

        if password != confirm_password:

            flash(
                "Passwords do not match.",
                "danger"
            )

            return redirect(
                url_for("register")
            )

        conn = get_db()

        existing_user = conn.execute(
            """
            SELECT id
            FROM users
            WHERE username = ?
            """,
            (username,)
        ).fetchone()

        if existing_user:

            conn.close()

            flash(
                "Username already exists.",
                "danger"
            )

            return redirect(
                url_for("register")
            )

        password_hash = generate_password_hash(
            password
        )

        conn.execute(
            """
            INSERT INTO users
            (name, username, password, role)
            VALUES (?, ?, ?, ?)
            """,
            (
                name,
                username,
                password_hash,
                "student"
            )
        )

        conn.commit()
        conn.close()

        flash(
            "Registration successful. Please login.",
            "success"
        )

        return redirect(
            url_for("login")
        )

    return render_template("register.html")


# =========================================================
# LOGIN
# =========================================================

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form.get(
            "username",
            ""
        ).strip()

        password = request.form.get(
            "password",
            ""
        )

        conn = get_db()

        user = conn.execute(
            """
            SELECT *
            FROM users
            WHERE username = ?
            """,
            (username,)
        ).fetchone()

        conn.close()

        if user and check_password_hash(
            user["password"],
            password
        ):

            session.clear()

            session["user_id"] = user["id"]
            session["username"] = user["username"]
            session["name"] = user["name"]
            session["role"] = user["role"]

            flash(
                f"Welcome back, {user['name']}!",
                "success"
            )

            if user["role"] == "admin":

                return redirect(
                    url_for("admin")
                )

            return redirect(
                url_for("dashboard")
            )

        flash(
            "Invalid username or password.",
            "danger"
        )

    return render_template("login.html")


# =========================================================
# LOGOUT
# =========================================================

@app.route("/logout")
def logout():

    session.clear()

    flash(
        "You have been logged out successfully.",
        "success"
    )

    return redirect(
        url_for("index")
    )


# =========================================================
# DASHBOARD
# =========================================================

@app.route("/dashboard")
@login_required
def dashboard():

    username = session["username"]

    conn = get_db()

    attempts = conn.execute(
        """
        SELECT *
        FROM results
        WHERE username = ?
        ORDER BY submitted_at DESC
        """,
        (username,)
    ).fetchall()

    questions_count = conn.execute(
        """
        SELECT COUNT(*) AS count
        FROM questions
        """
    ).fetchone()["count"]

    attempts_count = len(attempts)

    if attempts:

        best_percentage = max(
            float(attempt["percentage"])
            for attempt in attempts
        )

        average_percentage = round(
            sum(
                float(attempt["percentage"])
                for attempt in attempts
            ) / attempts_count,
            1
        )

        total_xp = sum(
            int(attempt["xp"] or 0)
            for attempt in attempts
        )

    else:

        best_percentage = 0
        average_percentage = 0
        total_xp = 0

    level = (total_xp // 100) + 1

    progress_xp = total_xp % 100

    conn.close()

    return render_template(
        "dashboard.html",
        attempts=attempts,
        questions_count=questions_count,
        attempts_count=attempts_count,
        best_percentage=best_percentage,
        average_percentage=average_percentage,
        total_xp=total_xp,
        level=level,
        progress_xp=progress_xp
    )


# =========================================================
# SELECT DOMAIN / START EXAM
# =========================================================

@app.route("/exam")
@login_required
def exam():

    domain = request.args.get("domain")
    difficulty = request.args.get(
        "difficulty",
        "All"
    )

    conn = get_db()

    categories = conn.execute(
        """
        SELECT category,
               COUNT(*) AS question_count
        FROM questions
        GROUP BY category
        ORDER BY category
        """
    ).fetchall()

    # If no domain selected
    if not domain:

        conn.close()

        return render_template(
            "select_domain.html",
            categories=categories,
            difficulties=DIFFICULTIES
        )

    # Validate difficulty
    if difficulty not in DIFFICULTIES:

        difficulty = "All"

    # ==========================================
    # BUILD QUERY
    # ==========================================

    if difficulty == "All":

        questions = conn.execute(
            """
            SELECT *
            FROM questions
            WHERE category = ?
            ORDER BY RANDOM()
            LIMIT ?
            """,
            (
                domain,
                QUESTIONS_PER_EXAM
            )
        ).fetchall()

    else:

        questions = conn.execute(
            """
            SELECT *
            FROM questions
            WHERE category = ?
            AND difficulty = ?
            ORDER BY RANDOM()
            LIMIT ?
            """,
            (
                domain,
                difficulty,
                QUESTIONS_PER_EXAM
            )
        ).fetchall()

    conn.close()

    # ==========================================
    # NOT ENOUGH QUESTIONS
    # ==========================================

    if len(questions) == 0:

        flash(
            "No questions are available for this domain and difficulty.",
            "warning"
        )

        return redirect(
            url_for("exam")
        )

    # ==========================================
    # SAVE EXAM SESSION
    # ==========================================

    session["exam_question_ids"] = [
        question["id"]
        for question in questions
    ]

    session["exam_domain"] = domain
    session["exam_difficulty"] = difficulty
    session["exam_started_at"] = datetime.now().timestamp()

    # Time limit
    if difficulty == "Easy":
        time_limit = 10

    elif difficulty == "Medium":
        time_limit = 12

    elif difficulty == "Hard":
        time_limit = 15

    else:
        time_limit = 12

    return render_template(
        "exam.html",
        questions=questions,
        domain=domain,
        difficulty=difficulty,
        time_limit=time_limit
    )


# =========================================================
# SUBMIT EXAM
# =========================================================

@app.route("/submit-exam", methods=["POST"])
@login_required
def submit_exam():

    question_ids = session.get(
        "exam_question_ids"
    )

    if not question_ids:

        flash(
            "Your exam session has expired. Please start again.",
            "warning"
        )

        return redirect(
            url_for("exam")
        )

    domain = session.get(
        "exam_domain",
        "General"
    )

    difficulty = session.get(
        "exam_difficulty",
        "All"
    )

    username = session["username"]

    conn = get_db()

    # ==========================================
    # FETCH QUESTIONS
    # ==========================================

    placeholders = ",".join(
        "?" for _ in question_ids
    )

    rows = conn.execute(
        f"""
        SELECT *
        FROM questions
        WHERE id IN ({placeholders})
        """,
        question_ids
    ).fetchall()

    question_map = {
        question["id"]: question
        for question in rows
    }

    score = 0
    review = []

    # ==========================================
    # CHECK ANSWERS
    # ==========================================

    for question_id in question_ids:

        question = question_map.get(
            question_id
        )

        if not question:
            continue

        selected_answer = request.form.get(
            f"question_{question_id}"
        )

        correct_answer = question[
            "correct_answer"
        ]

        is_correct = (
            selected_answer == correct_answer
        )

        if is_correct:
            score += 1

        review.append({
            "question": question["question"],
            "option_a": question["option_a"],
            "option_b": question["option_b"],
            "option_c": question["option_c"],
            "option_d": question["option_d"],
            "selected_answer": selected_answer,
            "correct_answer": correct_answer,
            "explanation": question["explanation"],
            "is_correct": is_correct
        })

    total = len(question_ids)

    percentage = round(
        (score / total) * 100,
        2
    ) if total else 0

    # ==========================================
    # XP CALCULATION
    # ==========================================

    xp = score * 10

    # Difficulty bonus
    if difficulty == "Medium":
        xp += score * 3

    elif difficulty == "Hard":
        xp += score * 5

    # Perfect score bonus
    if score == total and total > 0:
        xp += 25

    # ==========================================
    # PERFORMANCE MESSAGE
    # ==========================================

    if percentage >= 90:

        feedback = (
            "Outstanding! You have demonstrated excellent "
            "understanding of this domain."
        )

    elif percentage >= 75:

        feedback = (
            "Excellent work! Your technical fundamentals "
            "are looking strong."
        )

    elif percentage >= 60:

        feedback = (
            "Good performance! Keep practicing to strengthen "
            "your knowledge."
        )

    elif percentage >= 50:

        feedback = (
            "You passed, but there are areas that need "
            "more practice."
        )

    else:

        feedback = (
            "Keep learning! Review the explanations and "
            "try another assessment."
        )

    # ==========================================
    # SAVE RESULT
    # ==========================================

    cursor = conn.execute(
        """
        INSERT INTO results
        (
            username,
            score,
            total,
            percentage,
            category,
            difficulty,
            xp
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            username,
            score,
            total,
            percentage,
            domain,
            difficulty,
            xp
        )
    )

    attempt_id = cursor.lastrowid

    # ==========================================
    # SAVE INDIVIDUAL ANSWERS
    # ==========================================

    for question_id in question_ids:

        question = question_map.get(
            question_id
        )

        if not question:
            continue

        selected_answer = request.form.get(
            f"question_{question_id}"
        )

        correct_answer = question[
            "correct_answer"
        ]

        is_correct = (
            selected_answer == correct_answer
        )

        conn.execute(
            """
            INSERT INTO attempt_answers
            (
                attempt_id,
                question_id,
                selected_answer,
                correct_answer,
                is_correct
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                attempt_id,
                question_id,
                selected_answer,
                correct_answer,
                int(is_correct)
            )
        )

    conn.commit()
    conn.close()

    # ==========================================
    # CLEAR EXAM SESSION
    # ==========================================

    session.pop("exam_question_ids", None)
    session.pop("exam_domain", None)
    session.pop("exam_difficulty", None)
    session.pop("exam_started_at", None)

    return render_template(
        "result.html",
        score=score,
        total=total,
        percentage=percentage,
        category=domain,
        difficulty=difficulty,
        xp=xp,
        feedback=feedback,
        review=review,
        attempt_id=attempt_id
    )


# =========================================================
# CERTIFICATE
# =========================================================

@app.route("/certificate/<int:attempt_id>")
@login_required
def certificate(attempt_id):

    username = session["username"]

    conn = get_db()

    result = conn.execute(
        """
        SELECT *
        FROM results
        WHERE id = ?
        AND username = ?
        """,
        (
            attempt_id,
            username
        )
    ).fetchone()

    conn.close()

    if not result:

        flash(
            "Certificate not found.",
            "danger"
        )

        return redirect(
            url_for("dashboard")
        )

    if result["percentage"] < 50:

        flash(
            "Certificate is available after passing the assessment.",
            "warning"
        )

        return redirect(
            url_for("dashboard")
        )

    # ==========================================
    # CREATE PDF
    # ==========================================

    filename = (
        f"quizverse_certificate_{attempt_id}.pdf"
    )

    filepath = os.path.join(
        os.getcwd(),
        filename
    )

    pdf = canvas.Canvas(
        filepath,
        pagesize=A4
    )

    width, height = A4

    pdf.setTitle(
        "QuizVerse Certificate"
    )

    # Border
    pdf.rect(
        40,
        40,
        width - 80,
        height - 80
    )

    pdf.setFont(
        "Helvetica-Bold",
        28
    )

    pdf.drawCentredString(
        width / 2,
        height - 130,
        "QUIZVERSE"
    )

    pdf.setFont(
        "Helvetica-Bold",
        22
    )

    pdf.drawCentredString(
        width / 2,
        height - 180,
        "Certificate of Achievement"
    )

    pdf.setFont(
        "Helvetica",
        14
    )

    pdf.drawCentredString(
        width / 2,
        height - 250,
        "This certificate is proudly presented to"
    )

    pdf.setFont(
        "Helvetica-Bold",
        24
    )

    pdf.drawCentredString(
        width / 2,
        height - 300,
        session.get("name", username)
    )

    pdf.setFont(
        "Helvetica",
        14
    )

    pdf.drawCentredString(
        width / 2,
        height - 350,
        "for successfully completing the"
    )

    pdf.setFont(
        "Helvetica-Bold",
        18
    )

    pdf.drawCentredString(
        width / 2,
        height - 385,
        f"{result['category']} Assessment"
    )

    pdf.setFont(
        "Helvetica",
        14
    )

    pdf.drawCentredString(
        width / 2,
        height - 430,
        f"Score: {result['score']} / {result['total']}"
    )

    pdf.drawCentredString(
        width / 2,
        height - 455,
        f"Percentage: {result['percentage']}%"
    )

    pdf.drawCentredString(
        width / 2,
        height - 480,
        f"Difficulty: {result['difficulty']}"
    )

    pdf.setFont(
        "Helvetica-Oblique",
        11
    )

    pdf.drawCentredString(
        width / 2,
        100,
        "Keep learning. Keep growing. Keep achieving."
    )

    pdf.save()

    return send_file(
        filepath,
        as_attachment=True,
        download_name=filename
    )


# =========================================================
# LEADERBOARD
# =========================================================

@app.route("/leaderboard")
@login_required
def leaderboard():

    conn = get_db()

    leaderboard_data = conn.execute(
        """
        SELECT
            username,
            MAX(percentage) AS best_score,
            ROUND(AVG(percentage), 1) AS average_score,
            SUM(xp) AS total_xp,
            COUNT(*) AS attempts
        FROM results
        WHERE username != 'admin'
        GROUP BY username
        ORDER BY
            best_score DESC,
            total_xp DESC
        LIMIT 20
        """
    ).fetchall()

    conn.close()

    return render_template(
        "leaderboard.html",
        leaderboard=leaderboard_data
    )


# =========================================================
# ADMIN DASHBOARD
# =========================================================

@app.route("/admin")
@admin_required
def admin():

    conn = get_db()

    total_users = conn.execute(
        """
        SELECT COUNT(*) AS count
        FROM users
        WHERE role = 'student'
        """
    ).fetchone()["count"]

    total_questions = conn.execute(
        """
        SELECT COUNT(*) AS count
        FROM questions
        """
    ).fetchone()["count"]

    total_attempts = conn.execute(
        """
        SELECT COUNT(*) AS count
        FROM results
        """
    ).fetchone()["count"]

    average_score = conn.execute(
        """
        SELECT AVG(percentage) AS average
        FROM results
        """
    ).fetchone()["average"]

    recent_results = conn.execute(
        """
        SELECT *
        FROM results
        ORDER BY submitted_at DESC
        LIMIT 10
        """
    ).fetchall()

    conn.close()

    return render_template(
        "admin.html",
        total_users=total_users,
        total_questions=total_questions,
        total_attempts=total_attempts,
        average_score=round(
            average_score or 0,
            1
        ),
        recent_results=recent_results
    )


# =========================================================
# ADMIN QUESTIONS
# =========================================================

@app.route("/admin/questions")
@admin_required
def questions():

    conn = get_db()

    questions_data = conn.execute(
        """
        SELECT *
        FROM questions
        ORDER BY category, id DESC
        """
    ).fetchall()

    conn.close()

    return render_template(
        "questions.html",
        questions=questions_data
    )


# =========================================================
# ADMIN ADD QUESTION
# =========================================================

@app.route(
    "/admin/add-question",
    methods=["GET", "POST"]
)
@admin_required
def add_question():

    if request.method == "POST":

        question = request.form.get(
            "question",
            ""
        ).strip()

        option_a = request.form.get(
            "option_a",
            ""
        ).strip()

        option_b = request.form.get(
            "option_b",
            ""
        ).strip()

        option_c = request.form.get(
            "option_c",
            ""
        ).strip()

        option_d = request.form.get(
            "option_d",
            ""
        ).strip()

        correct_answer = request.form.get(
            "correct_answer",
            ""
        ).strip().upper()

        category = request.form.get(
            "category",
            ""
        ).strip()

        difficulty = request.form.get(
            "difficulty",
            "Easy"
        )

        explanation = request.form.get(
            "explanation",
            ""
        ).strip()

        if not all([
            question,
            option_a,
            option_b,
            option_c,
            option_d,
            correct_answer,
            category
        ]):

            flash(
                "Please fill all required fields.",
                "danger"
            )

            return redirect(
                url_for("add_question")
            )

        if correct_answer not in [
            "A",
            "B",
            "C",
            "D"
        ]:

            flash(
                "Correct answer must be A, B, C or D.",
                "danger"
            )

            return redirect(
                url_for("add_question")
            )

        conn = get_db()

        conn.execute(
            """
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
            """,
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
        )

        conn.commit()
        conn.close()

        flash(
            "Question added successfully.",
            "success"
        )

        return redirect(
            url_for("questions")
        )

    return render_template(
        "add_question.html"
    )


# =========================================================
# ADMIN DELETE QUESTION
# =========================================================

@app.route(
    "/admin/delete-question/<int:question_id>",
    methods=["POST"]
)
@admin_required
def delete_question(question_id):

    conn = get_db()

    conn.execute(
        """
        DELETE FROM questions
        WHERE id = ?
        """,
        (question_id,)
    )

    conn.commit()
    conn.close()

    flash(
        "Question deleted successfully.",
        "success"
    )

    return redirect(
        url_for("questions")
    )


# =========================================================
# ERROR HANDLERS
# =========================================================

@app.errorhandler(404)
def page_not_found(error):

    return render_template(
        "base.html"
    ), 404


@app.errorhandler(500)
def internal_error(error):

    return """
    <h1>QuizVerse Server Error</h1>
    <p>Please check the terminal for the detailed error.</p>
    """, 500


# =========================================================
# RUN APPLICATION
# =========================================================

if __name__ == "__main__":

    print("=" * 60)
    print("QuizVerse is starting...")
    print("Open: http://127.0.0.1:5000")
    print("=" * 60)

    socketio.run(
        app,
        host="127.0.0.1",
        port=5000,
        debug=True
    )