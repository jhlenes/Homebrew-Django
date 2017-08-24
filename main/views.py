import json

from django.http.response import HttpResponse, HttpResponseRedirect, HttpResponseBadRequest
from django.shortcuts import render, get_object_or_404
from django.urls import reverse
from django.utils import timezone

from main.models import Measurement, Point, Status
from .models import Batch


def index(request):
    batch = Batch.get_latest()
    if batch is not None:
        measurements = batch.get_measurement_temp_time_array()
        setpoints = batch.get_point_temp_time_array()
        return render(request, 'main/index.html', {
            'batch': batch,
            'measurements': measurements,
            'setpoints': setpoints,
        })
    else:
        return render(request, 'main/index.html')


def new_data(request):
    try:
        batch = get_object_or_404(Batch, pk=request.GET['id'])
        data = batch.get_measurement_temp_time_array(request.GET['time'])
        return render(request, 'main/new-data.html', {
            'data': data,
            'status': batch.status,
            'is_brewing': batch.is_brewing,
        })
    except (KeyError, Batch.DoesNotExist):
        return HttpResponseBadRequest("Bad Request: Specify 'id' and 'time'")


def send(request):
    # TODO: CHANGE TO POST
    batch_id = request.GET.get('id', False)
    if not batch_id:
        return HttpResponseBadRequest("Bad Request: Specify 'id'")
    batch = get_object_or_404(Batch, pk=batch_id)

    if batch.is_brewing:
        temp = request.GET.get('temp', False)
        if temp:
            temp = float(temp)
            if 'update' not in request.GET:  # if update don't add measurement
                measurement = Measurement(batch=batch, time=timezone.now(), temperature=temp)
                measurement.save()
            batch.status.current_temp = temp
            batch.status.save(update_fields=['current_temp'])

        is_heating = request.GET.get('heating', False)
        if is_heating:
            is_heating = int(is_heating) == 1
            batch.status.is_heating = is_heating
            batch.status.save(update_fields=['is_heating'])

        status = request.GET.get('status', False)
        if status:
            status = int(status) == 1
            batch.is_brewing = status
            batch.save(update_fields=['is_brewing'])

        return HttpResponse("OK")
    else:
        return HttpResponse("Batch is not active")


def new_batch(request):
    batch_num = request.POST.get('batch_num', False)
    if not batch_num:
        return render(request, 'main/new-batch.html')
    beer_type = request.POST['type']
    batch = Batch(batch_num=batch_num, beer_type=beer_type, start_date=timezone.now(), is_brewing=True)

    # Stop last batch if brewing
    last_batch = Batch.get_latest()
    if last_batch is not None and last_batch.is_brewing:
        last_batch.is_brewing = False
        last_batch.save()

    batch.save()

    points = []
    for key in request.POST:
        if len(key) >= 4 and key[:4] == 'hour':
            num = int(key[4:])
            hour = int(request.POST[key])
            temp = float(request.POST['temp' + str(num)])
            points.append(Point(batch=batch, point_num=num, hours=hour, temperature=temp))

    for point in points:
        point.save()

    batch.status = Status(batch=batch, current_temp=0, is_heating=False)
    batch.status.save()

    return HttpResponseRedirect(reverse('main:index'))


def previous_batches(request):
    batch_id = request.GET.get('id', False)
    if batch_id:
        batch = Batch.objects.get(id=batch_id)
        measurements = batch.get_measurement_temp_time_array()
        setpoints = batch.get_point_temp_time_array()

        return render(request, 'main/previous-batches.html', {
            'batch': batch,
            'measurements': measurements,
            'setpoints': setpoints,
            'batches': Batch.objects.all().order_by('-start_date'),
        })
    return render(request, 'main/previous-batches.html', {
        'batches': Batch.objects.all().order_by('-start_date'),
    })


def receive(request):
    """ Prints the batch_id and current setpoint, if available, in json format """
    batch = Batch.get_latest()
    if batch is not None:
        setpoint = batch.get_setpoint()
        if setpoint is not None:
            return HttpResponse(json.dumps({
                'batch_id': batch.id,
                'setpoint': setpoint
            }))
    return HttpResponse(json.dumps({'batch_id': -1}))
