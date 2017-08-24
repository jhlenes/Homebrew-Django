import json

import requests
from django.db import models
from django.utils import timezone
from django.utils.dateformat import format


class Batch(models.Model):
    batch_num = models.IntegerField()
    beer_type = models.CharField(max_length=200)
    start_date = models.DateTimeField()
    is_brewing = models.BooleanField()

    def __str__(self):
        return "Batch #{}: {}".format(self.batch_num, self.beer_type)

    @staticmethod
    def get_latest():
        """
        :returns:
            The latest batch if available, else None.
        """
        batches = Batch.objects.all().order_by('-start_date')
        if batches.count() > 0:
            return batches[0]
        return None

    def get_measurement_temp_time_array(self, datetime=None):
        """
        :param datetime:
            use this if the user only wants the measurements after a given time
        :return:
            if datetime specified, returns an array of strings, else a string representation of the same array.
            Each element in the array is of the form: '[<time(millis)>,<temp(Celsius)>]'
        """
        if datetime is not None:
            data = []
            for measurement in self.measurement_set.all().filter(time__gte=datetime).order_by('time'):
                data.append(measurement.as_time_temp_array())
            return data
        else:
            data = '[' + ','.join([x.as_time_temp_array() for x in self.measurement_set.all().order_by('time')]) + ']'
            return data

    def get_point_temp_time_array(self):
        """
        :returns:
            a string representation of an array where each element is of the form: '[<time(millis)>,<temp(Celsius)>]'
        """
        data = '[' + ','.join([x.as_time_temp_array() for x in self.point_set.all().order_by('hours')]) + ']'
        return data

    def get_setpoint(self, time=False):
        """ Calculates the current setpoint based on the points.
        :returns:
            The setpoint if batch is brewing, else None.
        """
        if self.is_brewing:
            if not time:
                time = timezone.now()
            start_time = int(format(self.start_date, 'U'))
            now = int(format(time, 'U'))
            hours_passed = (now - start_time) / 3600.0

            point1 = None
            points = self.point_set.all().order_by('point_num')
            hours = 0.0
            for i in range(0, points.count()):
                point = points[i]
                hours += point.hours
                if hours > hours_passed:
                    point2 = point
                    point1 = points[i - 1]
                    break
            if point1 is None:
                self.is_brewing = False
                self.save()
                self.slackbot_send()
                return None

            derivative = (point2.temperature - point1.temperature) / float(point2.hours)
            setpoint = point1.temperature + derivative * (hours_passed - (hours - point2.hours))
            return setpoint

        return None

    def slackbot_send(self):
        webhook_url = 'https://hooks.slack.com/services/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'
        slack_data = {'text': "{} has finished brewing.".format(self)}
        requests.post(
            webhook_url, data=json.dumps(slack_data),
            headers={'Content-Type': 'application/json'}
        )

    class Meta:
        verbose_name_plural = "batches"


class Measurement(models.Model):
    batch = models.ForeignKey(Batch, on_delete=models.CASCADE)
    time = models.DateTimeField()
    temperature = models.FloatField()

    def __str__(self):
        return "Time: {}, Temperature: {}{}".format(self.time.strftime('%d.%m.%Y %H:%M:%S'), self.temperature, '\u2103')

    def as_time_temp_array(self):
        """
        :returns:
            the measurement as a string of the form: '[<time(millis)>,<temp(Celsius)>]'
        """
        # convert datetime to unix time and then to millis
        time_in_millis = int(format(self.time, 'U')) * 1000
        return ''.join(('[', str(time_in_millis), ',', str(self.temperature), ']'))


class Point(models.Model):
    batch = models.ForeignKey(Batch, on_delete=models.CASCADE)
    point_num = models.PositiveIntegerField()
    hours = models.PositiveIntegerField()
    temperature = models.FloatField()

    def __str__(self):
        return "Hour: {}, Temperature: {}{}".format(self.hours, self.temperature, '\u2103')

    def as_time_temp_array(self):
        """
        :returns:
            the point as a string of the form: '[<time(millis)>,<temp(Celsius)>]'
        """
        points = self.batch.point_set.all().filter(point_num__lt=self.point_num)
        hours = self.hours
        for point in points:
            hours += point.hours

        # convert start date of batch to millis and add the hours from this point in millis
        time_in_millis = int(format(self.batch.start_date, 'U')) * 1000 + hours * 3600 * 1000
        return ''.join(('[', str(time_in_millis), ',', str(self.temperature), ']'))

    class Meta():
        unique_together = ('batch', 'point_num',)


class Status(models.Model):
    batch = models.OneToOneField(Batch, on_delete=models.CASCADE, primary_key=True)
    current_temp = models.FloatField()
    is_heating = models.BooleanField()

    def __str__(self):
        return "Temperature: {}{}, Heating: {}".format(self.current_temp, '\u2103', self.is_heating)

    class Meta:
        verbose_name_plural = "status"
