from django.urls import path
from . import views

urlpatterns = [
    # Yeh ab homepage ko sahi se handle karega
    path("", views.ml_dashboard, name="ml_dashboard"),
    
    # Report page ke liye route
    path("report/", views.report_page, name="report_page"),
    
    # Feedback page ke liye route
    path("feedback/", views.feedback_page, name="feedback_page"),
    
    # Raw data page ke liye route
    path("datasets/results/2019/raw/", views.raw_data_dashboard, name="raw_data_dashboard"),
]

