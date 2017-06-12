import datetime

from django.db import models
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
            an array where each element is an array containing the time and temperature of a measure,
            i.e: [<time(millis)>, <temp(Celsius)>]
        """
        data = []
        if datetime is not None:
            for measurement in self.measurement_set.all().filter(time__gte=datetime).order_by('time'):
                data.append(measurement.as_time_temp_array())
        else:
            for measurement in self.measurement_set.all().order_by('time'):
                data.append(measurement.as_time_temp_array())
        return data

    def get_point_temp_time_array(self):
        """
        :returns:
            an array where each element is an array containing the time and temperature of a point,
            i.e: [<time(millis)>, <temp(Celsius)>]
        """
        setpoint = []
        for point in self.point_set.all().order_by('hours'):
            setpoint.append(point.as_time_temp_array())
        return setpoint

    def get_setpoint(self):
        """ Calculates the current setpoint based on the points.
        :returns:
            The setpoint if batch is brewing, else None.
        """
        if self.is_brewing:
            start_time = int(format(self.start_date, 'U'))
            now = int(format(datetime.datetime.now(), 'U'))
            hours_passed = (now - start_time) / 3600.0

            try:
                point1 = self.point_set.all().order_by('-hours').filter(hours__lte=hours_passed)[0]
                point2 = self.point_set.all().order_by('hours').filter(hours__gt=hours_passed)[0]

                derivative = (point2.temperature - point1.temperature) / float(point2.hours - point1.hours)
                setpoint = point1.temperature + derivative * (hours_passed - point1.hours)

                return setpoint
            except KeyError:
                self.is_brewing = False
                return None
        return None

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
            the measurement as an array of the form: [time(millis), temp(Celsius)]
        """
        # convert datetime to unix time and then to millis
        time_in_millis = int(format(self.time, 'U')) * 1000
        return [time_in_millis, self.temperature]


class Point(models.Model):
    batch = models.ForeignKey(Batch, on_delete=models.CASCADE)
    hours = models.IntegerField()
    temperature = models.FloatField()

    def __str__(self):
        return "Hour: {}, Temperature: {}{}".format(self.hours, self.temperature, '\u2103')

    def as_time_temp_array(self):
        """
        :returns:
            the point as an array of the form: [time(millis), temp(Celsius)]
        """
        # convert start date of batch to millis and add the hours from this point in millis
        time_in_millis = int(format(self.batch.start_date, 'U')) * 1000 + self.hours * 3600 * 1000
        return [time_in_millis, self.temperature]


class Status(models.Model):
    batch = models.OneToOneField(Batch, on_delete=models.CASCADE, primary_key=True)
    current_temp = models.FloatField()
    is_heating = models.BooleanField()

    def __str__(self):
        return "Temperature: {}{}, Heating: {}".format(self.current_temp, '\u2103', self.is_heating)

    class Meta:
        verbose_name_plural = "status"
