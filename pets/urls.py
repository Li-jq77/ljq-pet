from django.urls import path
from . import views
from . import dodou_views

app_name = "pets"

urlpatterns = [
    path("", views.IndexView.as_view(), name="index"),
    path("category/<slug:slug>/", views.CategoryView.as_view(), name="category"),
    path("dog/<int:pk>/", views.DogDetailView.as_view(), name="dog_detail"),
    path("login/", views.login_view, name="login"),
    path("register/", views.register_view, name="register"),
    path("logout/", views.logout_view, name="logout"),
    
    # 涓汉涓績 & 瀹犵墿绠＄悊
    path("profile/", views.profile_view, name="profile"),
    path("pet/add/", views.PetCreateView.as_view(), name="pet_add"),
    path("pet/<int:pk>/", views.pet_detail_view, name="pet_detail"),
    path("pet/<int:pk>/edit/", views.PetUpdateView.as_view(), name="pet_edit"),
    path("pet/<int:pk>/delete/", views.pet_delete_view, name="pet_delete"),
    path("pet/<int:pet_pk>/weight/add/", views.add_weight_record, name="add_weight"),
    path("weight/<int:pk>/delete/", views.delete_weight_record, name="delete_weight"),
    path("pet/<int:pet_pk>/vaccination/add/", views.add_vaccination, name="add_vaccination"),
    path("vaccination/<int:pk>/delete/", views.delete_vaccination, name="delete_vaccination"),
    path("pet/<int:pet_pk>/deworming/add/", views.add_deworming, name="add_deworming"),
    path("deworming/<int:pk>/delete/", views.delete_deworming, name="delete_deworming"),
    path("pet/<int:pet_pk>/reminder/add/", views.add_reminder, name="add_reminder"),
    path("pet/<int:pet_pk>/reminder/generate/", views.generate_smart_reminders, name="generate_smart_reminders"),
    path("reminder/<int:pk>/complete/", views.complete_reminder, name="complete_reminder"),
    path("reminder/<int:pk>/delete/", views.delete_reminder, name="delete_reminder"),
    path("calendar/", views.calendar_view, name="calendar"),
    path("posts/", views.PostListView.as_view(), name="post_list"),
    path("posts/new/", views.post_create_view, name="post_create"),
    path("posts/<int:pk>/", views.post_detail_view, name="post_detail"),
    # 产品 & 购物车 & 订单
    path("products/", views.product_list_view, name="product_list"),
    path("products/<int:pk>/", views.product_detail_view, name="product_detail"),
    path("products/<slug:slug>/", views.product_list_view, name="product_category"),
    path("cart/", views.cart_view, name="cart"),
    path("cart/add/<int:product_pk>/", views.add_to_cart, name="add_to_cart"),
    path("cart/add-dog/<int:dog_pk>/", views.add_dog_to_cart, name="add_dog_to_cart"),
    path("cart/remove/<int:item_pk>/", views.remove_from_cart, name="remove_from_cart"),
    path("cart/quantity/<int:item_pk>/<str:action>/", views.cart_quantity, name="cart_qty"),
    path("checkout/", views.checkout_view, name="checkout"),
    path("orders/", views.order_list_view, name="order_list"),
    path("orders/<int:pk>/", views.order_detail_view, name="order_detail"),
    path("orders/<int:pk>/cancel/", views.cancel_order_view, name="cancel_order"),
    path("orders/<int:pk>/pay/", views.pay_order_view, name="pay_order"),
    # 豆豆智能体
    path("dodou/chat/", dodou_views.dodou_chat_view, name="dodou_chat"),
    path("dodou/weather/", dodou_views.dodou_weather_view, name="dodou_weather"),
]
