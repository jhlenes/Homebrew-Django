from django.conf.urls import url

from . import views

app_name = 'main'
urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'new-data/', views.new_data, name='new-data'),
    url(r'send/', views.send, name='send'),
    url(r'new-batch/', views.new_batch, name='new-batch'),
    url(r'previous-batches/',views.previous_batches, name='previous-batches'),
    url(r'receive/', views.receive, name='receive'),

]
