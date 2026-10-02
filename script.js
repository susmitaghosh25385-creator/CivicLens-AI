const issueInput = document.getElementById("issueInput");
const analyzeBtn = document.getElementById("analyzeBtn");

const category = document.getElementById("category");
const priority = document.getElementById("priority");
const summary = document.getElementById("summary");
const action = document.getElementById("action");


analyzeBtn.addEventListener("click", function () {

    const issue = issueInput.value.trim();

    if (issue === "") {
        alert("Please describe a civic issue first.");
        return;
    }

    category.textContent = "Analyzing...";
    priority.textContent = "Analyzing...";
    summary.textContent = "Processing your report...";
    action.textContent = "Generating recommendation...";


    setTimeout(function () {

        category.textContent = "Civic Issue";

        priority.textContent = "Needs Review";

        summary.textContent =
            "Your reported issue has been received and is ready for further analysis.";

        action.textContent =
            "The issue should be reviewed by the appropriate civic authority.";

    }, 1000);

});