import datetime
import json

from django.db.models.aggregates import Sum
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from django.utils.dateformat import format

from main.models import Batch, Point, Status, Measurement


def create_batch(batch_num, beer_type, start_date=timezone.now()):
    batch = Batch.objects.create(batch_num=batch_num, beer_type=beer_type, start_date=start_date, is_brewing=True)
    Status.objects.create(batch=batch, current_temp=0.0, is_heating=False)
    return batch


def add_points_to_batch(batch, points):
    i = 1
    for point in points:
        Point.objects.create(batch=batch, point_num=i, hours=point[0], temperature=point[1])
        i += 1


def add_measurements_to_batch(batch, time0, measurements):
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


class BatchMethodTests(TestCase):
    def test_get_latest(self):
        time = timezone.now()
        batch = create_batch(3, 'Beer', time)
        batch2 = create_batch(2, 'Beer2', time + datetime.timedelta(hours=1))
        batch3 = create_batch(1, 'Beer2', time + datetime.timedelta(hours=-1))
        self.assertEqual(batch2, Batch.get_latest())

    def test_get_measurement_time_temp_array(self):
        # create batch
        time = timezone.now()
        batch = create_batch(1, 'Beer', time)
        add_measurements_to_batch(batch, time, [[0, 2], [2, 4]])

        # test without setting datetime
        m1 = batch.measurement_set.all().order_by('time')[0]
        m2 = batch.measurement_set.all().order_by('time')[1]
        self.assertEqual('[{},{}]'.format(m1.as_time_temp_array(), m2.as_time_temp_array()),
                         batch.get_measurement_temp_time_array())

        # test with setting datetime, only measurements after the time should be returned
        add_measurements_to_batch(batch, time, [[6, 4], [7, 2]])
        m3 = batch.measurement_set.all().order_by('time')[2]
        m4 = batch.measurement_set.all().order_by('time')[3]
        self.assertEqual([m3.as_time_temp_array(), m4.as_time_temp_array()],
                         batch.get_measurement_temp_time_array(time + datetime.timedelta(hours=5)))

    def test_get_point_temp_time_array(self):
        # create batch
        time = timezone.now()
        batch = create_batch(1, 'Beer', time)
        add_points_to_batch(batch, [[0, 2], [2, 4]])

        p1 = batch.point_set.all().order_by('point_num')[0]
        p2 = batch.point_set.all().order_by('point_num')[1]
        self.assertEqual('[{},{}]'.format(p1.as_time_temp_array(), p2.as_time_temp_array()),
                         batch.get_point_temp_time_array())

    def test_get_setpoint(self):
        # create batch
        time = timezone.now()
        batch = create_batch(1, 'Beer', time)
        add_points_to_batch(batch, [[0, 2], [2, 4], [2, 4], [2, 6], [2, 6]])

        # cases where batch is brewing
        self.assertAlmostEqual(2, batch.get_setpoint())
        self.assertAlmostEqual(3, batch.get_setpoint(time + datetime.timedelta(hours=1)), delta=0.01)
        self.assertAlmostEqual(4, batch.get_setpoint(time + datetime.timedelta(hours=2)), delta=0.01)
        self.assertAlmostEqual(4, batch.get_setpoint(time + datetime.timedelta(hours=2.5)), delta=0.01)
        self.assertAlmostEqual(4.5, batch.get_setpoint(time + datetime.timedelta(hours=4.5)), delta=0.01)
        self.assertAlmostEqual(5, batch.get_setpoint(time + datetime.timedelta(hours=5)), delta=0.01)
        self.assertAlmostEqual(6, batch.get_setpoint(time + datetime.timedelta(hours=7)), delta=0.01)
        self.assertAlmostEqual(6, batch.get_setpoint(time + datetime.timedelta(hours=7.9)), delta=0.01)

        # batch is not brewing
        self.assertEqual(None, batch.get_setpoint(time + datetime.timedelta(hours=8.1)))
        self.assertEqual(None, batch.get_setpoint(time + datetime.timedelta(hours=100)))


class IndexViewTests(TestCase):
    def test_index_view_with_no_batch(self):
        response = self.client.get(reverse('main:index'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "<h2>Latest batch</h2>")

    def test_index_view_with_finished_batch(self):
        # create batch
        time = timezone.now()
        batch = create_batch(1, 'Beer', time + datetime.timedelta(hours=-100))
        batch.is_brewing = False
        batch.save()
        add_points_to_batch(batch, [[0, 2], [2, 4], [2, 4], [2, 6], [2, 6]])

        response = self.client.get(reverse('main:index'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "<h2>Latest batch</h2>")

    def test_index_view_with_active_batch(self):
        # create batch
        time = timezone.now()
        batch = create_batch(1, 'Beer', time + datetime.timedelta(hours=3))
        add_points_to_batch(batch, [[0, 2], [2, 4], [2, 4], [2, 6], [2, 6]])

        response = self.client.get(reverse('main:index'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '<span id="current_temp">0.0</span>')
        self.assertContains(response, '<span id="is_heating" style="color:red " class="icon fa-times"></span>')


class ReceiveViewTests(TestCase):
    def test_receive_view(self):
        time = timezone.now() + datetime.timedelta(hours=-1)
        batch = create_batch(1, 'Beer', time)
        add_points_to_batch(batch, [[0, 2], [2, 4], [2, 4], [2, 6], [2, 6]])

        # cases where batch is brewing
        response = self.client.get(reverse('main:receive'))
        self.assertContains(response, '{"batch_id": 1, "setpoint": 3.')  # rest emitted because float

        batch.start_date = time + datetime.timedelta(hours=-6)
        batch.save()
        response = self.client.get(reverse('main:receive'))
        self.assertContains(response, '{"batch_id": 1, "setpoint": 6.')  # rest emitted because float

        # batch is not brewing
        batch.start_date += datetime.timedelta(hours=-100)
        batch.save()
        response = self.client.get(reverse('main:receive'))
        self.assertContains(response, '{"batch_id": -1}')


class SendViewTests(TestCase):
    def test_send_view(self):
        # create batch
        time = timezone.now()
        batch = create_batch(1, 'Beer', time)
        add_points_to_batch(batch, [[0, 2], [2, 4], [2, 4], [2, 6], [2, 6]])

        response = self.client.get(reverse('main:send'), {
            'id': 1,
            'temp': 2.2,
            'heating': 1
        })
        batch = Batch.get_latest()
        self.assertContains(response, 'OK')
        self.assertEqual(batch.measurement_set.all()[0].temperature, 2.2)
        self.assertEqual(batch.status.current_temp, 2.2)
        self.assertEqual(batch.status.is_heating, 1)

        response = self.client.get(reverse('main:send'), {
            'id': 1,
            'status': -1
        })
        batch = Batch.get_latest()
        self.assertContains(response, 'OK')
        self.assertEqual(batch.is_brewing, False)

        response = self.client.get(reverse('main:send'), {
            'id': 1,
            'temp': 1.1
        })
        self.assertContains(response, 'Batch is not active')

        response = self.client.get(reverse('main:send'), {
            'id': 5,
            'temp': 27.2,
            'heating': 1
        })
        self.assertEqual(response.status_code, 404)

        response = self.client.get(reverse('main:send'))
        self.assertEqual(response.status_code, 400)
