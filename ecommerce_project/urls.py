"""
URL configuration for ecommerce_project project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path,include
from accounts.views import CustomPasswordChangeView,user_profile_view,user_profile_update

from accounts import views
from django.conf import settings
from django.conf.urls.static import static

from django.contrib.auth import views as auth_views



urlpatterns = [
    path('admin/', admin.site.urls),
    path('userdashboard/', views.user_dashboard, name='user_dashboard'),
    path('salesdashboard/', views.sales_dashboard, name='sales_dashboard'),
    path('admindashboard/', views.admin_dashboard, name='admin_dashboard'),
    #authentication
    path('', views.register, name='register'),
    path('login/', views.custom_login, name='login'),
    path('logout/', views.logout_view, name='logout'),
   #forgot password
    path('password-reset/', auth_views.PasswordResetView.as_view(template_name='registration/password_reset_form.html'), name='password_reset'),
    path('password-reset/done/', auth_views.PasswordResetDoneView.as_view(template_name='registration/password_reset_done.html'), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='registration/password_reset_confirm.html'), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(template_name='registration/password_reset_complete.html'), name='password_reset_complete'),
    #admin
    path('profile/', views.admin_profile_view, name='admin_profile'),
    path('profile/update/', views.admin_profile_update, name='admin_profile_update'),
    path('change-password/', views.AdminPasswordChangeView.as_view(), name='admin_password_change'),
    path('change-password/done/', auth_views.PasswordChangeDoneView.as_view(
    template_name='accounts/change_password_done.html'), 
    name='admin_password_change_done'),
    path('verify-sales/<int:user_id>/', views.verify_sales_account, name='verify_sales_account'),
    path('delete-user/<int:user_id>/', views.delete_user, name='delete_user'),
    path('deactivate-user/<int:user_id>/', views.deactivate_user, name='deactivate_user'),
    path('sales-products/', views.sales_products_list, name='sales_products_list'),
    path('sales-products/delete/<int:product_id>/', views.delete_product, name='delete_product'),
    path('sales-products/toggle-status/<int:product_id>/', views.toggle_product_status, name='toggle_product_status'),
    path('admin-orders/', views.admin_order_list, name='admin_order_list'),
    #sales
    path('sales/profile/', views.sales_profile, name='sales_profile'),
    path('sales/profile/update/', views.sales_profile_update, name='sales_profile_update'),
    path('sales/change-password/', views.SalesPasswordChangeView.as_view(), name='sales_password_change'),
    path('sales/change-password/done/', auth_views.PasswordChangeDoneView.as_view(
    template_name='accounts/sales/change_password_done.html'), name='sales_password_change_done'),

    path('sales/dashboard/', views.sales_dashboard, name='sales_dashboard'),
    path('sales/products/', views.sales_product_list, name='sales_product_list'),
    path('sales/products/add/', views.sales_product_add, name='sales_product_add'),
    path('sales/products/edit/<int:pk>/', views.sales_product_edit, name='sales_product_edit'),
    path('sales/products/delete/<int:pk>/', views.sales_product_delete, name='sales_product_delete'),
    path('order/update/<int:order_id>/<str:new_status>/', views.update_order_status, name='update_order_status'),
    #user
    path('user/profile/', user_profile_view, name='user_profile'),
    path('user/profile/update/', user_profile_update, name='user_profile_update'),
    path('user/change-password/', views.UserPasswordChangeView.as_view(), name='user_password_change'),
    path('user/change-password/done/', auth_views.PasswordChangeDoneView.as_view(
    template_name='accounts/user/change_password_done.html'), name='user_password_change_done'),
    # Wishlist
    path('user/wishlist/add/<int:product_id>/', views.add_to_wishlist, name='add_to_wishlist'),
    path('user/wishlist/', views.view_wishlist, name='view_wishlist'),
    path('wishlist/remove/<int:item_id>/', views.remove_from_wishlist, name='remove_from_wishlist'),
    # Order
    path('user/order/<int:product_id>/', views.order_product, name='order_product'),
    path('user/orders/', views.view_orders, name='view_orders'),
    path('user/orders/cancel/<int:order_id>/', views.cancel_order, name='cancel_order'),
    path('user/orders/ship/<int:order_id>/', views.mark_shipped, name='mark_shipped'),
    # Address
    path('user/addresses/', views.address_list, name='address_list'),
    path('user/address/add/', views.address_add, name='address_add'),
    path('user/address/edit/<int:pk>/', views.address_edit, name='address_edit'),

    path('api/', include('accounts.api_urls')), 

]+static(settings.MEDIA_URL,document_root=settings.MEDIA_ROOT)
