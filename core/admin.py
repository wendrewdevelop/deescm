from django.contrib import admin
from .models import (
    AccountModel, 
    RepoModel, 
    RepoObjectModel,
    RepoIssueModel,
    RepoStarsModel,
    RepoForksModel
)


admin.site.register(AccountModel)
admin.site.register(RepoModel)
admin.site.register(RepoObjectModel)
admin.site.register(RepoIssueModel)
admin.site.register(RepoStarsModel)
admin.site.register(RepoForksModel)