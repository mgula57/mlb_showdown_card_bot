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
function cacheObject(key, object) {
    // Check if the localStorage object exists
    if(localStorage) {
        // Store data
        localStorage.setItem(key, object);
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

function changeImageSection(imageSelectObject) {
    var selection = imageSelectObject.value;
    for (const section of ['auto', 'link', 'upload']) { 
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
            document.getElementById(date).value = yearText + document.getElementById(date).value.slice(4);
        }
    }
}

// ON CHANGE OF SET INPUT
function changeSetSelection(newSet) {
    updatedSet = newSet.value;
    localStorage.setItem('set', updatedSet);
    console.log(updatedSet);
    // CHECK WHAT src OF CARD_IMAGE IS
    if (document.getElementById('card_image').src.includes('interface')) {
        const theme = localStorage.getItem('theme') || 'light';
        const suffix = (theme == 'dark') ? '-Dark' : '';
        document.getElementById('card_image').src = `static/interface/BlankPlayer-${updatedSet}${suffix}.png`;
    }
}

// THEME
function toggleTheme() {
    var currentTheme = localStorage.getItem('theme') || 'light';
    var newTheme = (currentTheme == 'light') ? 'dark' : 'light';
    setTheme(newTheme);
}

// -------------------------------------------------------
// CHARTS
// -------------------------------------------------------

// SETUP TRENDS CHART
function createTrendsChart(data, trends_data, elementId, unit, is_placeholder=false, events=["mousemove", "mouseout", "click", "touchstart", "touchmove", "touchend"]) {

    if (trends_data == null) {
        return;
    }

    // UPDATE TEXT IN LABEL FOR playerInSeasonTrends TO DISPLAY THE YEAR FROM data
    if (elementId == "playerInSeasonTrends") {
        const year = is_placeholder ? "Year" : data.player_year;
        document.getElementById("in_season_trend_label").textContent = `${year} Card Evolution`;
    }
    
    // DESTROY EXITING CHART INSTANCE TO REUSE <CANVAS> ELEMENT
    let chartStatus = Chart.getChart(elementId);
    if (chartStatus != undefined) {
        chartStatus.destroy();
    }
    
    // CREATE NEW CHART OBJECT
    var marksCanvas = document.getElementById(elementId);
    var color = Chart.helpers.color;

    // PARSE VALUES
    var xValues = []
    var yValues = []
    var customAttributes = []
    for (let day in trends_data) {
        xValues.push(day);
        yValues.push(trends_data[day]["points"]);
        customAttributes.push(trends_data[day]);
    }

    const myChart = new Chart(marksCanvas, {
        type: "line",
        data: {
            labels: xValues,
            datasets: [{
                data: yValues,
                label: "PTS",
                fill: true,
                customData: customAttributes,
                tension: 0.4,
                // Scriptable option for point radius with a condition
                pointRadius: (context) => {
                    if (is_placeholder) {
                        return 0;
                    }
                    const dataPoint = context.dataset.customData[context.dataIndex];
                    return (dataPoint.year === data.player_year && unit == 'year') ? 6 : 3;
                },
                // Scriptable option for point background color with a condition
                pointBackgroundColor: (context) => {
                    const dataPoint = context.dataset.customData[context.dataIndex];
                    return color(dataPoint.color).alpha(0.9).rgbString();
                },
                segment: {
                    // Use ctx.p0DataIndex (the starting point of the segment) to get the correct color
                    borderColor: (ctx) => {
                        const dataIndex = ctx.p0DataIndex; // Access the starting point's index
                        return color(customAttributes[dataIndex].color).rgbString(); // Access the fill color for the segment
                    },
                    backgroundColor: (ctx) => {
                        const dataIndex = ctx.p0DataIndex; // Access the starting point's index
                        return color(customAttributes[dataIndex].color).alpha(0.4).rgbString(); // Access the fill color for the segment
                    }
                }
            }]
        },
        options: {
            events: events,
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                mode: 'index',  // Tooltip should show for all elements in the same index (hovering over empty space will show the tooltip for the closest data)
                intersect: false // Ensures tooltip is triggered even if not directly over a point or bar
            },
            animation: {
                onComplete: function () {
                    if (is_placeholder) {
                        const chart = myChart;
                        const ctx = chart.ctx;
                        ctx.save();
                        ctx.font = "bold 24px Arial";
                        ctx.fillStyle = "rgba(116, 116, 116, 0.7)";
                        ctx.textAlign = "center";
                        ctx.textBaseline = "middle";
                        ctx.fillText("NO DATA", chart.width / 2, chart.height / 2);
                        ctx.restore();
                    }
                }
            },
            plugins: {
                legend: {
                    display: false
                },
                // Configure the Data Labels plugin:
                datalabels: {
                    display: (context) => {
                        // Only display when condition is met
                        const dataPoint = context.dataset.customData[context.dataIndex];
                        return dataPoint.year === data.player_year && unit == 'year';
                    },
                    formatter: (value, context) => {
                        // Return whatever label you want to show—e.g., the year or custom text
                        const dataPoint = context.dataset.customData[context.dataIndex];
                        return dataPoint.points; // or "Your Label" or any custom formatting
                    },
                    anchor: 'end',  // Position label at the end of the point
                    align: 'top',   // Align label above the point
                    color: 'black', // Label text color (adjust as needed)
                    font: {
                        weight: 'bold'
                    }
                },
                tooltip: {
                    intersect: false,
                    displayColors: false,
                    callbacks: {
                        title: function(tooltipItems) {
                            const tooltipItem = tooltipItems[0];
                            const dataset = tooltipItem.dataset;
                            const index = tooltipItem.dataIndex;
                            const dataDict = dataset.customData[index]; // Get dict for the data point
                            return `${tooltipItem.label} ${dataDict.team}: ${tooltipItem.raw} PTS`
                        },
                        label: function(tooltipItem) {
                            const dataset = tooltipItem.dataset;
                            const index = tooltipItem.dataIndex;
                            const dataDict = dataset.customData[index]; // Get dict for the data point
                            
                            // Convert dict to an array of strings (each key-value pair on a new line)
                            let tooltipLines = [];
                            for (const [key, value] of Object.entries(dataDict)) {
                                if (!['team', 'points', 'year', 'color'].includes(key)) {
                                    tooltipLines.push(`${key.toUpperCase()}: ${value}`);
                                }
                            }
    
                            return tooltipLines; // Returning an array displays each entry on a new line
                        }
                    }
                }
            },
            scales: {
              x: {
                type: 'time',
                time: {
                    unit: unit,
                    parser: unit == 'day' ? 'yyyy-MM-dd' : 'yyyy',
                    displayFormats: {
                        unit: unit == 'day' ? 'MMM dd' : 'yyyy',
                    },
                    tooltipFormat: unit == 'day' ? 'MMM dd' : 'yyyy'
                },
                ticks: {
                    font: {
                        size: 10 // Smaller font size for x-axis ticks
                    }
                }
              },
              y: {
                min: 0,
                max: Math.ceil( (Math.max(...yValues) + 50) / 200 ) * 200,
                ticks: {
                    font: {
                        size: 10 // Smaller font size for x-axis ticks
                    }
                }
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

function buildGenericChartPlaceholders() {
    data = {
        player_year: "", // SO YEAR NEVER MATCHES
    };
    light_gray_color = 'rgba(158, 158, 158, 0.08)';
    generic_career_data = {
        '2013': {'color': light_gray_color, 'points': 120, },
        '2014': {'color': light_gray_color, 'points': 160, },
        '2015': {'color': light_gray_color, 'points': 280, },
        '2016': {'color': light_gray_color, 'points': 230, },
        '2017': {'color': light_gray_color, 'points': 310, },
        '2018': {'color': light_gray_color, 'points': 320, },
        '2019': {'color': light_gray_color, 'points': 330, },
        '2020': {'color': light_gray_color, 'points': 440, },
        '2021': {'color': light_gray_color, 'points': 480, },
        '2022': {'color': light_gray_color, 'points': 520, },
        '2023': {'color': light_gray_color, 'points': 400, },
        '2024': {'color': light_gray_color, 'points': 420, },
        '2025': {'color': light_gray_color, 'points': 320, },
    };
    generic_in_season_data = {
        '2025-03-30': { 'color': light_gray_color, 'points': 150 },
        '2025-04-06': { 'color': light_gray_color, 'points': 110 },
        '2025-04-13': { 'color': light_gray_color, 'points': 160 },
        '2025-04-20': { 'color': light_gray_color, 'points': 250 },
        '2025-04-27': { 'color': light_gray_color, 'points': 270 },
        '2025-05-04': { 'color': light_gray_color, 'points': 280 },
        '2025-05-11': { 'color': light_gray_color, 'points': 250 },
        '2025-05-18': { 'color': light_gray_color, 'points': 230 },
        '2025-05-25': { 'color': light_gray_color, 'points': 200 },
        '2025-06-01': { 'color': light_gray_color, 'points': 270 },
        '2025-06-08': { 'color': light_gray_color, 'points': 330 },
        '2025-06-15': { 'color': light_gray_color, 'points': 350 },
        '2025-06-22': { 'color': light_gray_color, 'points': 350 },
        '2025-06-29': { 'color': light_gray_color, 'points': 370 },
        '2025-07-06': { 'color': light_gray_color, 'points': 320 },
        '2025-07-13': { 'color': light_gray_color, 'points': 350 },
        '2025-07-20': { 'color': light_gray_color, 'points': 400 },
        '2025-07-27': { 'color': light_gray_color, 'points': 470 },
        '2025-08-03': { 'color': light_gray_color, 'points': 450 },
        '2025-08-10': { 'color': light_gray_color, 'points': 480 },
        '2025-08-17': { 'color': light_gray_color, 'points': 500 },
        '2025-08-24': { 'color': light_gray_color, 'points': 520 },
        '2025-08-31': { 'color': light_gray_color, 'points': 550 },
        '2025-09-07': { 'color': light_gray_color, 'points': 500 },
        '2025-09-14': { 'color': light_gray_color, 'points': 510 },
        '2025-09-21': { 'color': light_gray_color, 'points': 510 },
        '2025-09-28': { 'color': light_gray_color, 'points': 520 }
    };

    createTrendsChart(data=data, trends_data=generic_career_data, elementId="playerCareerTrends", unit='year', is_placeholder=true, events=[]);
    createTrendsChart(data=data, trends_data=generic_in_season_data, elementId="playerInSeasonTrends", unit='day', is_placeholder=true, events=[]);
}

function setTheme(themeName) {
    // UPDATE LOCAL STORAGE
    localStorage.setItem('theme', themeName);

    var is_dark = themeName == 'dark'
    // ALTER CONTAINERS
    containers_to_alter = [
        "container_bg", "overlay", "input_container_column", "input_container",
        "main_body", "breakdown_output", 
        "estimated_values_footnote", "chart_adjustments_footnote", "points_breakdown_footnote", "opponent_values_footnote", 
        "loader_container_rectangle",
    ]
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
        "points_table", "chart_versions_table", "rank_table", "opponent_table", "eraSelection", "breakdownSelection", 
        "imageTypeSelection", "parallelSelection", "periodSelection", "start_date", "end_date", "split"
    ]
    for (const id of form_inputs_to_alter) {
        var element = document.getElementById(id);
        if (element === null) {
            continue;
        }
        var current_name = element.className
        const is_text_only = ["darkModeToggleLabel", "varSpdToggleLabel", "addBorderLabel", "darkThemeToggleLabel"].includes(id)
        const is_table = ["stats_table", "points_table", "chart_versions_table", "rank_table", "opponent_table"].includes(id)
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
        var set = localStorage.getItem('set') || '2000';
        document.getElementById('card_image').src = `static/interface/BlankPlayer-${set}${suffix}.png`;
    }
}

function showCardData(data) {

    // THEME
    var storedTheme = localStorage.getItem('theme') || 'light';
    const is_dark = storedTheme == 'dark'

    // HIDE OVERLAY
    $('#overlay').hide();
    
    // CHECK FOR ERROR
    $('#message_string').hide();
    $("#message_string").text(data.error);
    const isError = data.error !== null & data.image_path === null;
    if (isError) {
        document.getElementById("message_string").style.color = "red";
        $('#message_string').show();
    }
    
    // CHANGE ERROR TO ORANGE IF WARNING
    if (data.image_path & data.error) {
        $('#message_string').show();
        document.getElementById("message_string").style.color = "orange";
    }

    // CHANGE CARD IMAGE
    var storedSet = localStorage.getItem('set') || '2000';
    $("#card_image").attr('src', data.image_path || `static/interface/BlankPlayer-${storedSet}${(is_dark) ? '-Dark' : ''}.png`);
    
    // ADD HYPERLINK TO BREF
    if (data.player_name) {
        $("#player_name").show();
        $("#player_name").text(data.player_name.toUpperCase());

        // ADD CHILDREN TO PLAYER DETAILS DIV
        // CLEAR OUT PLAYER DETAILS DIV
        $("#player_details_div").empty();
        $("#player_details_div").show();
        const attributes = ['player_year', 'period']
        for (const attr_type of attributes) { 
            var attr_text = data[attr_type];
            if (attr_type in ['period']) {
                attr_text = `${attr_type}: ${attr_text}`;
            }
            $("#player_details_div").append(`<div class="player_attribute_box">${attr_text}</div>`);
        }

    } else {
        $("#player_name").hide();
        $("#player_details_div").hide();
    }

    // TRENDS GRAPHS
    if (isError) {
        buildGenericChartPlaceholders();
    } else {
        createTrendsChart(data=data, trends_data=data.yearly_trends_data, elementId="playerCareerTrends", unit='year');
        createTrendsChart(data=data, trends_data=data.in_season_trends_data, elementId="playerInSeasonTrends", unit='day'); 
    }
    
    // VAR NEEDED FOR TABLE CLASSES
    var table_class_suffix = (storedTheme == 'dark') ? " table-dark" : ""
    var table_class_name = "table table-striped table-bordered" + table_class_suffix
    
    // PLAYER STATS
    var player_stats_table = "<table class='" + table_class_name + "' id='stats_table'><tr><th> </th> <th>Real</th> <th>Bot</th> <th>Diff</th> </tr>";
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
    var player_points_table = "<table class='" + table_class_name + "' id='points_table'><tr> <th>Category</th> <th>Stat</th> <th>Pts</th> <th>Pctile</th> </tr>";
    $.each(data.player_points, function (index, value) {
        is_total_row = (data.player_points.length - 1) == index | (data.player_points.length - 2) == index;
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
    var player_chart_versions_table = "<table class='" + table_class_name + "' id='chart_versions_table'><tr> <th>Version</th> <th>Accuracy</th> <th>OPS</th> <th>Notes</th> </tr>";
    $.each(data.player_chart_versions, function (index, value) {
        player_chart_versions_table += '<tr>'
        $.each(value, function (index, value) {
            if (index == 0) {
                bold_start = '<b>';
                bold_end = '</b>';
            } else {
                bold_start = '';
                bold_end = '';
            }
            player_chart_versions_table += '<td>' + bold_start + value + bold_end + '</td>';
        });
        player_chart_versions_table += '</tr>';
    });
    player_chart_versions_table += '</table>';
    $("#chart_versions_table").replaceWith(player_chart_versions_table);

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
        var storedTheme = localStorage.getItem('theme') || 'light';
        setTheme(storedTheme);
        // CHECK FOR LAST SELECTED TAB
        selectedTab = localStorage.getItem("tab");
        if (!selectedTab) {
            selectedTab = "create";
            localStorage.setItem('tab', selectedTab);
        }

        // POPULATE LAST CARD SETTINGS
        lastCard = localStorage.getItem("last_card");
        if (selectedTab == "create" && lastCard) {
            //
            lastCardJson = JSON.parse(lastCard);
            
            // FOR NOW MANUALLY SETTING VALUES
            // WHEN FRONT END IS UPGRADED, THIS WILL BE REPLACED

            // NAME AND YEAR
            // DONT APPLY FOR FIRST RELEASE. GET FEEDBACK ON THIS
            // document.getElementById("name").value = lastCardJson.name;
            // document.getElementById("year").value = lastCardJson.year;

            // STATS PERIOD
            document.getElementById("periodSelection").value = lastCardJson.period;
            // document.getElementById("date-start").value = lastCardJson.period_start_date;
            // document.getElementById("date-end").value = lastCardJson.period_end_date;
            document.getElementById("split").value = lastCardJson.period_split;

            // ERA, EXPANSION, EDITION
            document.getElementById("eraSelection").value = lastCardJson.era;
            document.getElementById("expansionSelection").value = lastCardJson.expansion;
            document.getElementById("editionSelection").value = lastCardJson.edition;

            // CHART VERSION AND SET NUMBER
            document.getElementById("chartVersionSelection").value = lastCardJson.offset;
            document.getElementById("setnum").value = lastCardJson.set_num;

            // IMAGE
            document.getElementById("parallelSelection").value = lastCardJson.parallel;
            document.getElementById("url").value = lastCardJson.url;

            // MORE OPTIONS
            var moreOptionsSelections = [];
            if (lastCardJson.is_variable_spd_00_01) { moreOptionsSelections.push("VariableSpeed"); }
            if (lastCardJson.addBorder) { moreOptionsSelections.push("Border"); }
            if (lastCardJson.is_dark_mode) { moreOptionsSelections.push("DarkMode"); }
            if (lastCardJson.hide_team_logo) { moreOptionsSelections.push("HideTeamBranding"); }
            if (lastCardJson.is_secondary_color) { moreOptionsSelections.push("SecondaryColor"); }
            if (lastCardJson.is_multi_colored) { moreOptionsSelections.push("MultiColor"); }
            if (lastCardJson.show_year_text) { moreOptionsSelections.push("YearContainer"); }
            if (lastCardJson.set_year_plus_one) { moreOptionsSelections.push("SetYearPlus1"); }
            if (lastCardJson.ignore_cache) { moreOptionsSelections.push("IgnoreCache"); }

            if (lastCardJson.stat_highlights_type == "ALL") {
                moreOptionsSelections.push("StatHighlightsModern");
                moreOptionsSelections.push("StatHighlightsOldSchool");
            } else if (lastCardJson.stat_highlights_type == "MODERN") {
                moreOptionsSelections.push("StatHighlightsModern");
            } else if (lastCardJson.stat_highlights_type == "OLD_SCHOOL") {
                moreOptionsSelections.push("StatHighlightsOldSchool");
            }

            if (lastCardJson.nickname_index) {
                if (lastCardJson.nickname_index == 1) { moreOptionsSelections.push("Nickname-1"); }
                if (lastCardJson.nickname_index == 2) { moreOptionsSelections.push("Nickname-2"); }
                if (lastCardJson.nickname_index == 3) { moreOptionsSelections.push("Nickname-3"); }
            }

            if (lastCardJson.glow_multiplier) {
                if (lastCardJson.glow_multiplier == 2) { moreOptionsSelections.push("Glow-2"); }
                if (lastCardJson.glow_multiplier == 3) { moreOptionsSelections.push("Glow-3"); }
            }

            $('.selectpicker').selectpicker('val', moreOptionsSelections);

        }
    }
    // SET TABS
    setupTabs(selectedTab);

    // DEFAULT CHARTS
    buildGenericChartPlaceholders();
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
            var is_multi_colored = moreOptionsSelected.includes("MultiColor");

            // NICKNAME INDEX
            var nickname_index = null;
            if (moreOptionsSelected.includes("Nickname-1")) {
                nickname_index = 1;
            } else if (moreOptionsSelected.includes("Nickname-2")) {
                nickname_index = 2
            } else if (moreOptionsSelected.includes("Nickname-3")) {
                nickname_index = 3
            }

            var glow_multiplier = null;
            if (moreOptionsSelected.includes("Glow-3")) {
                glow_multiplier = 3;
            } else if (moreOptionsSelected.includes("Glow-2")) {
                glow_multiplier = 2;
            }

            // STAT HIGHLIGHTS
            var is_stat_highlights_modern = moreOptionsSelected.includes("StatHighlightsModern");
            var is_stat_highlights_old_school = moreOptionsSelected.includes("StatHighlightsOldSchool");
            var stat_highlights = "NONE"
            if (is_stat_highlights_modern & is_stat_highlights_old_school) {
                stat_highlights = "ALL";
            } else if (is_stat_highlights_modern) {
                stat_highlights = "MODERN";
            } else if (is_stat_highlights_old_school) {
                stat_highlights = "OLD_SCHOOL";
            }
            
            // PERIOD
            var period = $("#periodSelection :selected").val();
            var periodStartDate = $('input[name="date-start"]').val()
            var periodEndDate = $('input[name="date-end"]').val()
            var periodSplit = $('input[name="split"]').val()

            // SET NUMBER AND EXPANSION
            set_num = $('input[name="setnum"]').val()
            expansion = $("#expansionSelection :selected").val()
            
            // CACHE SET VALUE
            var set = $("#setSelection :selected").val()
            cacheObject("set", set)

            // STORE LAST CREATE CARD SETTINGS
            var card_object = {
                name: name,
                year: year,
                set: set,
                edition: edition,
                url: image_link,
                img_name: image_name,
                set_num: set_num,
                offset: selectedOffset,
                expansion: expansion,
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
                is_multi_colored: is_multi_colored,
                nickname_index: nickname_index,
                period: period,
                period_start_date: periodStartDate,
                period_end_date: periodEndDate,
                period_split: periodSplit,
                stat_highlights_type: stat_highlights,
                glow_multiplier: glow_multiplier
            }
            cacheObject("last_card", JSON.stringify(card_object))

            $.getJSON('/card_creation', card_object, function (data) {
                showCardData(data)
            });
            return false;
        }
    });

})