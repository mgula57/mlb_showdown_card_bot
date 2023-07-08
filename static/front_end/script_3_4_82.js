
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
    for (const section of ['link', 'upload']) { 
        console.log(section)
        if (section == selection) {
            $("#" + section).show();
        } else {
            $("#" + section).hide();
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

    form_inputs_to_alter = ["name", "year", "setSelection", "expansionSelection", "editionSelection", "moreOptionsSelect", "setnum", "chartVersionSelection", "darkThemeToggleLabel", "url", "img_upload", "stats_table", "points_table", "accuracy_table","rank_table", "opponent_table", "eraSelection", "breakdownSelection", "imageTypeSelection"]
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
        document.getElementById("error").style.color = "orange";

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
            $("#player_link").text(`Set: ${data.player_context} | ${data.era} | Year(s):`);
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
            uploadImageFile();
            var files = $('#img_upload').prop('files');
            var image_name = ""
            if (files.length > 0) {
                image_name = files[0].name;
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
            var add_year_container = moreOptionsSelected.includes("YearContainer");
            var set_year_plus_one = moreOptionsSelected.includes("SetYearPlus1");
            var hide_team_branding = moreOptionsSelected.includes("HideTeamBranding");
            var is_variable_spd = moreOptionsSelected.includes("VariableSpeed");
            var ignore_showdown_library = moreOptionsSelected.includes("IgnoreShowdownLibrary");
            
            // CACHE SET VALUE
            var set = $("#setSelection :selected").val()
            cacheSet(set)

            $.getJSON('/card_creation', {
                name: name,
                year: year,
                set: set,
                edition: edition,
                url: $('input[name="url"]').val(),
                img_name: image_name,
                set_num: $('input[name="setnum"]').val(),
                offset: selectedOffset,
                expansion: $("#expansionSelection :selected").val(),
                addBorder: is_border,
                is_dark_mode: is_dark_mode,
                is_variable_spd_00_01: is_variable_spd,
                is_foil: is_foil,
                add_year_container: add_year_container,
                set_year_plus_one: set_year_plus_one,
                hide_team_logo: hide_team_branding,
                ignore_showdown_library: ignore_showdown_library,
                era: era,
            }, function (data) {
                showCardData(data)
            });
            return false;
        }
    });

})