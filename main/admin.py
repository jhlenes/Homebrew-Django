from django.contrib import admin

from .models import Batch, Measurement, Point, Status


class PointInline(admin.TabularInline):
    model = Point
    extra = 3


class StatusInline(admin.TabularInline):
    model = Status


class BatchAdmin(admin.ModelAdmin):
    fieldsets = [
        ('Batch details', {'fields': ['batch_num', 'beer_type', 'start_date', 'is_brewing']})
    ]
    inlines = [StatusInline, PointInline]
    list_display = ('batch_num', 'beer_type', 'start_date', 'is_brewing')
    list_display_links = ('batch_num', 'beer_type')
    list_filter = ['start_date']
    search_fields = ['beer_type']


class MeasurmentAdmin(admin.ModelAdmin):
    list_display = ('batch', 'time', 'temperature')
    list_display_links = ('time', 'temperature')
    list_filter = ['batch', 'time', 'temperature']
    search_fields = ['batch__beer_type']


admin.site.register(Batch, BatchAdmin)
admin.site.register(Measurement, MeasurmentAdmin)
