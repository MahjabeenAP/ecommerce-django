from django.urls import path
from . import api_views



urlpatterns = [
    path('products/', api_views.product_list_create_api, name='product_list_create_api'),
    path('products/<int:pk>/', api_views.product_detail_api, name='product_detail_api'),

    path('wishlist/add/', api_views.add_to_wishlist_api, name='add_to_wishlist_api'),
    path('wishlist/', api_views.view_wishlist_api, name='view_wishlist_api'),
    path('wishlist/remove/<int:pk>/', api_views.remove_from_wishlist_api, name='remove_from_wishlist_api'),

    path('orders/place/<int:product_id>/', api_views.order_product_api, name='order_product_api'),
    path('orders/', api_views.view_orders_api, name='view_orders_api'),
    path('orders/cancel/<int:order_id>/', api_views.cancel_order_api, name='cancel_order_api'),
    path('orders/mark-shipped/<int:order_id>/', api_views.mark_order_shipped_api, name='mark_order_shipped_api'),

    path('address/', api_views.address_list_api, name='list'),
    path('address/add/', api_views.address_add_api, name='add'),
    path('address/edit/<int:pk>/', api_views.address_edit_api, name='edit'),

    path('profile/', api_views.user_profile_api, name='user_profile_api'),

    path('register/', api_views.register_api, name='api_register'),
    path('login/', api_views.login_api, name='api_login'),
    path('logout/', api_views.logout_api, name='api_logout'),

    # Change Password (for logged-in users)
    path('change-password/', api_views.change_password_api, name='change_password_api'),
    # Forgot Password (send email with reset link)
    path('forgot-password/', api_views.forgot_password_api, name='forgot_password_api'),
    # Reset Password (link from email)
    path('reset-password/<uidb64>/<token>/', api_views.reset_password_api, name='reset_password_api'),

   


]