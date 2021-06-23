$("#collapse_history_button").click(function() {
    $('#collapse_history').collapse('toggle');
   // $('#collapse_history_span').toggleClass('glyphicon-chevron-up glyphicon-chevron-down');
});

function clear_runs_table() {
    $("#history_table tbody tr").remove();
}

function insert_run(task, method, target = '-', res = '-') {

    // Create an empty <tr> element and add it to the 1st position of the table:
    var row = document.getElementById('history_table').getElementsByTagName('tbody')[0].insertRow(0);

    // Insert new cells (<td> elements) at the 1st and 2nd position of the "new" <tr> element:
    var cell1 = row.insertCell(0);
    var cell2 = row.insertCell(1);
    var cell3 = row.insertCell(2);
    var cell4 = row.insertCell(3);

    // Add some text to the new cells:
    cell1.innerHTML = task;
    cell2.innerHTML = method;
    cell3.innerHTML = target;
    cell4.innerHTML = res;
}