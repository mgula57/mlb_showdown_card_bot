
// -------------------------------------------------------
// METHODS
// -------------------------------------------------------

// VALIDATE FORM
function validate_form(ignoreAlert) {
    // ENSURE THAT REQUIRED FIELDS ARE FILLED OUT
    var name = document.getElementById("name").value;
    var year = document.getElementById("year").value;
    if (name == null || name == "") {
        if (ignoreAlert == false) {
            alert("Please enter a name.");
        }
        return false;
    }
    if (year == null || year == "" || Number.isInteger(year)) {
        if (ignoreAlert == false) {
            alert("Please enter a year.");
        }
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

// THEME
function toggleTheme(toggleElement) {
    if (toggleElement.checked) {
        setTheme('dark');
    } else {
        setTheme('light');
    }
}

function setTheme(themeName) {
    // UPDATE LOCAL STORAGE
    localStorage.setItem('theme', themeName);

    // ALTER CONTAINERS
    containers_to_alter = ["container_bg", "overlay", "input_container_column", "input_container", "main_body", "breakdown_output", "player_name", "player_link", "estimated_values_footnote"]
    for (const id of containers_to_alter) {
        document.getElementById(id).className = (id + "_" + themeName);
    }

    form_inputs_to_alter = ["name", "year", "setSelection", "expansionSelection", "editionSelection", "setnum", "statsVersionSelection", "darkModeToggleLabel", "varSpdToggleLabel", "addBorderLabel", "darkThemeToggleLabel", "url", "img_upload", "stats_table", "points_table", "accuracy_table"]
    for (const id of form_inputs_to_alter) {
        var current_name = document.getElementById(id).className
        const is_text_only = ["darkModeToggleLabel", "varSpdToggleLabel", "addBorderLabel", "darkThemeToggleLabel"].includes(id)
        const suffix = (is_text_only) ? 'text-muted' : 'bg-dark text-white';
        if (themeName == 'dark') {
            if (current_name.includes(suffix) == false) {
                document.getElementById(id).className = (current_name + ' ' + suffix);
            }
        } else {
            document.getElementById(id).className = current_name.replace(suffix,'');
        }
    }
    // IMAGES
    const suffix = (themeName == 'dark') ? '-Dark' : ''; 
    document.getElementById('showdown_logo_img').src = `static/interface/ShowdownLogo${suffix}.png`;
    if (document.getElementById('card_image').src.includes('interface')) {
        document.getElementById('card_image').src = `static/interface/BlankPlayer${suffix}.png`;
    }
}

function showCardData(data) {
    $('#overlay').hide();
    $("#error").text(data.error);
    document.getElementById("error").style.color = "red";
    // ADD STATS TO TABLE
    if (!data.error) {
        // THEME
        var storedTheme = localStorage.getItem('theme')

        // CHANGE CARD IMAGE
        $("#card_image").attr('src', data.image_path);
        console.log("auto image");
        if (data.is_automated_image) {
            const successColor = (storedTheme == 'dark') ? "#41d21a" : "green"
            document.getElementById("error").style.color = successColor;
            $("#error").text("Automated Image!");
        };
        
        // ADD HYPERLINK TO BREF
        if (data.player_name) {
            document.getElementById("playerlink_href").href = data.bref_url;
            $("#playerlink_href_text").text('BREF Page');
            $("#player_name").text(data.player_name.toUpperCase());
            $("#player_link").text(`${data.player_year} (${data.player_context} Set)`);
        }
        
        // VAR NEEDED FOR TABLE CLASSES
        var table_class_suffix = (storedTheme == 'dark') ? " bg-dark text-white" : ""

        // PLAYER STATS
        var player_stats_table = "<table class='table" + table_class_suffix + "' id='stats_table'><tr><th> </th><th>Actual</th><th>Showdown</th></tr>";
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
        var player_points_table = "<table class='table" + table_class_suffix + "' id='points_table'><tr> <th>Category</th> <th>Stat</th> <th>Points</th> </tr>";
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
        $('#name').val(data.player_name);
        $('#year').val(data.player_year);
        // PLAYER ACCURACY
        
        var player_accuracy_table = "<table class='table" + table_class_suffix + "' id='accuracy_table'><tr> <th>Version</th> <th>" + data.player_command + "</th> <th>Outs</th> <th>Accuracy</th> </tr>";
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
    };
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
        var storedTheme = localStorage.getItem('theme')
        if (storedTheme.length > 0) {
            setTheme(storedTheme);
            if (storedTheme == 'dark') {
                document.getElementById("dark_theme_toggle").checked = true;
            }
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
    $('a#create_card, a#create_card_random').bind('click', function (event) {
        is_random_card = $(event.currentTarget).attr('id') == 'create_card_random';
        is_valid = validate_form(ignoreAlert=is_random_card)
        
        if (is_valid || is_random_card) {
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
            var name = (is_random_card === true) ? '((RANDOM))' : $('input[name="name"]').val();
            var year = (is_random_card === true) ? '((RANDOM))' : $('input[name="year"]').val();
            var editionSelection = $("#editionSelection :selected").val();
            var is_cc = editionSelection == "Cooperstown Collection";
            var is_ss = editionSelection == "Super Season";
            var is_rs = editionSelection == "Rookie Season";
            var is_asg = editionSelection == "All-Star Game";
            var is_holiday = editionSelection == "Holiday";

            // CACHE SET VALUE
            var set = $("#setSelection :selected").val()
            cacheSet(set)

            $.getJSON('/card_creation', {
                name: name,
                year: year,
                set: set,
                url: $('input[name="url"]').val(),
                img_name: image_name,
                cc: is_cc,
                ss: is_ss,
                rs: is_rs,
                asg: is_asg,
                set_num: $('input[name="setnum"]').val(),
                offset: selectedOffset,
                expansion: $("#expansionSelection :selected").val(),
                is_holiday: is_holiday,
                addBorder: $('#addBorder').is(':checked'),
                is_dark_mode: $('#darkModeToggle').is(':checked'),
                is_variable_spd_00_01: $('#varSpdToggle').is(':checked'),
            }, function (data) {
                showCardData(data)
            });
            return false;
        }
    });

})