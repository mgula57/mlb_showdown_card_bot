
// -------------------------------------------------------
// METHODS
// -------------------------------------------------------

// VALIDATE FORM
function validate_form(ignoreAlert) {
    // ENSURE THAT REQUIRED FIELDS ARE FILLED OUT
    var name = document.getElementById("name").value;
    var year = document.getElementById("year").value;
    var period = document.getElementById("periodSelection").value;
    var split_name = document.getElementById("split").value;

    // NAME MUST BE POPULATED
    if (name == null || name == "") {
        if (ignoreAlert == false) {
            alert("Please enter a name.");
        }
        return false;
    }

    // YEAR MUST BE POPULATED
    if (year == null || year == "" || Number.isInteger(year)) {
        if (ignoreAlert == false) {
            alert("Please enter a year.");
        }
        return false;
    }

    // SPLIT MUST BE POPULATED (IF PERIOD IS SPLIT)
    if (period == 'SPLIT' & (split_name == null || split_name == "") ) {
        if (ignoreAlert == false) {
            alert("Please enter a split, or switch to a different period type.");
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
            console.log("Error Uploading Image");
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
function toggleBreakdownSelection() {
    for (var option of document.getElementById('breakdownSelection').options) {
        if (option.selected) {
            document.getElementById(option.value + "_div").style.display = "initial";
        } else {
            document.getElementById(option.value + "_div").style.display = "none";
        }
    }
}
 
function checkHideForPoints(pointsElement) {
    if (pointsElement.checked) {
        document.getElementById("stats_div").style.display = "none";
        document.getElementById("points_div").style.display = "initial";
        document.getElementById("accuracy_div").style.display = "none";
        document.getElementById("rank_div").style.display = "none";
    }
}

function checkHideForAccuracy(accuracyElement) {
    if (accuracyElement.checked) {
        document.getElementById("stats_div").style.display = "none";
        document.getElementById("points_div").style.display = "none";
        document.getElementById("accuracy_div").style.display = "initial";
        document.getElementById("rank_div").style.display = "none";
    }
}

function checkHideForRank(rankElement) {
    if (rankElement.checked) {
        document.getElementById("stats_div").style.display = "none";
        document.getElementById("points_div").style.display = "none";
        document.getElementById("accuracy_div").style.display = "none";
        document.getElementById("rank_div").style.display = "initial";
    }
}

function changeImageSection(imageSelectObject) {
    var selection = imageSelectObject.value;
    for (const section of ['auto', 'link', 'upload']) { 
        console.log(section)
        if (section == selection) {
            $("#" + section).show();
        } else {
            $("#" + section).hide();
        }
    }
}

function changePeriodSection(windowSelectObject) {
    
    // SHOW/HIDE SECTIONS
    var selection = windowSelectObject.value;
    const sections_and_ids = {
        'DATES': [
            'div_start_date',
            'div_end_date',
        ],
        'POST' : [],
        'REGULAR': [],
        'SPLIT': ['div_split', 'div_split_description'],
    };
    for (const key in sections_and_ids) { 
        var ids = sections_and_ids[key]
        for (const id of ids) {
            if (key == selection) {
                $("#" + id).show();
            } else {
                $("#" + id).hide();
            }
        }
    }

    // SHOW/HIDE EDITIONS
    if (selection == 'POST') {
        // ENABLE POSTSEASON, DISABLE SUPER SEASON AND ASG
        document.getElementById("POST-option").disabled = false;
        for (const edition of ["ASG", "SS"]) { 
            var element = document.getElementById(edition + "-option");
            element.disabled = true;
            if (element.selected == true) {
                // CHANGE SELECTION TO NONE
                element.selected = false;
                document.getElementById("NONE-option").selected = true;
            }
        }
        
    } else {
        // ENABLE POSTSEASON, DISABLE SUPER SEASON AND ASG
        for (const edition of ['ASG', 'SS']) { 
            document.getElementById(edition + "-option").disabled = false;
        }
        var postElement = document.getElementById("POST-option")
        postElement.disabled = true;
        if (postElement.selected == true) {
            // CHANGE SELECTION TO NONE
            postElement.selected = false;
            document.getElementById("NONE-option").selected = true;
        }
    }
}

// ON CHANGE OF YEAR INPUT
function changeYear(newYear) {
    yearText = newYear.value;
    if (yearText.length == 4) {
        for (const date of ["start_date", "end_date"]) {
            console.log(date)
            document.getElementById(date).value = yearText + document.getElementById(date).value.slice(4);
        }
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

// SETUP RADAR CHART
function createRadarChart(data) {
    $("#radar_container").show();

    // DESTROY EXITING CHART INSTANCE TO REUSE <CANVAS> ELEMENT
    let chartStatus = Chart.getChart("playerRadar");
    if (chartStatus != undefined) {
        chartStatus.destroy();
    }
    
    // CREATE NEW CHART OBJECT
    var marksCanvas = document.getElementById("playerRadar");
    var color = Chart.helpers.color;
    Chart.defaults.color = "black"
    var marksData = {
        labels: data.radar_labels,
        datasets: [
            {
                label: `${data.player_name} (${data.player_year})`,
                backgroundColor: color(data.radar_color).alpha(0.2).rgbString(),
                borderColor: data.radar_color,
                borderWidth: 1,
                pointBackgroundColor: data.radar_color,
                data: data.radar_values
            },
            {
                label: `Avg (${data.player_year})`,
                backgroundColor: "rgb(0,0,0,0.1)",
                borderColor: "gray",
                borderWidth: 0.5,
                data: data.radar_values.map(x => 50)
            },
        ]
    };

    var chartOptions = {
        scales: {
            r: {
                pointLabels: {
                    font: {
                        size: 12,
                    }
                },
                ticks: {
                    callback: function() {return ""},
                    beginAtZero: true,
                    showLabelBackdrop: false
                },
                suggestedMin: 0,
                suggestedMax: 100,
            },
        }
    };

    var radarChart = new Chart(marksCanvas, {
        type: "radar",
        data: marksData,
        options: chartOptions
    });
}

// SETUP TRENDS CHART
function createTrendsChart(data) {
    // SHOW CONTAINER
    $("#trend_container").show();
    if (data.trends_diff > 0) {
        $("#player_trend_up_arrow").show();
        $("#player_trend_down_arrow").hide();
    } else if (data.trends_diff < 0) {
        $("#player_trend_down_arrow").show();
        $("#player_trend_up_arrow").hide();
    } else {
        $("#player_trend_down_arrow").hide();
        $("#player_trend_up_arrow").hide();
    }
    
    // DESTROY EXITING CHART INSTANCE TO REUSE <CANVAS> ELEMENT
    let chartStatus = Chart.getChart("playerTrends");
    if (chartStatus != undefined) {
        chartStatus.destroy();
    }
    
    // CREATE NEW CHART OBJECT
    var marksCanvas = document.getElementById("playerTrends");
    var color = Chart.helpers.color;

    // PARSE VALUES
    var xValues = []
    var yValues = []
    for (let day in data.trends_data) {
        xValues.push(day);
        yValues.push(data.trends_data[day]["points"]);
    }

    new Chart(marksCanvas, {
        type: "line",
        data: {
            labels: xValues,
            datasets: [{
                data: yValues,
                label: "PTS",
                borderColor: data.radar_color,
                backgroundColor: color(data.radar_color).alpha(0.2).rgbString(),
                fill: true
            }]
        },
        options: {
            plugins: {
                legend: {
                    display: false
                },
            },
            scales: {
              x: {
                type: 'time',
                time: {
                    unit: 'day',
                    parser: 'MM-dd-yyyy',
                    displayFormats: {
                        'day': 'MMM dd',
                    },
                    tooltipFormat: "MMM dd"
                }
              },
              y: {
                min: 0,
                max: Math.max(...yValues) + 200
              }
            },
            elements:{
                point:{
                    borderWidth: 0,
                    backgroundColor: 'rgba(0,0,0,0)'
                }
            }
          }
    });
}

function setTheme(themeName) {
    // UPDATE LOCAL STORAGE
    localStorage.setItem('theme', themeName);

    var is_dark = themeName == 'dark'
    // ALTER CONTAINERS
    containers_to_alter = ["container_bg", "overlay", "input_container_column", "input_container", "main_body", "breakdown_output", "radar_container", "trend_container", "player_name", "player_link", "player_shOPS_plus", "estimated_values_footnote", "rank_values_footnote", "opponent_values_footnote", "loader_container_rectangle"]
    for (const id of containers_to_alter) {
        var element = document.getElementById(id);
        if (element === null) {
            continue;
        }
        document.getElementById(id).className = (id + "_" + themeName);
    }

    form_inputs_to_alter = [
        "name", "year", "setSelection", "expansionSelection", "editionSelection", "moreOptionsSelect", 
        "setnum", "chartVersionSelection", "darkThemeToggleLabel", "url", "img_upload", "stats_table", 
        "points_table", "accuracy_table","rank_table", "opponent_table", "eraSelection", "breakdownSelection", 
        "imageTypeSelection", "parallelSelection", "periodSelection", "start_date", "end_date", "split"
    ]
    for (const id of form_inputs_to_alter) {
        var element = document.getElementById(id);
        if (element === null) {
            continue;
        }
        var current_name = element.className
        const is_text_only = ["darkModeToggleLabel", "varSpdToggleLabel", "addBorderLabel", "darkThemeToggleLabel"].includes(id)
        const is_table = ["stats_table", "points_table", "accuracy_table", "rank_table", "opponent_table"].includes(id)
        const default_suffix = (is_text_only) ? 'text-muted' : 'bg-dark text-white';
        const suffix = (is_table) ? 'table-dark' : default_suffix;
        
        if (is_dark) {
            if (current_name.includes(suffix) == false) {
                element.className = (current_name + ' ' + suffix);
            }
        } else {
            element.className = current_name.replace(suffix,'');
        }
    }
    // IMAGES
    const suffix = (is_dark) ? '-Dark' : ''; 
    document.getElementById('showdown_logo_img').src = `static/interface/ShowdownLogo${suffix}.png`;
    if (document.getElementById('card_image').src.includes('interface')) {
        document.getElementById('card_image').src = `static/interface/BlankPlayer${suffix}.png`;
    }
}

function showCardData(data) {
    $("#error").text(data.error);
    document.getElementById("error").style.color = "red";
    const isError = data.error & !data.image_path
    // ADD STATS TO TABLE
    if (!isError) {
        // THEME
        var storedTheme = localStorage.getItem('theme')

        // CHANGE ERROR TO ORANGE IF WARNING
        if (data.image_path) {
            document.getElementById("error").style.color = "orange";
        }

        // CHANGE CARD IMAGE
        $("#card_image").attr('src', data.image_path);

        // ADD MESSAGING BELOW CARD IMAGE
        const successColor = (storedTheme == 'dark') ? "#41d21a" : "green"
        
        if (data.is_stats_loaded_from_library || data.is_img_loaded_from_library) {
            console.log("Loaded From Showdown Library");
            $('#showdown_library_logo_img').show();
        } else {
            $('#showdown_library_logo_img').hide();
        }
        
        if (data.is_automated_image) {
            console.log("auto image");
            document.getElementById("error").style.color = successColor;
            $("#error").text("Automated Image!");
        };
        
        // ADD HYPERLINK TO BREF
        if (data.player_name) {
            document.getElementById("playerlink_href").href = data.bref_url;
            $("#playerlink_href_text").text(data.player_year);
            $("#player_name").text(data.player_name.toUpperCase());
            $("#player_link").text(`Set: ${data.player_set} | ${data.era} | Year(s):`);
        }

        // ADD shOPS+
        if (data.shOPS_plus) {
            $("#player_shOPS_plus_text").text("shOPS+");
            $("#player_shOPS_plus").text(data.shOPS_plus);
        } else {
            $("#player_shOPS_plus_text").text("");
            $("#player_shOPS_plus").text("");
        }
        
        // VAR NEEDED FOR TABLE CLASSES
        var table_class_suffix = (storedTheme == 'dark') ? " table-dark" : ""
        var table_class_name = "table table-striped table-bordered" + table_class_suffix
        
        // PLAYER STATS
        var player_stats_table = "<table class='" + table_class_name + "' id='stats_table'><tr><th> </th><th>Actual</th><th>Showdown</th></tr>";
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
        var player_points_table = "<table class='" + table_class_name + "' id='points_table'><tr> <th>Category</th> <th>Stat</th> <th>Points</th> </tr>";
        $.each(data.player_points, function (index, value) {
            is_total_row = (data.player_points.length - 1) == index;
            const tr_class = (is_total_row) ? ' class="table-success">' : '>';
            player_points_table += '<tr' + tr_class
            
            $.each(value, function (index, value) {
                if (index == 0) {
                    bold_start = '<b>';
                    bold_end = '</b>';
                } else {
                    bold_start = '';
                    bold_end = '';
                }
                player_points_table += '<td>' + bold_start + value + bold_end + '</td>';
            });
            player_points_table += '</tr>';
        });
        player_points_table += '</table>';
        $("#points_table").replaceWith(player_points_table);

        // ERA
        var opponent_text = "<h6 style='color: #686666; padding: 0px;'><b>Avg " + data.opponent_type + " - " + data.era + "</b></h6>"
        $("#avg_opponent_text").replaceWith(opponent_text);

        var opponent_table = "<table class='" + table_class_name + "' id='opponent_table'><tr> <th> </th> <th># Chart Results</th> </tr>";
        $.each(data.opponent, function (index, value) {
            opponent_table += '<tr>'
            $.each(value, function (index, value) {
                if (index == 0) {
                    bold_start = '<b>';
                    bold_end = '</b>';
                } else {
                    bold_start = '';
                    bold_end = '';
                }
                opponent_table += '<td>' + bold_start + value + bold_end + '</td>';
            });
            opponent_table += '</tr>';
        });
        opponent_table += '</table>';
        $("#opponent_table").replaceWith(opponent_table);

        // ACCURACY
        var player_accuracy_table = "<table class='" + table_class_name + "' id='accuracy_table'><tr> <th>Version</th> <th>" + data.player_command + "</th> <th>Outs</th> <th>Accuracy</th> </tr>";
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

        // PLAYER RANK
        // ONLY AVAILABLE FOR SHOWDOWN LIBRARY
        var player_ranks_table = "<table class='" + table_class_name + "' id='rank_table'><tr> <th> </th> <th>Value</th> <th>Rank</th> <th>Percentile</th> </tr>";
        $.each(data.player_ranks, function (index, value) {
            player_ranks_table += '<tr>'
            $.each(value, function (index, value) {
                if (index == 0) {
                    bold_start = '<b>';
                    bold_end = '</b>';
                } else {
                    bold_start = '';
                    bold_end = '';
                }
                td_colspan = (value == 'RANKINGS NOT AVAILABLE') ? " colspan='4'" : ""
                player_ranks_table += `<td${td_colspan}>` + bold_start + value + bold_end + '</td>';
            });
            player_ranks_table += '</tr>';
        });
        player_ranks_table += '</table>';
        $("#rank_table").replaceWith(player_ranks_table);

        // PLAYER RADAR CHART
        if (data.radar_labels != null) {
            createRadarChart(data=data)
        }
        else {
            $("#radar_container").hide();
        }

        // TRENDS GRAPH
        if (data.trends_data != null) {
            createTrendsChart(data=data)
        } else {
            $("#trend_container").hide();
        }

        // PERIOD
        $("#period_string").text(data.period);

        // WARNINGS

        // REMOVE EXISTING
        var warningDivs = document.getElementsByClassName("warning_text");

        // Convert the NodeList to an array for easier removal
        var warningDivsArray = Array.from(warningDivs);

        // Remove each div
        warningDivsArray.forEach(function (div) {
            div.remove();
        });

        var cardContainer = document.getElementById("card_container_div");

        for (var warning of data.warnings) {

            // CREATE A NEW PARAGRAPH ELEMENT
            var warningElement = document.createElement("h5");

            // SET THE CONTENT OF THE NEW PARAGRAPH
            warningElement.className = "warning_text"
            warningElement.textContent = '** ' + warning;
            warningElement.style.color = '#9fb419';

            // APPEND THE NEW PARAGRAPH TO THE END OF THE DIV
            cardContainer.appendChild(warningElement);
        }

    };
    $('#overlay').hide();
}

// -------------------------------------------------------
// TABS
// -------------------------------------------------------

function setupTabs(selectedTab) {
    // ITERATE THROUGH BUTTONS TO APPLY ON CLICK EVENT
    document.querySelectorAll(".tabs_button").forEach(button => {
        button.addEventListener("click", () => {
            // POPULATE CONSTANTS
            const tabsParent = button.parentElement;
            const tabContentId = button.dataset.forTab;
            const isExploreButton = tabContentId == "explore"
            var tabToActivate = document.querySelector(`.tab-content[data-tab="${tabContentId}"]`);
            const tabContentContainer = document.getElementById('tabs-content')
            if (!tabToActivate) {
                tabToActivate = document.getElementById('explore_content');
            }

            // REMOVE ACTIVE BUTTONS
            tabsParent.querySelectorAll(".tabs_button").forEach(button => {
                button.classList.remove("tabs_button--active");
            });
            
            // REMOVE ACTIVE CONTENT
            tabContentContainer.querySelectorAll(".tab-content").forEach(tab => {
                tab.classList.remove("tab-content--active");
            });

            if (isExploreButton) {
                // REMOVE HIDDEN
                tabToActivate.classList.remove('tab-content-explore-hidden');
                // ADD NORMAL
                tabToActivate.classList.add('tab-content');
            };

            // TRIGGER ACTIVE BUTTON/CONTENT
            button.classList.add("tabs_button--active");
            tabToActivate.classList.add("tab-content--active");
            
            // SET DEFAULT
            localStorage.setItem('tab', tabContentId);
        });
    });

    // APPLY DEFAULT TAB
    const isExploreButton = selectedTab == "explore"
    var tabToLoad = document.querySelector(`.tab-content[data-tab="${selectedTab}"]`);
    if (!tabToLoad) {
        tabToLoad = document.getElementById('explore_content');
    }
    if (isExploreButton) {
        // REMOVE HIDDEN
        tabToLoad.classList.remove('tab-content-explore-hidden');
        // ADD NORMAL
        tabToLoad.classList.add('tab-content');
    };
    tabToLoad.classList.add('tab-content--active');
    const tabButtonToLoad = document.querySelector(`.tabs_button[data-for-tab="${selectedTab}"]`);
    tabButtonToLoad.classList.add("tabs_button--active");
};

// -------------------------------------------------------
// ON LOAD
// -------------------------------------------------------

$(document).ready(function() {
    var selectedTab = "create"
    if(localStorage) {
        var storedSet = localStorage.getItem("set")
        if (storedSet) {
            document.getElementById("setSelection").value = storedSet.replace('2022-', '');
        }
        var storedTheme = localStorage.getItem('theme')
        if (storedTheme) {
            setTheme(storedTheme);
            if (storedTheme == 'dark') {
                document.getElementById("dark_theme_toggle").checked = true;
            }
        }
        // CHECK FOR LAST SELECTED TAB
        selectedTab = localStorage.getItem("tab");
        if (!selectedTab) {
            selectedTab = "create";
            localStorage.setItem('tab', selectedTab);
        }
    }
    // SET TABS
    setupTabs(selectedTab);
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
            
            var image_name = ""
            var image_link = ""
            var image_parallel = "NONE"
            
            var imageType = $("#imageTypeSelection :selected").val();
            if (imageType == "upload") {
                uploadImageFile();
                var files = $('#img_upload').prop('files');
                if (files.length > 0) {
                    image_name = files[0].name;
                }
            } else if (imageType == "link") {
                image_link = $('input[name="url"]').val()
            } else if (imageType == "auto") {
                image_parallel = $("#parallelSelection :selected").val();
            }

            // CHART ALTERNATES
            var selectedOffset = $("#chartVersionSelection :selected").val();
            var era = $("#eraSelection :selected").val();

            // EDITION
            var name = (is_random_card === true) ? '((RANDOM))' : $('input[name="name"]').val();
            var year = (is_random_card === true) ? '((RANDOM))' : $('input[name="year"]').val();
            var edition = $("#editionSelection :selected").val();

            // MORE OPTIONS
            var moreOptionsSelected = [];
            for (var option of document.getElementById('moreOptionsSelect').options)
            {
                if (option.selected) {
                    moreOptionsSelected.push(option.value);
                }
            }
            var is_border = moreOptionsSelected.includes("Border");
            var is_dark_mode = moreOptionsSelected.includes("DarkMode");
            var is_foil = moreOptionsSelected.includes("Foil");
            var show_year_text = moreOptionsSelected.includes("YearContainer");
            var set_year_plus_one = moreOptionsSelected.includes("SetYearPlus1");
            var hide_team_branding = moreOptionsSelected.includes("HideTeamBranding");
            var is_variable_spd = moreOptionsSelected.includes("VariableSpeed");
            var ignore_showdown_library = moreOptionsSelected.includes("IgnoreShowdownLibrary");
            var ignore_cache = moreOptionsSelected.includes("IgnoreCache");
            var is_secondary_color = moreOptionsSelected.includes("SecondaryColor");

            // NICKNAME INDEX
            var nickname_index = null;
            if (moreOptionsSelected.includes("Nickname-1")) {
                nickname_index = 1;
            } else if (moreOptionsSelected.includes("Nickname-2")) {
                nickname_index = 2
            } else if (moreOptionsSelected.includes("Nickname-3")) {
                nickname_index = 3
            }
            
            // PERIOD
            var period = $("#periodSelection :selected").val();
            var periodStartDate = $('input[name="date-start"]').val()
            var periodEndDate = $('input[name="date-end"]').val()
            var periodSplit = $('input[name="split"]').val()
            
            // CACHE SET VALUE
            var set = $("#setSelection :selected").val()
            cacheSet(set)

            $.getJSON('/card_creation', {
                name: name,
                year: year,
                set: set,
                edition: edition,
                url: image_link,
                img_name: image_name,
                set_num: $('input[name="setnum"]').val(),
                offset: selectedOffset,
                expansion: $("#expansionSelection :selected").val(),
                addBorder: is_border,
                is_dark_mode: is_dark_mode,
                is_variable_spd_00_01: is_variable_spd,
                is_foil: is_foil,
                show_year_text: show_year_text,
                set_year_plus_one: set_year_plus_one,
                hide_team_logo: hide_team_branding,
                ignore_showdown_library: ignore_showdown_library,
                era: era,
                parallel: image_parallel,
                ignore_cache: ignore_cache,
                is_secondary_color: is_secondary_color,
                nickname_index: nickname_index,
                period: period,
                period_start_date: periodStartDate,
                period_end_date: periodEndDate,
                period_split: periodSplit
            }, function (data) {
                showCardData(data)
            });
            return false;
        }
    });

})