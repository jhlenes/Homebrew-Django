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
            type: 'line'
        },
        title: {
            text: 'Beer type'
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
            name: 'Setpoint',
            data: [],
            color: '#434348',
            marker: {
                symbol: 'diamond'
            }
        }
        ],
        credits: {
            enabled: false
        },
        exporting: {
            enabled: false
        }
    });
});

$(document).ready(function () {
    var numFields = 2;
    var maxFields = 12;
    var wrapper = $(".insert_fields");

    var hourRule = {
        required: true,
        digits: true,
    };

    var tempRule = {
        required: true,
        number: true,
        min: 0.1
    };

    $('#newBatchForm').validate({ // initialize the plugin
        rules: {
            batch_num: hourRule,
            type: {
                required: true,
                minlength: 3
            },
            hour1: hourRule,
            hour2: hourRule,
            temp1: tempRule,
            temp2: tempRule
        }
    });

    jQuery.extend(jQuery.validator.messages, {
        required: "Required",
        minlength: jQuery.validator.format("Please enter a longer description."),
        min: jQuery.validator.format("Must be positive.")
    });

    $(".add_field").click(function (e) {  // If "Add point" button is clicked
        e.preventDefault();
        if (numFields < maxFields) {
            numFields++;
            // Add input field
            $(wrapper).append('<div class="6u"><input type="text" name="hour' + numFields + '" id="hour' + numFields + '" placeholder="Hour"/></div>');
            $('input[name="hour' + numFields + '"]').rules('add', hourRule);
            $(wrapper).append('<div class="6u"><input type="text" name="temp' + numFields + '" id="temp' + numFields + '" placeholder="Temperature"/></div>');
            $('input[name="temp' + numFields + '"]').rules('add', tempRule);
        }
    });

    $(".remove_field").click(function (e) { // If "Remove point" button is clicked
        e.preventDefault();
        if (numFields > 2) {
            $('input[name="temp' + numFields + '"]').rules('remove');
            wrapper.children().last().remove();
            $('input[name="hour' + numFields + '"]').rules('remove');
            wrapper.children().last().remove();

            if (typeof chart.series[0].data[numFields - 1] !== 'undefined') { // if point exists, delete it
                chart.series[0].data[numFields - 1].remove();
            }

            numFields--;
        }
    });

    $('form').on("blur", "input[id*='batch_num']", function () {
        if ($(this).attr('class') == 'error') {
            return;
        }
        chart.setSubtitle({
            text: "Batch #" + $(this).val() + ": " + moment().format('DD.MM.YYYY')
        });
    });

    $('form').on("blur", "input[id*='type']", function () {
        if ($(this).attr('class') == 'error') {
            return;
        }
        chart.setTitle({
            text: $(this).val()
        });
    });

    var points = new Array(maxFields);
    for (var i = 0; i < maxFields; i++) {
        points[i] = [-1, -1];
    }
    var currentDate = 1000 * parseInt(+new Date() / 1000); // milliseconds with seconds precision
    points[0][0] = currentDate;

    var getTime = function (num, hours) {
        var time = points[num - 2][0] + hours * 3600 * 1000;
        return time;
    };

    // This function is called everytime focus goes away from a insert field
    $('form').on("blur", "input[id^='hour']", function () {
        if ($(this).attr('class') == 'error') {
            return;
        }
        var num = parseInt($(this).attr('id').substring(4));  // Point number
        var time = getTime(num, parseInt($(this).val()));
        points[num - 1][0] = time;

        var temp = points[num - 1][1];
        if (temp != -1) {
            if (typeof chart.series[0].data[num - 1] !== 'undefined') { // if point already exists, update point
                chart.series[0].data[num - 1].update({
                    x: time,
                    y: temp
                }, false);

                // Update later points
                for (var i = num + 1; i < maxFields; i++) {
                    if (points[i - 1][0] !== -1) {
                        points[i - 1][0] = getTime(i, $('#hour' + i).val());
                        chart.series[0].data[i - 1].update({x: points[i - 1][0]}, false);
                    } else {
                        break;
                    }
                }
                chart.redraw();
            } else {  // Add point...
                if (num == 1 || chart.series[0].data.length == num - 1) { // only if previous point exists
                    chart.series[0].addPoint([time, temp]);
                }
            }
        }
    });

    $('form').on("blur", "input[id^='temp']", function () {
        if ($(this).attr('class') == 'error') {
            return;
        }
        var num = parseInt($(this).attr('id').substring(4));  // Point number
        var temp = parseFloat($(this).val());
        points[num - 1][1] = temp;

        var time = points[num - 1][0];
        if (time != -1) {
            if (typeof chart.series[0].data[num - 1] !== 'undefined') { // if point already exists, update point
                chart.series[0].data[num - 1].update({
                    x: time,
                    y: temp
                });
            } else {  // Add point
                if (num == 1 || chart.series[0].data.length == num - 1) { // only if previous point exists
                    chart.series[0].addPoint([time, temp]);
                }
            }
        }
    });


});

