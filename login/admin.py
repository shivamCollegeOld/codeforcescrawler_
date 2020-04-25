from django.contrib import admin
from .models import UserProfileInfo, User, languages, verdicts, levels


admin.site.register(UserProfileInfo)
admin.site.register(languages)

admin.site.register(verdicts)
admin.site.register(levels)