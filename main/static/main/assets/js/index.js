// Create chart
$(function () {
    var zone = 'Europe/Oslo';
    var offset = -moment.tz(moment(), zone).utcOffset();

    Highcharts.setOptions({
        global: {
            timezoneOffset: offset
        }
    });
    chart = Highcharts.chart('highcharts_featured', {
        chart: {
            type: 'spline'
        },
        title: {
            text: 'No data available'
        },
        subtitle: {
            text: ''
        },
        xAxis: {
            type: 'datetime',
            labels: {
                overflow: 'justify'
            }
        },
        yAxis: {
            title: {
                text: 'Temperature (°C)'
            }
        },
        tooltip: {
            valueSuffix: ' °C'
        },
        plotOptions: {
            line: {
                dataLabels: {
                    enabled: false
                },
                enableMouseTracking: true
            }
        },
        series: [{
            name: 'Temperature',
            data: []
        }, {
            type: 'line',
            name: 'Setpoint',
            data: []
        }],
        credits: {
            enabled: false
        },
        exporting: {
            enabled: false
        }
    });
});

$(document).ready(function () {

    var batch_id = $('#highcharts_featured').data('batch_id');
    var last_update = new Date()

    var current_temp = 0.0;
    var is_heating = false;
    var is_brewing = false;

    // Continuously fetch new data for the chart
    var updater = function () {
        $.ajax({    //create an ajax request to new-data.html
            type: "GET",
            url: "new-data/?id=" + batch_id + "&time=" + last_update.toISOString(),
            success: function (response) {
                last_update = new Date();

                // the response is a javascript function which updates the chart with new values
                // and updates the variables defined above
                eval("(" + response + ")");

                // Update brewstatusbar
                if (is_brewing) {
                    $('#brewstatusbar').css('display', 'block');
                    $('#brewstatustitle').css('display', 'none');
                    $('#current_temp').text(current_temp);
                    if (is_heating) {
                        $('#is_heating').attr('class', 'icon fa-check').css('color', 'green');
                    } else {
                        $('#is_heating').attr('class', 'icon fa-times').css('color', 'red');
                    }
                } else {
                    $('#brewstatusbar').css('display', 'none');
                    $('#brewstatustitle').css('display', 'block');
                }

            }
        });
    };
    setInterval(updater, 30000);  // Call every 30 seconds

    $('.special.abortbutton').on("click", function () {

        if (confirm("Are you sure you want to abort this batch?")) {
            var batch_id = parseInt($('#highcharts_featured').data('batch_id'));
            $.ajax({
                type: "GET",
                url: "send/?id=" + batch_id + "&status=0",
                success: function (response) {
                    confirm("Batch aborted successfully!");
                    window.location.href = "";
                }
            });
        }
    });
});

