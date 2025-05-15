from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.authentication import TokenAuthentication
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.contrib.sites.shortcuts import get_current_site
from .models import Product, Wishlist, Order, Address,CustomUser
from .serializers import ProductSerializer, WishlistSerializer, OrderSerializer, AddressSerializer, UserSerializer,ChangePasswordSerializer
from rest_framework.authtoken.models import Token
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_decode
from django.contrib.auth import update_session_auth_hash

# Only allow authenticated users to access the APIs
@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def product_list_create_api(request):
    if request.method == 'GET':
        products = Product.objects.filter(is_active=True)
        serializer = ProductSerializer(products, many=True)
        return Response(serializer.data)

    elif request.method == 'POST':
        user = request.user
        # Check if user is sales and verified before allowing creation
        if user.role != 'sales' or not getattr(user, 'is_verified', False):
            return Response({'error': 'Only verified sales users can add products.'}, status=status.HTTP_403_FORBIDDEN)

        serializer = ProductSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(created_by=user)  # save creator as logged-in user
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def product_detail_api(request, pk):
    product = get_object_or_404(Product, pk=pk)
    user = request.user

    if request.method in ['PUT', 'DELETE']:
        # Only allow if user is verified sales and is creator
        if user.role != 'sales' or not getattr(user, 'is_verified', False):
            return Response({'error': 'Only verified sales users can update or delete products.'}, status=status.HTTP_403_FORBIDDEN)
        if product.created_by != user:
            return Response({'error': 'Permission denied. You are not the creator of this product.'}, status=status.HTTP_403_FORBIDDEN)

    if request.method == 'GET':
        serializer = ProductSerializer(product)
        return Response(serializer.data)

    elif request.method == 'PUT':
        serializer = ProductSerializer(product, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()  # created_by stays unchanged
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        product.delete()
        return Response({'message': 'Product deleted successfully.'}, status=status.HTTP_204_NO_CONTENT)
    



# Add to Wishlist
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_to_wishlist_api(request):
    #  Only allow users with 'user' role
    if request.user.role != 'user':
        return Response({'error': 'Only users can add to wishlist.'}, status=status.HTTP_403_FORBIDDEN)

    product_id = request.data.get('product_id')
    if not product_id:
        return Response({'error': 'Product ID is required'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        product = Product.objects.get(pk=product_id)
    except Product.DoesNotExist:
        return Response({'error': 'Product not found'}, status=status.HTTP_404_NOT_FOUND)

    wishlist_item, created = Wishlist.objects.get_or_create(user=request.user, product=product)
    if not created:
        return Response({'message': 'Already in wishlist'}, status=status.HTTP_200_OK)

    serializer = WishlistSerializer(wishlist_item)
    return Response(serializer.data, status=status.HTTP_201_CREATED)


# View Wishlist
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def view_wishlist_api(request):
    # Only allow users with 'user' role
    if request.user.role != 'user':
        return Response({'error': 'Only users can view wishlist.'}, status=status.HTTP_403_FORBIDDEN)

    wishlist_items = Wishlist.objects.filter(user=request.user)
    serializer = WishlistSerializer(wishlist_items, many=True)
    return Response(serializer.data)


# Remove from Wishlist
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def remove_from_wishlist_api(request, pk):
    # Only allow users with 'user' role
    if request.user.role != 'user':
        return Response({'error': 'Only users can remove from wishlist.'}, status=status.HTTP_403_FORBIDDEN)

    try:
        wishlist_item = Wishlist.objects.get(pk=pk, user=request.user)
        wishlist_item.delete()
        return Response({'message': 'Removed from wishlist'}, status=status.HTTP_204_NO_CONTENT)
    except Wishlist.DoesNotExist:
        return Response({'error': 'Wishlist item not found'}, status=status.HTTP_404_NOT_FOUND)  


# place order api 
# 1. Place Order - Only 'user' can order
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def order_product_api(request, product_id):
    if request.user.role != 'user':
        return Response({'error': 'Only users can place orders.'}, status=status.HTTP_403_FORBIDDEN)

    try:
        product = Product.objects.get(id=product_id)
    except Product.DoesNotExist:
        return Response({'error': 'Product not found'}, status=status.HTTP_404_NOT_FOUND)

    existing_order = Order.objects.filter(user=request.user, product=product).first()

    if existing_order and existing_order.status != 'cancelled':
        return Response({'message': 'You already have an active order for this product.'}, status=status.HTTP_200_OK)

    order = Order.objects.create(user=request.user, product=product, status='pending')
    serializer = OrderSerializer(order)
    return Response({'message': 'Order placed successfully!', 'order': serializer.data}, status=status.HTTP_201_CREATED)


# 2. View Orders - User sees their orders, Sales sees received orders
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def view_orders_api(request):
    user = request.user

    if user.role == 'user':
        orders = Order.objects.filter(user=user).select_related('product', 'user')
    elif user.role == 'sales':
        orders = Order.objects.filter(product__created_by=user).select_related('product', 'user')
    elif user.role == 'admin':
        orders = Order.objects.all().select_related('product', 'user')
    else:
        return Response({'error': 'Unauthorized'}, status=status.HTTP_403_FORBIDDEN)

    serializer = OrderSerializer(orders, many=True)
    return Response(serializer.data)


# 3. Cancel Order - Only the user who placed it can cancel
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def cancel_order_api(request, order_id):
    try:
        order = Order.objects.get(id=order_id, user=request.user)
    except Order.DoesNotExist:
        return Response({'error': 'Order not found'}, status=status.HTTP_404_NOT_FOUND)

    if order.status != 'pending':
        return Response({'error': 'Only pending orders can be cancelled.'}, status=status.HTTP_400_BAD_REQUEST)

    order.status = 'cancelled'
    order.cancelled_at = timezone.now()
    order.save()

    # Send cancellation email
    send_mail(
        f'Order #{order.id} Cancelled',
        f'Hello {request.user.username},\n\nYour order for {order.product.name} has been cancelled.\nOrder ID: {order.id}\nPrice: ${order.product.price}',
        settings.DEFAULT_FROM_EMAIL,
        [request.user.email],
        fail_silently=True,
    )

    return Response({'message': 'Order cancelled successfully.'}, status=status.HTTP_200_OK)


# 4. Mark Order as Shipped - Only sales who owns product can mark
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mark_order_shipped_api(request, order_id):
    try:
        order = Order.objects.get(id=order_id, product__created_by=request.user)
    except Order.DoesNotExist:
        return Response({'error': 'Order not found or unauthorized access.'}, status=status.HTTP_404_NOT_FOUND)

    if order.status != 'pending':
        return Response({'error': 'Only pending orders can be marked as shipped.'}, status=status.HTTP_400_BAD_REQUEST)

    order.status = 'completed'
    order.save()

    return Response({'message': 'Order marked as shipped.'}, status=status.HTTP_200_OK)


# List Address - for 'user' and 'sales'
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def address_list_api(request):
    if request.user.role not in ['user', 'sales']:
        return Response({'error': 'Unauthorized access.'}, status=status.HTTP_403_FORBIDDEN)

    address = Address.objects.filter(user=request.user).first()
    if address:
        serializer = AddressSerializer(address)
        return Response(serializer.data)
    else:
        return Response({'message': 'No address found.'}, status=status.HTTP_404_NOT_FOUND)


#  Add Address - only 'user'
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def address_add_api(request):
    if request.user.role != 'user':
        return Response({'error': 'Only users can add an address.'}, status=status.HTTP_403_FORBIDDEN)

    if Address.objects.filter(user=request.user).exists():
        return Response({'error': 'You already have an address. Please edit it instead.'}, status=status.HTTP_400_BAD_REQUEST)

    serializer = AddressSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save(user=request.user)
        return Response({'message': 'Address saved successfully!', 'address': serializer.data}, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# Edit Address API
@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def address_edit_api(request, pk):
    user = request.user

    # Only allow role 'user' to edit
    if user.role != 'user':
        return Response({'error': 'Only users can edit their address.'}, 
                        status=status.HTTP_403_FORBIDDEN)

    try:
        address = Address.objects.get(id=pk, user=user)
    except Address.DoesNotExist:
        return Response({'error': 'Address not found.'}, 
                        status=status.HTTP_404_NOT_FOUND)

    partial = request.method == 'PATCH'
    serializer = AddressSerializer(address, data=request.data, partial=partial)
    
    if serializer.is_valid():
        serializer.save()
        return Response({'message': 'Address updated successfully!', 'address': serializer.data})
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

 # user profile 
@api_view(['GET', 'PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def user_profile_api(request):
    user = request.user

    if request.method == 'GET':
        serializer = UserSerializer(user)
        return Response(serializer.data)

    elif request.method == 'PUT':
        serializer = UserSerializer(user, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({'message': 'Profile updated successfully!', 'user': serializer.data})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'PATCH':
        serializer = UserSerializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({'message': 'Profile updated successfully!', 'user': serializer.data})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

#register api
@api_view(['POST'])
@permission_classes([AllowAny])
def register_api(request):
    data = request.data
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    role = data.get('role')

    if CustomUser.objects.filter(email=email).exists():
        return Response({'error': 'Email already exists'}, status=status.HTTP_400_BAD_REQUEST)

    user = CustomUser(
        username=username,
        email=email,
        role=role
    )
    user.set_password(password)

    if role == 'admin':
        user.is_staff = True
        user.is_superuser = True

    user.save()

    # Email notification
    current_site = get_current_site(request)
    dashboard_url = f"http://{current_site.domain}/{role}dashboard/"
    subject = "Welcome to Our Site!"
    message = f"""Hello {username},

Thank you for registering with us!

Access your dashboard here:
{dashboard_url}

Best regards,
Your Website Team
"""
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [email], fail_silently=False)

    # Create token
    token, created = Token.objects.get_or_create(user=user)

    return Response({'message': 'User registered successfully', 'token': token.key}, status=status.HTTP_201_CREATED)
   
# login api
@api_view(['POST'])
@permission_classes([AllowAny])
def login_api(request):
    email = request.data.get('email')
    password = request.data.get('password')

    user = authenticate(request, username=email, password=password)

    if user is not None:
        login(request, user)
        token, created = Token.objects.get_or_create(user=user)
        serializer = UserSerializer(user)
        return Response({'token': token.key, 'user': serializer.data}, status=status.HTTP_200_OK)
    else:
        return Response({'error': 'Invalid email or password'}, status=status.HTTP_401_UNAUTHORIZED)

#logout api
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_api(request):
    request.user.auth_token.delete()  # Delete the token
    logout(request)
    return Response({'message': 'Logged out successfully'}, status=status.HTTP_200_OK)



# change password api 
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def change_password_api(request):
    user = request.user
    current_password = request.data.get("current_password")
    new_password = request.data.get("new_password")
    confirm_password = request.data.get("confirm_password")

    if not user.check_password(current_password):
        return Response({"error": "Current password is incorrect."}, status=status.HTTP_400_BAD_REQUEST)

    if new_password != confirm_password:
        return Response({"error": "New passwords do not match."}, status=status.HTTP_400_BAD_REQUEST)

    user.set_password(new_password)
    user.save()

    return Response({"message": "Password changed successfully."}, status=status.HTTP_200_OK)

# Forgot Password (Send Reset Email) API

# Send Password Reset Email

@api_view(['POST'])
@permission_classes([AllowAny])
def forgot_password_api(request):
    email = request.data.get('email')
    user = CustomUser.objects.filter(email=email).first()

    if user:
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        domain = get_current_site(request).domain
        reset_url = f"http://{domain}/reset-password/{uid}/{token}/"

        # You can customize this message
        message = f"Hi {user.username},\n\nUse this link to reset your password:\n{reset_url}"

        send_mail(
            subject="Reset your password",
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False
        )

    # Return same response to avoid user enumeration
    return Response({'message': 'If the email is registered, a password reset link has been sent.'}, status=200)

#  Reset Password with UID and Token

@api_view(['POST'])
@permission_classes([AllowAny])
def reset_password_api(request, uidb64, token):
    new_password = request.data.get('new_password')
    confirm_password = request.data.get('confirm_password')

    if new_password != confirm_password:
        return Response({"error": "Passwords do not match."}, status=400)

    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = CustomUser.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, CustomUser.DoesNotExist):
        return Response({'error': 'Invalid link.'}, status=400)

    if default_token_generator.check_token(user, token):
        user.set_password(new_password)
        user.save()
        return Response({'message': 'Password reset successful.'})
    else:
        return Response({'error': 'Invalid or expired token.'}, status=400)
    



