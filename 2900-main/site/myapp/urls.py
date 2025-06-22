from django.urls import path
from . import views
from django.contrib.auth import views as auth_views
from myapp.views import settings_view
from myapp.views import my_available_content

urlpatterns = [
     path('', views.index, name='index'),
     path('search/', views.search, name='search'),
     path('randomizer/', views.randomizer, name='randomizer'),
     path('randomizer/get-random-content/', views.get_random_content, name='get_random_content'),
     path('popular/', views.popular, name='popular'),
     path('trending/', views.trending, name='trending'),
     path('login/', views.login_view, name='login'),
     path('logout/', auth_views.LogoutView.as_view(), name='logout'),
     path('register/', views.register_view, name='register'),
     path('profile/', views.profile_view, name='profile'),
     path('<str:media_type>/<int:media_id>/', views.content_detail, name='content_detail'),
     path('watchlist/', views.watchlist, name='watchlist'),
     path('watchlist/add/<str:media_type>/<str:media_id>/', 
         views.add_to_watchlist, 
         name='add_to_watchlist'),
     path('watchlist/remove/<str:media_type>/<str:media_id>/', 
         views.remove_from_watchlist, 
         name='remove_from_watchlist'),
     path('contact/', views.contact, name='contact'),
     path('privacy/', views.privacy, name='privacy'),
     path('about/', views.about, name='about'),
     path('my_available_content/', my_available_content, name='my_available_content'),
     path('settings/', settings_view, name='settings'), 
     path('friends/send-request/', views.send_friend_request_view, name='send_friend_request'),
     path('friends/accept-request/<int:request_id>/', views.accept_friend_request_view, name='accept_friend_request'),
     path('friends/reject-request/<int:request_id>/', views.reject_friend_request_view, name='reject_friend_request'),
     path('friends/unfriend/', views.unfriend_view, name='unfriend'),
     path('settings/change-password/', views.change_password_view, name='change_password'),
     path('settings/delete-account/', views.delete_account_view, name='delete_account'),
     path('friend/<str:username>/', views.my_friend_view, name='my_friend'),
     path('director/<str:director_name>/', views.director_detail, name='director_detail'),
     path('actor/<str:actor_name>/', views.actor_detail, name='actor_detail'), 

] 