function sortTable(columnIndex) {
    var table, rows, switching, i, x, y, shouldSwitch, dir, switchcount = 0;
    table = event.target.closest('table');
    switching = true;
    dir = "asc";

    while (switching) {
        switching = false;
        rows = table.rows;

        for (i = 1; i < (rows.length - 1); i++) {
            shouldSwitch = false;
            x = rows[i].getElementsByTagName("TD")[columnIndex];
            y = rows[i + 1].getElementsByTagName("TD")[columnIndex];

            var xContent = x.innerText.toLowerCase();
            var yContent = y.innerText.toLowerCase();

            // Remove emojis e símbolos para comparação numérica
            var xNum = parseFloat(xContent.replace(/[^\d.-]/g, ''));
            var yNum = parseFloat(yContent.replace(/[^\d.-]/g, ''));

            if (!isNaN(xNum) && !isNaN(yNum)) {
                if (dir == "asc") {
                    if (xNum > yNum) { shouldSwitch = true; break; }
                } else if (dir == "desc") {
                    if (xNum < yNum) { shouldSwitch = true; break; }
                }
            } else {
                if (dir == "asc") {
                    if (xContent > yContent) { shouldSwitch = true; break; }
                } else if (dir == "desc") {
                    if (xContent < yContent) { shouldSwitch = true; break; }
                }
            }
        }

        if (shouldSwitch) {
            rows[i].parentNode.insertBefore(rows[i + 1], rows[i]);
            switching = true;
            switchcount++;
        } else {
            if (switchcount == 0 && dir == "asc") {
                dir = "desc";
                switching = true;
            }
        }
    }
}
