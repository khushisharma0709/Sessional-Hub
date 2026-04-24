// Sessional Hub - script.js
// Shared JS used across all pages

// Unit toggle on generate page
function showUnit(num) {
    let box = document.getElementById("unit" + num + "box");
    if (box) {
        box.style.display = box.style.display === "none" ? "block" : "none";
    }
}

function toggleTopics(selectBox, id) {
    let box = document.getElementById(id);
    if (!box) return;
    box.style.display = selectBox.value === "partial" ? "block" : "none";
}

function limitTopics(input, unit) {
    let max = parseInt(input.value);
    let checks = document.querySelectorAll('input[name="unit' + unit + '_topics"]');
    checks.forEach(c => {
        c.onclick = function () {
            let selected = document.querySelectorAll('input[name="unit' + unit + '_topics"]:checked');
            if (selected.length > max) {
                this.checked = false;
                alert("Only " + max + " topics allowed");
            }
        };
    });
}