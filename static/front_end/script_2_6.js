
// -------------------------------------------------------
// METHODS
// -------------------------------------------------------

// VALIDATE FORM
function validate_form() {
    // ENSURE THAT REQUIRED FIELDS ARE FILLED OUT
    var name = document.getElementById("name").value;
    var year = document.getElementById("year").value;
    if (name == null || name == "") {
        alert("Please enter a name.");
        return false;
    }
    if (year == null || year == "" || Number.isInteger(year)) {
        alert("Please enter a year.");
        return false;
    }
    return true;
}
// UPLOADING IMAGE
function uploadImageFile() {
    var image_data = $('#img_upload').prop('files')[0];
    var form_data = new FormData();
    form_data.append('image_file', image_data);
    $.ajax({
        url: '/upload',
        cache: false,
        contentType: false,
        processData: false,
        data: form_data,
        method: 'POST',
        success: function (php_script_response) {
            alert(php_script_response);
        },
        error: function (data) {
            console.log("error");
            console.log(data);
        }
    });
}

// STORE SET IN CACHE
function cacheSet(set) {
    // Check if the localStorage object exists
    if(localStorage) {
        // Store data
        localStorage.setItem("set", set);
    }
}

// CHANGE OUTPUT VIEWS
function checkHideForStats(statsElement) {
    if (statsElement.checked) {
        document.getElementById("stats_div").style.display = "initial";
        document.getElementById("points_div").style.display = "none";
        document.getElementById("accuracy_div").style.display = "none";
    }
}
 
function checkHideForPoints(pointsElement) {
    if (pointsElement.checked) {
        document.getElementById("stats_div").style.display = "none";
        document.getElementById("points_div").style.display = "initial";
        document.getElementById("accuracy_div").style.display = "none";
    }
}

function checkHideForAccuracy(accuracyElement) {
    if (accuracyElement.checked) {
        document.getElementById("stats_div").style.display = "none";
        document.getElementById("points_div").style.display = "none";
        document.getElementById("accuracy_div").style.display = "initial";
    }
}

// -------------------------------------------------------
// ON LOAD
// -------------------------------------------------------

$(document).ready(function() {
    if(localStorage) {
        var storedSet = localStorage.getItem("set")
        if (storedSet.length > 0) {
            document.getElementById("setSelection").value = storedSet;
        }
    }
});

// -------------------------------------------------------
// AJAX
// -------------------------------------------------------

// TOOLTIP
$(function () {
    $('[data-toggle="tooltip"]').tooltip()
})
// CREATE CARD
$(function () {
    $('a#create_card').bind('click', function () {
        is_valid = validate_form()
        if (is_valid) {
            $('#overlay').show();
            uploadImageFile();
            var files = $('#img_upload').prop('files');
            var image_name = ""
            if (files.length > 0) {
                image_name = files[0].name;
            }

            // STATS ALTERNATES
            const offsets = document.querySelectorAll('input[name="offset"]');
            let selectedOffset;
            for (const offset of offsets) {
                if (offset.checked) {
                    selectedOffset = offset.id.slice(-1);
                    break;
                }
            }

            // EDITION
            var editionSelection = $("#editionSelection :selected").val();
            var is_cc = editionSelection == "Cooperstown Collection";
            var is_ss = editionSelection == "Super Season";
            var is_asg = editionSelection == "All-Star Game";
            var is_holiday = editionSelection == "Holiday";

            // CACHE SET VALUE
            var set = $("#setSelection :selected").val()
            cacheSet(set)

            $.getJSON('/card_creation', {
                name: $('input[name="name"]').val(),
                year: $('input[name="year"]').val(),
                set: set,
                url: $('input[name="url"]').val(),
                img_name: image_name,
                cc: is_cc,
                ss: is_ss,
                asg: is_asg,
                set_num: $('input[name="setnum"]').val(),
                offset: selectedOffset,
                expansion: $("#expansionSelection :selected").val(),
                is_holiday: is_holiday,
                addBorder: $('#addBorder').is(':checked'),
            }, function (data) {
                $('#overlay').hide();
                $("#error").text(data.error);
                // ADD STATS TO TABLE
                if (data.error != 'Unable to create Showdown Card. Make sure the player name and year are correct.') {
                    $("#card_image").attr('src', data.image_path);
                    console.log("auto image");
                    if (data.is_automated_image) {
                        document.getElementById("error").style.color = "green";
                        $("#error").text("Automated Image!");
                    };
                    
                    // ADD HYPERLINK TO BREF
                    document.getElementById("playerlink_href").href = data.bref_url;
                    $("#playerlink").text(`${data.player_name} - ${data.player_year} (${data.player_context} Set)`);
                    
                    // PLAYER STATS
                    var player_stats_table = "<table class='table table-striped' id='stats_table'><tr><th> </th><th>Actual</th><th>Showdown</th></tr>";
                    $.each(data.player_stats, function (index, value) {
                        player_stats_table += '<tr>'
                        $.each(value, function (index, value) {
                            if (index == 0) {
                                bold_start = '<b>';
                                bold_end = '</b>';
                            } else {
                                bold_start = '';
                                bold_end = '';
                            }
                            player_stats_table += '<td>' + bold_start + value + bold_end + '</td>';
                        });
                        player_stats_table += '</tr>';
                    });
                    player_stats_table += '</table>';
                    $("#stats_table").replaceWith(player_stats_table);

                    // PLAYER POINTS
                    var player_points_table = "<table class='table table-striped' id='points_table'><tr> <th>Category</th> <th>Stat</th> <th>Points</th> </tr>";
                    $.each(data.player_points, function (index, value) {
                        player_points_table += '<tr>'
                        is_total_row = (data.player_points.length - 1) == index;
                        $.each(value, function (index, value) {
                            if (index == 0) {
                                bold_start = '<b>';
                                bold_end = '</b>';
                            } else {
                                bold_start = '';
                                bold_end = '';
                            }
                            if (is_total_row) {
                                td_class = ' class="table-success">';
                            } else {
                                td_class = '>';
                            }
                            player_points_table += '<td' + td_class + bold_start + value + bold_end + '</td>';
                        });
                        player_points_table += '</tr>';
                    });
                    player_points_table += '</table>';
                    $("#points_table").replaceWith(player_points_table);

                    // PLAYER ACCURACY
                    var player_accuracy_table = "<table class='table table-striped' id='accuracy_table'><tr> <th>Version</th> <th>' + data.player_command + '</th> <th>Outs</th> <th>Accuracy</th> </tr>";
                    $.each(data.player_accuracy, function (index, value) {
                        player_accuracy_table += '<tr>'
                        $.each(value, function (index, value) {
                            if (index == 0) {
                                bold_start = '<b>';
                                bold_end = '</b>';
                            } else {
                                bold_start = '';
                                bold_end = '';
                            }
                            player_accuracy_table += '<td>' + bold_start + value + bold_end + '</td>';
                        });
                        player_accuracy_table += '</tr>';
                    });
                    player_accuracy_table += '</table>';
                    $("#accuracy_table").replaceWith(player_accuracy_table);
                }
            });
            return false;
        }
    });
});