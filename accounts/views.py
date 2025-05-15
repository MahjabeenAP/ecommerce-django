from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import  authenticate, login , logout
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.sites.shortcuts import get_current_site
from .forms import UserRegistrationForm,ProductForm
from django.contrib.auth import get_user_model
User = get_user_model()
from django.shortcuts import get_object_or_404
from .models import Product, CustomUser,Wishlist,Order,Address

from django.contrib.auth.views import PasswordChangeView
from django.urls import reverse_lazy
from django.db.models import Q
from django.utils import timezone
from datetime import timedelta 

from .forms import CustomUserUpdateForm,ProductForm,AddressForm

# Create your views here.
# Utility functions to check roles
def is_user(user):
    return user.is_authenticated and user.role == 'user'

def is_sales(user):
    return user.is_authenticated and user.role == 'sales'

def is_admin(user):
    return user.is_authenticated and user.role == 'admin' or user.is_superuser

# Dashboard Views


            # USER

@login_required
@user_passes_test(is_user)
def user_dashboard(request):
    return render(request, 'accounts/user_dashboard.html')

@login_required
def user_profile_view(request):
    return render(request, 'accounts/user/profile.html', {'user': request.user})

@login_required
def user_profile_update(request):
    if request.method == 'POST':
        form = CustomUserUpdateForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully.')
            return redirect('user_profile')
    else:
        form = CustomUserUpdateForm(instance=request.user)
    return render(request, 'accounts/user/profile_update.html', {'form': form})

class UserPasswordChangeView(PasswordChangeView):
    template_name = 'accounts/user/change_password.html'
    success_url = reverse_lazy('user_password_change_done')

    def form_valid(self, form):
        response = super().form_valid(form)

        # Send confirmation email
        send_mail(
            subject='Password Changed Successfully',
            message='Hello {},\n\nYour password has been changed successfully.\n\nIf this was not you, please reset your password immediately.'.format(self.request.user.username),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[self.request.user.email],
            fail_silently=False,
        )

        messages.success(self.request, 'Password changed and confirmation email sent.')
        return response



# Dashboard - Product List
@login_required
@user_passes_test(is_user)
def user_dashboard(request):
    products = Product.objects.filter(is_active=True)
    active_order_ids = Order.objects.filter(
        user=request.user
    ).exclude(status='cancelled').values_list('product_id', flat=True)
    
    # Get list of product IDs in user's wishlist
    wishlist_products = Wishlist.objects.filter(
        user=request.user
    ).values_list('product_id', flat=True)
    
    return render(request, 'accounts/user_dashboard.html', {
        'products': products,
        'active_order_ids': list(active_order_ids),
        'wishlist_products': wishlist_products,
    })


