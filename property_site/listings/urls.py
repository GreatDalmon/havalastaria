from django.urls import path
from . import views

app_name = 'listings'

urlpatterns = [
    # The homepage (e.g., http://127.0.0.1:8000/)
    path('', views.index, name='index'),

    # The detail page (e.g., http://127.0.0.1:8000/property/1/)
    path('property/<int:pk>/', views.property_detail, name='property_detail'),

    # Add the URL for creating a new listing (Make sure this is ABOVE the register path)
    path('property/new/', views.create_listing, name='create_listing'),

    # Add the URLs for editing and deleting
    path('property/<int:pk>/edit/', views.edit_listing, name='edit_listing'),
    path('property/<int:pk>/delete/', views.delete_listing, name='delete_listing'),

    # Dashboard
    path('dashboard/', views.dashboard, name='dashboard'),

    path('dashboard/users/', views.manage_users, name='manage_users'),
    path('dashboard/users/add-agent/', views.add_agent, name='add_agent'),
    path('dashboard/users/<int:pk>/<str:action>/', views.user_action, name='user_action'),

    path('book-tour/<int:pk>/', views.book_tour, name='book_tour'),
    path('messages/', views.inbox, name='inbox'),
    path('chat/<int:pk>/', views.conversation, name='conversation'),
    path('chat/<int:pk>/poll/', views.chat_poll, name='chat_poll'),
    path('chat/<int:pk>/respond/<str:decision>/', views.tour_response, name='tour_response'),

    # Add the registration URL
    path('register/', views.register, name='register'),
]