🎯 QuizVerse

![QuizVerse](https://img.shields.io/badge/Project-QuizVerse-blue)
![Python](https://img.shields.io/badge/Python-3.x-yellow)
![Flask](https://img.shields.io/badge/Flask-Web%20Framework-black)
![HTML](https://img.shields.io/badge/HTML-Frontend-orange)
![CSS](https://img.shields.io/badge/CSS-Styling-blue)
![JavaScript](https://img.shields.io/badge/JavaScript-Client%20Side-yellow)

📌 About the Project

QuizVerse is a web-based quiz application developed using **Python and Flask**.

The application follows a **Client–Server Architecture**, where the client provides the user interface and communicates with the Flask server. The server handles application logic, quiz questions, answers, and result processing.

The main goal of QuizVerse is to provide a simple, interactive, and user-friendly platform for attempting quizzes and viewing results.

🖼️ Project Overview

QuizVerse Architecture


flowchart LR
    A[👩‍💻 Client / User] -->|HTTP Request| B[🌐 Flask Server]
    B --> C[⚙️ Application Logic]
    C --> D[📝 Quiz Questions]
    C --> E[📊 Score / Results]
    D --> B
    E --> B
    B -->|HTTP Response| A

🔄 Client–Server Communication

        USER
          │
          ▼
   ┌───────────────┐
   │    CLIENT     │
   │ HTML/CSS/JS   │
   └───────┬───────┘
           │
       HTTP Request
           │
           ▼
   ┌───────────────┐
   │ FLASK SERVER  │
   │    Python     │
   └───────┬───────┘
           │
      Quiz Processing
           │
           ▼
   ┌───────────────┐
   │ Quiz / Result  │
   │     Logic      │
   └───────┬───────┘
           │
       HTTP Response
           │
           ▼
   ┌───────────────┐
   │    CLIENT     │
   │ Display Result│
   └───────────────┘
