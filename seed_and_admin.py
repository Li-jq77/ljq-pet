import os
os.chdir("D:/Study/codex学习/pet_agent")

# ===== 1. Seed products =====
os.environ["DJANGO_SETTINGS_MODULE"] = "pet_agent.settings"
import django
django.setup()
from pets.models import ProductCategory, Product, Cart, CartItem, Order, OrderItem

cat1, _ = ProductCategory.objects.get_or_create(slug="vaccine", defaults={"name":"疫苗","icon":"💉","sort_order":1})
cat2, _ = ProductCategory.objects.get_or_create(slug="food", defaults={"name":"宠物食品","icon":"🍖","sort_order":2})
cat3, _ = ProductCategory.objects.get_or_create(slug="toy", defaults={"name":"宠物玩具","icon":"🧸","sort_order":3})
cat4, _ = ProductCategory.objects.get_or_create(slug="accessory", defaults={"name":"宠物配件","icon":"🎀","sort_order":4})
cat5, _ = ProductCategory.objects.get_or_create(slug="health", defaults={"name":"保健品","icon":"💊","sort_order":5})

products = [
    ("狂犬疫苗(单针)",cat1,80,"/static/images/狂犬疫苗.png","宠物医院专用狂犬疫苗，安全有效",99),
    ("犬四联疫苗(卫佳伍)",cat1,120,"/static/images/疫苗.png","预防犬瘟热、细小病毒等四种传染病",50),
    ("猫三联疫苗(妙三多)",cat1,150,"/static/images/疫苗.png","预防猫瘟、猫鼻支、猫杯状病毒",50),
    ("皇家狗粮15kg",cat2,320,"/static/images/狗粮.png","成犬用，营养均衡，适口性好",30),
    ("渴望猫粮5kg",cat2,280,"/static/images/猫粮.png","六种鱼配方，富含Omega-3",25),
    ("宠物零食鸡肉干",cat2,35,"/static/images/零食.png","天然风干鸡胸肉，无添加",100),
    ("发声玩具球",cat3,25,"/static/images/玩具球.png","狗狗猫咪都爱玩的发声球",200),
    ("逗猫棒(羽毛款)",cat3,18,"/static/images/逗猫棒.png","猫咪最爱的互动玩具",150),
    ("漏食球益智玩具",cat3,45,"/static/images/益智玩具.png","藏食设计，让宠物边玩边吃",80),
    ("项圈牵引绳套装",cat4,55,"/static/images/牵引绳.png","舒适透气，防挣脱设计",60),
    ("宠物猫狗通用睡垫",cat4,89,"/static/images/睡垫.png","加厚柔软，四季通用",40),
    ("宠物外出水壶",cat4,38,"/static/images/水壶.png","一键出水，便携设计",70),
    ("宠物指甲剪套装",cat4,29,"/static/images/指甲剪.png","防误剪设计，含磨甲刀",90),
    ("益生菌(调理肠胃)",cat5,68,"/static/images/益生菌.png","改善宠物肠胃健康，调理软便",45),
    ("鱼油软胶囊(护毛)",cat5,88,"/static/images/鱼油.png","富含Omega-3，美毛护肤",35),
]

for name, cat, price, img, desc, stock in products:
    Product.objects.get_or_create(name=name, defaults={
        "category": cat, "price": price, "image_url": img,
        "description": desc, "stock": stock, "is_published": True
    })

print(f"Seeded {len(products)} products")

# ===== 2. Update admin.py =====
admin = open("pets/admin.py", "r", encoding="utf-8").read()
if "ProductCategoryAdmin" not in admin:
    admin = admin.rstrip() + """

@admin.register(ProductCategory)
class ProductCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "icon", "sort_order")
    prepopulated_fields = {"slug": ("name",)}

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "price", "stock", "is_published")
    list_filter = ("category", "is_published")

@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ("user", "created_at")

@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ("cart", "product", "quantity")

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("user", "total", "status", "created_at")
    list_filter = ("status",)

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ("order", "product", "quantity", "price")
"""
    open("pets/admin.py", "w", encoding="utf-8").write(admin)
    print("Admin updated")
else:
    print("Admin already has products/orders")