# Add to Wishlist
@login_required
def add_to_wishlist(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    Wishlist.objects.get_or_create(user=request.user, product=product)
    messages.success(request, 'Product added to wishlist.')
    return redirect('user_dashboard')


# View Wishlist
@login_required
def view_wishlist(request):
    wishlist_items = Wishlist.objects.filter(user=request.user)
    return render(request, 'accounts/user/wishlist.html', {'wishlist_items': wishlist_items})

@login_required
def remove_from_wishlist(request, item_id):
    wishlist_item = get_object_or_404(Wishlist, id=item_id, user=request.user)
    wishlist_item.delete()
    return redirect('view_wishlist')

# Order Product
@login_required
def order_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    existing_order = Order.objects.filter(
        user=request.user,
        product=product
    ).first()
    
    if existing_order:
        # If order exists but is cancelled, create a new one
        if existing_order.status == 'cancelled':
            Order.objects.create(
                user=request.user,
                product=product,
                status='pending'
            )
            messages.success(request, 'New order created successfully!')
        else:
            messages.info(request, 'You already have an active order for this product.')
    else:
        # Create new order if none exists
        Order.objects.create(
            user=request.user,
            product=product,
            status='pending'
        )
        messages.success(request, 'Order placed successfully!')
    return redirect('view_orders')


# View Orders
@login_required
def view_orders(request):
    orders = Order.objects.filter(
        Q(user=request.user) | 
        Q(product__created_by=request.user)
    ).select_related('product', 'user', 'product__created_by').order_by('-created_at')
    
    
    return render(request, 'accounts/user/orders.html', {
        'orders': orders,
        'user_is_seller': request.user.products.exists(),
        'now': timezone.now() 
    })

@login_required
def cancel_order(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    order.cancelled_at = timezone.now()
    if order.status == 'pending':
        order.status = 'cancelled'
        order.save()

        send_mail(
            f'Order #{order.id} Cancelled',
            f'Hello {request.user.username},\n\n'
            f'Your order for {order.product.name} has been cancelled.\n'
            f'Order ID: {order.id}\n'
            f'Price: ${order.product.price}\n\n'
            'Thank you for using our store.',
            settings.DEFAULT_FROM_EMAIL,
            [request.user.email],
            fail_silently=False,
        )


        messages.success(request, 'Order cancelled successfully.')
    else:
        messages.error(request, 'Only pending orders can be cancelled.')
    
    return redirect('view_orders')

@login_required
def mark_shipped(request, order_id):
    order = get_object_or_404(Order, id=order_id, product__created_by=request.user)
    
    if order.status == 'pending':
        order.status = 'completed'
        order.save()
        messages.success(request, 'Order marked as shipped.')
    else:
        messages.error(request, 'Only pending orders can be shipped.')
    
    return redirect('view_orders')

# Address Views
@login_required
def address_list(request):
    addresses = Address.objects.filter(user=request.user)
    return render(request, 'accounts/user/address_list.html', {'addresses': addresses})

@login_required
def address_add(request):
    if Address.objects.filter(user=request.user).exists():
        messages.warning(request, 'You can only have one address. Please edit your existing address.')
        return redirect('address_edit', pk=request.user.address_set.first().id)
    
    if request.method == 'POST':
        form = AddressForm(request.POST)
        if form.is_valid():
            address = form.save(commit=False)
            address.user = request.user
            address.save()
            messages.success(request, 'Address saved successfully!')
            return redirect('user_dashboard')
    else:
        form = AddressForm()
    
    return render(request, 'accounts/user/address_form.html', {'form': form})


@login_required
def address_edit(request, pk):
    address = get_object_or_404(Address, id=pk, user=request.user)
    if request.method == 'POST':
        form = AddressForm(request.POST, instance=address)
        if form.is_valid():
            form.save()
            messages.success(request, 'Address updated successfully!')
            return redirect('user_dashboard')
    else:
        form = AddressForm(instance=address)
    
    return render(request, 'accounts/user/address_form.html', {'form': form, 'address': address})



#             SALES 


@login_required
@user_passes_test(is_sales)
def sales_dashboard(request):
    if request.user.role != 'sales':
        return redirect('login')

    products = Product.objects.filter(created_by=request.user)
    orders = Order.objects.filter(
        product__created_by=request.user
    ).select_related('user', 'product').order_by('-created_at')
    
    return render(request, 'accounts/sales_dashboard.html', {
        'products': products,
        'orders': orders,
        'is_verified': request.user.is_verified
    })

@login_required
@user_passes_test(is_sales)
def update_order_status(request, order_id, new_status):
    order = get_object_or_404(Order, id=order_id, product__created_by=request.user)
    
    if request.method == 'POST':
        valid_statuses = ['shipped', 'completed', 'cancelled']
        if new_status in valid_statuses:
            order.status = new_status
            if new_status == 'cancelled':
                order.cancelled_at = timezone.now()
            order.save()
            messages.success(request, f'Order #{order.id} status updated to {new_status}')
        else:
            messages.error(request, 'Invalid status update')
    
    return redirect('sales_dashboard')

@login_required
def sales_product_list(request):
    if request.user.role != 'sales':
        return redirect('login')

    products = Product.objects.filter(created_by=request.user)
    return render(request, 'accounts/sales_dashboard.html', {'products': products})


@login_required
def sales_product_add(request):
    if request.user.role != 'sales' or not request.user.is_verified:
        messages.warning(request, "You must be verified to add products.")
        return redirect('sales_dashboard')

    form = ProductForm(request.POST or None, request.FILES or None)
    if form.is_valid():
        product = form.save(commit=False)
        product.created_by = request.user
        product.save()
        messages.success(request, "Product added successfully.")
        return redirect('sales_dashboard')

    return render(request, 'accounts/sales/sales_product_form.html', {'form': form})


@login_required
def sales_product_edit(request, pk):
    product = get_object_or_404(Product, pk=pk, created_by=request.user)
    form = ProductForm(request.POST or None, request.FILES or None, instance=product)

    if form.is_valid():
        form.save()
        messages.success(request, "Product updated successfully.")
        return redirect('sales_dashboard')

    return render(request, 'accounts/sales/sales_product_form.html', {'form': form})

@login_required
def sales_product_delete(request, pk):
    product = get_object_or_404(Product, pk=pk, created_by=request.user)
    product.delete()
    messages.success(request, "Product deleted successfully.")
    return redirect('sales_dashboard')

@login_required
@user_passes_test(is_sales)
def sales_profile(request):
    return render(request, 'accounts/sales_profile.html', {'user': request.user})

@login_required
@user_passes_test(is_sales)
def sales_profile_update(request):
    if request.method == 'POST':
        form = CustomUserUpdateForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully.')
            return redirect('sales_profile')
    else:
        form = CustomUserUpdateForm(instance=request.user)
    return render(request, 'accounts/sales_profile_update.html', {'form': form})

class SalesPasswordChangeView(PasswordChangeView):
    template_name = 'accounts/sales/change_password.html'
    success_url = reverse_lazy('sales_password_change_done')

    def form_valid(self, form):
        response = super().form_valid(form)

        # Send email
        send_mail(
            subject='Password Changed Successfully',
            message='Hello {},\n\nYour password has been changed successfully.\n\nIf this was not you, please reset your password immediately.'.format(self.request.user.username),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[self.request.user.email],
            fail_silently=False,
        )

        messages.success(self.request, 'Password changed and confirmation email sent.')
        return response
    



#           admin


@login_required
def admin_profile_view(request):
    return render(request, 'accounts/admin_dashboard/profile.html', {'user': request.user})

@login_required
def admin_profile_update(request):
    if request.method == 'POST':
        form = CustomUserUpdateForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully.')
            return redirect('admin_profile')
    else:
        form = CustomUserUpdateForm(instance=request.user)
    return render(request, 'accounts/admin_dashboard/profile_update.html', {'form': form})


class AdminPasswordChangeView(PasswordChangeView):
    template_name = 'accounts/change_password.html'
    success_url = reverse_lazy('admin_password_change_done')

    def form_valid(self, form):
        response = super().form_valid(form)
        
        # Send email notification
        send_mail(
            subject='Password Changed Successfully',
            message=f'Hello {self.request.user.username},\n\nYour admin password has been changed successfully.\n\nIf this was not you, please reset your password immediately.',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[self.request.user.email],
            fail_silently=False,
        )
        
        messages.success(self.request, 'Password changed and confirmation email sent.')
        return response

@login_required
@user_passes_test(is_admin)
def admin_dashboard(request):
    search_query = request.GET.get('search', '')

    pending_sales = CustomUser.objects.filter(role='sales', is_verified=False)
    verified_sales = CustomUser.objects.filter(role='sales', is_verified=True)
    users = CustomUser.objects.filter(role='user')
    
    # Apply search filter if query exists
    if search_query:
        # Search in username or email fields (case-insensitive)
        pending_sales = pending_sales.filter(
            Q(username__icontains=search_query) | 
            Q(email__icontains=search_query)
        )
        verified_sales = verified_sales.filter(
            Q(username__icontains=search_query) | 
            Q(email__icontains=search_query)
        )
        users = users.filter(
            Q(username__icontains=search_query) | 
            Q(email__icontains=search_query)
        )

    context = {
        'pending_sales': pending_sales,
        'verified_sales': verified_sales,
        'users': users,
        'search_query': search_query, 
    }
    return render(request, 'accounts/admin_dashboard.html', context)

@login_required
@user_passes_test(is_admin)
def delete_user(request, user_id):
    user = get_object_or_404(CustomUser, id=user_id)
    user.delete()
    messages.success(request, f"User '{user.username}' deleted.")
    return redirect('admin_dashboard')


@login_required
@user_passes_test(is_admin)
def deactivate_user(request, user_id):
    user = get_object_or_404(CustomUser, id=user_id)
    user.is_active = False
    user.save()
    messages.warning(request, f"User '{user.username}' deactivated.")
    return redirect('admin_dashboard')


@login_required
@user_passes_test(is_admin)
def verify_sales_account(request, user_id):
    user = CustomUser.objects.get(id=user_id)
    if user.role == 'sales':
        user.is_verified = True
        user.save()
        messages.success(request, f"Sales account '{user.username}' has been verified.")
    return redirect('admin_dashboard')

# product list shown admin
def sales_products_list(request):
    if request.user.is_superuser or request.user.role == 'admin':
        sales_users = CustomUser.objects.filter(role='sales')
        products = Product.objects.filter(created_by__in=sales_users)
        return render(request, 'accounts/admin_dashboard/sales_products.html', {'products': products})
    else:
        return redirect('login')

@user_passes_test(is_admin)
def delete_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    product.delete()
    messages.success(request, 'Product deleted successfully.')
    return redirect('sales_products_list')

@user_passes_test(is_admin)
def toggle_product_status(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    product.is_active = not product.is_active
    product.save()
    messages.success(request, f'Product {"activated" if product.is_active else "deactivated"} successfully.')
    return redirect('sales_products_list')

@login_required
@user_passes_test(is_admin)
def admin_order_list(request):
    search_query = request.GET.get('search', '')
    status_filter = request.GET.get('status', '')
    
    orders = Order.objects.all().select_related(
        'user', 'product', 'product__created_by'
    ).order_by('-created_at')
    
    # Apply filters if provided
    if search_query:
        orders = orders.filter(
            Q(user__username__icontains=search_query) |
            Q(user__email__icontains=search_query) |
            Q(product__name__icontains=search_query)
        )
    
    if status_filter:
        orders = orders.filter(status=status_filter)
    
    context = {
        'orders': orders,
        'search_query': search_query,
        'status_filter': status_filter,
        'status_choices': Order.STATUS_CHOICES,
    }
    
    return render(request, 'accounts/admin_dashboard/order_list.html', context)


#        REGISTRATION WITH EMAIL


def register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            # Save the user
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])

            if user.role == 'admin':
                user.is_superuser = True
                user.is_staff = True 

            user.save()

             # Generate dashboard URL based on role
            current_site = get_current_site(request)
            domain = current_site.domain

            if user.role == 'admin':
                dashboard_url = f"http://{domain}/admindashboard/"
            elif user.role == 'sales':
                dashboard_url = f"http://{domain}/salesdashboard/"
            elif user.role == 'user':
                dashboard_url = f"http://{domain}/userdashboard/"
            else:
                dashboard_url = f"http://{domain}/dashboard/"

             # (Optional) Send welcome email (without password)
            subject = "Welcome to Our Site!"
            message =  f"""Hello {user.username},

Thank you for registering with us!

You can access your dashboard here:
{dashboard_url}

Please log in using your credentials.

Best regards,
Your Website Team
"""
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                fail_silently=False,
            )   

            # Automatically authenticate and log in the user
            user = authenticate(request, email=user.email, password=form.cleaned_data['password'])
            if user is not None:
                login(request, user) 

                # Redirect based on user role
            if user.is_superuser:
                return redirect('admin_dashboard')
            elif user.role == 'sales':
                return redirect('sales_dashboard')
            elif user.role == 'user':
                return redirect('user_dashboard')
            else:
                return redirect('default_dashboard')

           
            # Show success message
        messages.success(request, "Registration successful. Please check your email.")

        return redirect('login')  # Fallback redirect

    else:
        form = UserRegistrationForm()

    return render(request, 'registration/register.html', {'form': form})

# password change 
class CustomPasswordChangeView(PasswordChangeView):
    template_name = 'accounts/change_password.html'
    success_url = reverse_lazy('password_change_done')

    def form_valid(self, form):
        print("✅ Password changed successfully!")  # DEBUG print
        return super().form_valid(form)

#   login 
def custom_login(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')

        user = authenticate(request, username=email, password=password)

        if user is not None:
            login(request, user)
            # Redirect based on role
            if user.role == 'admin' or user.is_superuser:
                return redirect('admin_dashboard')
            elif user.role == 'sales':
                return redirect('sales_dashboard')
            elif user.role == 'user':
                return redirect('user_dashboard')
        else:
            messages.error(request, 'Invalid email or password.')

    return render(request, 'registration/login.html')

def logout_view(request):
    logout(request)
    return redirect('login')


