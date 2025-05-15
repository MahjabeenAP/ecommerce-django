from django.contrib import admin
from .models import CustomUser,Product,Wishlist,Order,Address

# Register your models here.

@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'role', 'is_verified')
    list_filter = ('role', 'is_verified')
    search_fields = ('username', 'email')

admin.site.register(Product)  
admin.site.register(Wishlist)
admin.site.register(Order)
admin.site.register(Address)  