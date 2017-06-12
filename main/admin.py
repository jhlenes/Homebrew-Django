from django.contrib import admin

from .models import Batch, Measurement, Point, Status


class MeasurementInline(admin.TabularInline):
    model = Measurement
    extra = 3


class PointInline(admin.TabularInline):
    model = Point
    extra = 3


class StatusInline(admin.TabularInline):
    model = Status


class BatchAdmin(admin.ModelAdmin):
    fieldsets = [
        ('Batch details', {'fields': ['batch_num', 'beer_type', 'start_date', 'is_brewing']})
    ]
    inlines = [StatusInline, MeasurementInline, PointInline]
    list_display = ('batch_num', 'beer_type', 'start_date', 'is_brewing')
    list_display_links = ('batch_num', 'beer_type')
    list_filter = ['start_date']
    search_fields = ['beer_type']


admin.site.register(Batch, BatchAdmin)
