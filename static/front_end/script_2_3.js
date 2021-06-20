
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
        console.log(Number.isInteger(year))
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
            const sets = document.querySelectorAll('input[name="set"]');
            let selectedValue;
            for (const set of sets) {
                if (set.checked) {
                    selectedValue = set.value;
                    break;
                }
            }
            var files = $('#img_upload').prop('files');
            var image_name = ""
            if (files.length > 0) {
                image_name = files[0].name;
            }
            $.getJSON('/card_creation', {
                name: $('input[name="name"]').val(),
                year: $('input[name="year"]').val(),
                set: selectedValue,
                url: $('input[name="url"]').val(),
                img_name: image_name,
                cc: $('#cc').is(':checked'),
                ss: $('#ss').is(':checked'),
                asg: $('#asg').is(':checked'),
                set_num: $('input[name="setnum"]').val(),
                offset: $('input[name="offset"]').val(),
                expansion: $("#expansionSelection :selected").val(),
            }, function (data) {
                $('#overlay').hide();
                $("#error").text(data.error);
                // ADD STATS TO TABLE
                if (data.error != 'Unable to create Showdown Card. Make sure the player name and year are correct.') {
                    $("#card_image").attr('src', data.image_path);
                    var player_stats_table = '<table id="stats_table"><tr><th> </th><th>Actual</th><th>Showdown</th></tr>';
                    console.log(data.player_stats)
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
                }
            });
            return false;
        }
    });
});