from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("login", views.login_view, name="login"),
    path("logout", views.logout_view, name="logout"),
    path("register", views.register, name="register"),
    path("create_listing/", views.create_listing, name="create_listing"),
    path('listing/<int:listing_id>/', views.listing_detail, name='listing_detail'),
    path("watchlist/", views.watchlist, name="watchlist"),
    path("categories/", views.category_list, name="category_list"),
    path("categories/<int:category_id>/",
         views.category_listings, name="category_listings"),
    path('listing/<int:listing_id>/add_comment/',
         views.add_comment, name='add_comment'),
    path('listing/<int:listing_id>/place_bid/',
         views.place_bid, name='place_bid'),
    path('listing/<int:listing_id>/watchlist_toggle/',
         views.watchlist_toggle, name='watchlist_toggle'),
    path('listing/<int:listing_id>/close_auction/',
         views.close_auction, name='close_auction')
]
