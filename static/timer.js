document.addEventListener("DOMContentLoaded", function () {

    const questions =
        document.querySelectorAll(".question-card");

    const progressBar =
        document.getElementById("quizProgress");

    const counter =
        document.getElementById("questionCounter");

    const timer =
        document.getElementById("timer");

    const form =
        document.getElementById("quizForm");


    let currentQuestion = 0;


    function showQuestion(index) {

        questions.forEach(function (question, i) {

            question.classList.toggle(
                "d-none",
                i !== index
            );

        });


        const number =
            index + 1;

        counter.textContent =
            number + " / " + questions.length;


        const progress =
            (number / questions.length) * 100;

        progressBar.style.width =
            progress + "%";

    }


    document.querySelectorAll(".next-btn")
        .forEach(function (button) {

            button.addEventListener(
                "click",
                function () {

                    if (currentQuestion < questions.length - 1) {

                        currentQuestion++;

                        showQuestion(
                            currentQuestion
                        );

                        window.scrollTo({
                            top: 0,
                            behavior: "smooth"
                        });

                    }

                }
            );

        });


    document.querySelectorAll(".previous-btn")
        .forEach(function (button) {

            button.addEventListener(
                "click",
                function () {

                    if (currentQuestion > 0) {

                        currentQuestion--;

                        showQuestion(
                            currentQuestion
                        );

                        window.scrollTo({
                            top: 0,
                            behavior: "smooth"
                        });

                    }

                }
            );

        });


    // =====================================================
    // TIMER
    // =====================================================

    let remaining =
        TIME_LIMIT;


    function updateTimer() {

        const minutes =
            Math.floor(
                remaining / 60
            );

        const seconds =
            remaining % 60;


        timer.textContent =
            String(minutes).padStart(2, "0")
            + ":"
            + String(seconds).padStart(2, "0");


        if (remaining <= 60) {

            timer.classList.add(
                "timer-danger"
            );

        }


        if (remaining <= 0) {

            timer.textContent =
                "00:00";

            clearInterval(timerInterval);

            alert(
                "Time is up! Your assessment will be submitted automatically."
            );

            form.submit();

            return;

        }


        remaining--;

    }


    updateTimer();

    const timerInterval =
        setInterval(
            updateTimer,
            1000
        );


    // =====================================================
    // WARN BEFORE LEAVING
    // =====================================================

    window.addEventListener(
        "beforeunload",
        function (event) {

            event.preventDefault();

            event.returnValue = "";

        }
    );


    form.addEventListener(
        "submit",
        function () {

            window.onbeforeunload = null;

            clearInterval(timerInterval);

        }
    );


    showQuestion(0);

});