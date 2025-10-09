from django.contrib import admin
from .models import State, ExitPoll, ConstituencyResult, MLResult, Feedback

admin.site.register(State)
admin.site.register(ExitPoll)
admin.site.register(ConstituencyResult)
admin.site.register(MLResult)
admin.site.register(Feedback) 
