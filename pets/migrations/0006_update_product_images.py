from django.db import migrations


IMAGE_MAP = {
    "狂犬疫苗(单针)": "/static/images/products/vaccine-rabies.png",
    "犬四联疫苗(卫佳伍)": "/static/images/products/vaccine-dhpp.png",
    "猫三联疫苗(妙三多)": "/static/images/products/vaccine-feline.png",
    "皇家狗粮15kg": "/static/images/products/food-dog.png",
    "渴望猫粮5kg": "/static/images/products/food-cat.png",
    "宠物零食鸡肉干": "/static/images/products/treat-chicken.png",
    "发声玩具球": "/static/images/products/toy-ball.png",
    "逗猫棒(羽毛款)": "/static/images/products/toy-cat-wand.png",
    "漏食球益智玩具": "/static/images/products/toy-puzzle.png",
    "项圈牵引绳套装": "/static/images/products/leash-collar.png",
    "宠物猫狗通用睡垫": "/static/images/products/pet-bed.png",
    "宠物外出水壶": "/static/images/products/water-bottle.png",
    "宠物指甲剪套装": "/static/images/products/nail-clipper.png",
    "益生菌(调理肠胃)": "/static/images/products/probiotics.png",
    "鱼油软胶囊(护毛)": "/static/images/products/fish-oil.png",
}


def update_product_images(apps, schema_editor):
    Product = apps.get_model("pets", "Product")
    for name, image_url in IMAGE_MAP.items():
        Product.objects.filter(name=name).update(image_url=image_url)


class Migration(migrations.Migration):

    dependencies = [
        ("pets", "0005_cartitem_dog_orderitem_dog_alter_cartitem_product_and_more"),
    ]

    operations = [
        migrations.RunPython(update_product_images, migrations.RunPython.noop),
    ]
