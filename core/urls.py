from django.urls import path
from .views import (
    IndexView, 
    HomePageView,
    LoginView,
    user_logout,
    MyReposView,
    RepoPageView,
    ProfileView,
)


urlpatterns = [
    path('', IndexView.as_view(), name='index'),
    path('home/', HomePageView.as_view(), name='home'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', user_logout, name='logout'),
    path('myrepos/<str:user_id>/', MyReposView.as_view(), name='myrepos'),
    path('repo/<str:repo_id>/', MyReposView.as_view(), name='repo'),
    path('profile/<str:user_id>/', ProfileView.as_view(), name='profile'),
]