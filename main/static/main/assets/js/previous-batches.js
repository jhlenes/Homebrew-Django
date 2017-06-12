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
            text: ''
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

    $("#batchesTable").tablesorter({
        dateFormat: "dd.mm.yyyy",
        sortList: [[2, 1]] // Sort on third column, order descending.
    });

    $('#batchesTable tbody').on("click", "tr", function () {
        var batchId = parseInt($(this).children().first().data('batch_id'));
        window.location.href = url + '?id=' + batchId;
    });

});


