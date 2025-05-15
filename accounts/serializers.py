from rest_framework import serializers
from .models import CustomUser, Product, Wishlist, Order, Address
from django.contrib.auth import get_user_model

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'phone_number', 'role', 'is_verified']
        read_only_fields = ['id', 'role', 'is_verified']


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = '__all__'
        read_only_fields = ['id', 'created_by', 'created_at']

class WishlistSerializer(serializers.ModelSerializer):
    class Meta:
        model = Wishlist
        fields = ['id', 'user', 'product']
        read_only_fields = ['user']


class OrderSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_price = serializers.DecimalField(source='product.price', max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = Order
        fields = ['id', 'user', 'product', 'product_name', 'product_price', 'status', 'created_at', 'cancelled_at']
        read_only_fields = ['user', 'status', 'created_at', 'cancelled_at']


class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = ['address_line', 'city', 'postal_code']
        extra_kwargs = {
            'address_line': {'required': False, 'allow_blank': True},
            'city': {'required': False, 'allow_blank': True},
            'postal_code': {'required': False, 'allow_blank': True},
        }
    
  

class ChangePasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, min_length=8)
    confirm_password = serializers.CharField(required=True)

    def validate(self, data):
        if data['new_password'] != data['confirm_password']:
            raise serializers.ValidationError("Passwords don't match.")
        return data        