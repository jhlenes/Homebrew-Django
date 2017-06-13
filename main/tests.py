import datetime

from django.db.models.aggregates import Sum
from django.test import TestCase
from django.utils import timezone
from django.utils.dateformat import format

from main.models import Batch, Point, Status, Measurement


def create_batch(batch_num, beer_type, start_date=timezone.now()):
    batch = Batch.objects.create(batch_num=batch_num, beer_type=beer_type, start_date=start_date, is_brewing=True)
    Status.objects.create(batch=batch, current_temp=0, is_heating=False)
    return batch


def add_points_to_batch(batch, points):
    i = 1
    for point in points:
        Point.objects.create(batch=batch, point_num=i, hours=point[0], temperature=point[1])
        i += 1


def add_measurements_to_batch(batch, time0, measurements):
    i = 1
    for measurement in measurements:
        time = time0 + datetime.timedelta(hours=measurement[0])
        Measurement.objects.create(batch=batch, time=time, temperature=measurement[1])


class PointMethodTests(TestCase):
    def test_as_time_temp_array(self):
        # create batch
        time = timezone.now()
        batch = create_batch(1, 'Beer', time)
        add_points_to_batch(batch, [[0, 2], [2, 4], [2, 4], [2, 6], [2, 6]])

        # point1
        point1 = batch.point_set.all().order_by('point_num')[0]
        self.assertEqual('[' + str(int(format(time, 'U')) * 1000) + ',2.0]', point1.as_time_temp_array())

        # point2
        point2 = batch.point_set.all().order_by('point_num')[1]
        expected = '[' + str((int(format(time, 'U')) + point2.hours * 3600) * 1000) + ',4.0]'
        self.assertEqual(expected, point2.as_time_temp_array())

        # point5
        point5 = batch.point_set.all().order_by('point_num')[4]
        hours = batch.point_set.all().aggregate(a=Sum('hours'))
        expected = '[' + str((int(format(time, 'U')) + hours['a'] * 3600) * 1000) + ',6.0]'
        self.assertEqual(expected, point5.as_time_temp_array())


class MeasurementMethodTests(TestCase):
    def test_as_time_temp_array(self):
        # create batch
        time = timezone.now()
        batch = create_batch(1, 'Beer', time)
        add_measurements_to_batch(batch, time, [[0, 2], [2, 4], [2, 4], [2, 6], [2, 6]])

        # measurement1
        measurement1 = batch.measurement_set.all().order_by('time')[0]
        expected = '[' + str(int(format(time, 'U')) * 1000) + ',2.0]'
        self.assertEqual(expected, measurement1.as_time_temp_array())

        # measurement2
        measurement2 = batch.measurement_set.all().order_by('time')[1]
        expected = '[' + str((int(format(time, 'U')) + 2 * 3600) * 1000) + ',4.0]'
        self.assertEqual(expected, measurement2.as_time_temp_array())
