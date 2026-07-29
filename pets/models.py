from django.db import models
from django.urls import reverse
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from datetime import date, timedelta


# ---------- 宠物档案 ----------

class PetProfile(models.Model):
    """用户饲养的宠物档案"""
    SPECIES_CHOICES = [
        ('dog', '🐶 狗狗'),
        ('cat', '🐱 猫咪'),
        ('rabbit', '🐰 兔子'),
        ('bird', '🐦 小鸟'),
        ('fish', '🐟 鱼类'),
        ('hamster', '🐹 仓鼠'),
        ('turtle', '🐢 乌龟'),
        ('other', '其他'),
    ]

    GENDER_CHOICES = [
        ('male', '♂️ 男生'),
        ('female', '♀️ 女生'),
    ]

    owner = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="主人", related_name="pets")
    name = models.CharField("宠物昵称", max_length=50)
    species = models.CharField("物种", max_length=20, choices=SPECIES_CHOICES, default='dog')
    breed = models.CharField("品种", max_length=100, blank=True, help_text="如：金毛、布偶猫")
    gender = models.CharField("性别", max_length=10, choices=GENDER_CHOICES, default='male')
    birthday = models.DateField("出生日期", null=True, blank=True)
    adopted_date = models.DateField("领养/接回家日期", null=True, blank=True)
    avatar_url = models.URLField("头像链接", max_length=500, blank=True)
    color = models.CharField("毛色/特征", max_length=100, blank=True)
    microchip_id = models.CharField("芯片编号", max_length=50, blank=True)
    notes = models.TextField("备注", blank=True, help_text="过敏史、特殊习惯等")
    is_active = models.BooleanField("是否在养", default=True)
    created_at = models.DateTimeField("创建时间", auto_now_add=True)
    updated_at = models.DateTimeField("更新时间", auto_now=True)

    class Meta:
        verbose_name = "宠物档案"
        verbose_name_plural = "宠物档案"
        ordering = ["-is_active", "-created_at"]

    def __str__(self):
        return f"{self.owner.username}的{self.name}"

    def get_absolute_url(self):
        return reverse("pets:pet_detail", args=[self.pk])

    @property
    def age(self):
        """计算宠物年龄（年月）"""
        if not self.birthday:
            return None
        today = date.today()
        years = today.year - self.birthday.year
        months = today.month - self.birthday.month
        if today.day < self.birthday.day:
            months -= 1
        if months < 0:
            years -= 1
            months += 12
        if years > 0:
            return f"{years}岁{months}个月"
        return f"{months}个月"

    @property
    def latest_weight(self):
        """最近一次体重记录"""
        record = self.weight_records.order_by('-recorded_at').first()
        return record.weight if record else None

    @property
    def upcoming_reminders(self):
        """未来7天的提醒"""
        today = date.today()
        week_later = today + timedelta(days=7)
        return self.reminders.filter(
            reminder_date__gte=today,
            reminder_date__lte=week_later,
            is_completed=False
        ).order_by('reminder_date')


class WeightRecord(models.Model):
    """体重记录（体重曲线）"""
    pet = models.ForeignKey(PetProfile, on_delete=models.CASCADE, verbose_name="宠物", related_name="weight_records")
    weight = models.DecimalField("体重(kg)", max_digits=5, decimal_places=2,
                                  validators=[MinValueValidator(0.01)])
    recorded_at = models.DateField("记录日期", default=date.today)
    notes = models.CharField("备注", max_length=200, blank=True)
    created_at = models.DateTimeField("创建时间", auto_now_add=True)

    class Meta:
        verbose_name = "体重记录"
        verbose_name_plural = "体重记录"
        ordering = ["-recorded_at"]

    def __str__(self):
        return f"{self.pet.name} - {self.weight}kg ({self.recorded_at})"


class Vaccination(models.Model):
    """疫苗接种记录"""
    VACCINE_TYPES = [
        ('rabies', '狂犬疫苗'),
        ('dhpp', '犬瘟/细小/肝炎/副流感四联'),
        ('dhpp_plus', '犬八联疫苗'),
        ('fvrpc', '猫三联(猫瘟/猫鼻支/猫杯状)'),
        ('felv', '猫白血病疫苗'),
        ('other', '其他疫苗'),
    ]

    pet = models.ForeignKey(PetProfile, on_delete=models.CASCADE, verbose_name="宠物", related_name="vaccinations")
    vaccine_type = models.CharField("疫苗类型", max_length=20, choices=VACCINE_TYPES)
    vaccine_name = models.CharField("疫苗名称", max_length=100, blank=True, help_text="如：卫佳伍、妙三多")
    dose_number = models.IntegerField("第几针", default=1, validators=[MinValueValidator(1)])
    administered_date = models.DateField("接种日期")
    next_due_date = models.DateField("下次接种日期", null=True, blank=True)
    clinic = models.CharField("接种医院/诊所", max_length=100, blank=True)
    veterinarian = models.CharField("兽医姓名", max_length=50, blank=True)
    notes = models.TextField("备注", blank=True)
    created_at = models.DateTimeField("创建时间", auto_now_add=True)

    class Meta:
        verbose_name = "疫苗接种"
        verbose_name_plural = "疫苗接种"
        ordering = ["-administered_date"]

    def __str__(self):
        return f"{self.pet.name} - {self.get_vaccine_type_display()}(第{self.dose_number}针)"


class Deworming(models.Model):
    """驱虫记录"""
    DEWORMING_TYPES = [
        ('internal', '体内驱虫'),
        ('external', '体外驱虫'),
        ('both', '体内外同驱'),
    ]

    pet = models.ForeignKey(PetProfile, on_delete=models.CASCADE, verbose_name="宠物", related_name="dewormings")
    deworming_type = models.CharField("驱虫类型", max_length=10, choices=DEWORMING_TYPES)
    product_name = models.CharField("驱虫药名称", max_length=100, blank=True, help_text="如：大宠爱、福来恩")
    administered_date = models.DateField("驱虫日期")
    next_due_date = models.DateField("下次驱虫日期", null=True, blank=True)
    notes = models.TextField("备注", blank=True)
    created_at = models.DateTimeField("创建时间", auto_now_add=True)

    class Meta:
        verbose_name = "驱虫记录"
        verbose_name_plural = "驱虫记录"
        ordering = ["-administered_date"]

    def __str__(self):
        return f"{self.pet.name} - {self.get_deworming_type_display()}({self.administered_date})"


class Reminder(models.Model):
    """智能日程提醒"""
    REMINDER_TYPES = [
        ('vaccination', '💉 疫苗接种'),
        ('deworming', '🪱 驱虫'),
        ('nails', '💅 剪指甲'),
        ('bath', '🛁 洗澡'),
        ('grooming', '✂️ 美容'),
        ('checkup', '🏥 体检'),
        ('teeth', '🦷 刷牙/洁牙'),
        ('weight', '⚖️ 称体重'),
        ('feed', '🍖 换粮/补货'),
        ('custom', '📌 自定义'),
    ]

    pet = models.ForeignKey(PetProfile, on_delete=models.CASCADE, verbose_name="宠物", related_name="reminders")
    reminder_type = models.CharField("提醒类型", max_length=20, choices=REMINDER_TYPES)
    title = models.CharField("提醒标题", max_length=100)
    description = models.TextField("详细说明", blank=True)
    reminder_date = models.DateField("提醒日期")
    repeat_interval_days = models.IntegerField("重复间隔(天)", null=True, blank=True,
                                                 help_text="留空则不重复")
    is_completed = models.BooleanField("是否已完成", default=False)
    completed_at = models.DateTimeField("完成时间", null=True, blank=True)
    created_at = models.DateTimeField("创建时间", auto_now_add=True)

    class Meta:
        verbose_name = "日程提醒"
        verbose_name_plural = "日程提醒"
        ordering = ["reminder_date", "created_at"]

    def __str__(self):
        return f"{self.pet.name} - {self.title}"

class PetCategory(models.Model):
    """狗狗分类：小型犬、中型犬、大型犬"""
    name = models.CharField("分类名称", max_length=50)
    slug = models.SlugField("标识", max_length=50, unique=True)
    description = models.TextField("描述", blank=True)
    icon = models.CharField("图标", max_length=50, help_text="使用 emoji", blank=True)
    sort_order = models.IntegerField("排序", default=0)
    created_at = models.DateTimeField("创建时间", auto_now_add=True)

    class Meta:
        verbose_name = "宠物分类"
        verbose_name_plural = "宠物分类"
        ordering = ["sort_order"]

    def __str__(self):
        return self.name


class Dog(models.Model):
    """狗狗品种"""
    name = models.CharField("品种名称", max_length=100)
    category = models.ForeignKey(
        PetCategory, on_delete=models.CASCADE,
        verbose_name="分类", related_name="dogs"
    )
    price = models.DecimalField("价格(元)", max_digits=10, decimal_places=2)
    image_url = models.URLField("图片链接", max_length=500, blank=True)
    description = models.TextField("品种介绍")
    color = models.CharField("常见毛色", max_length=200, blank=True)
    weight = models.CharField("体重范围", max_length=50, help_text="例如: 25-35kg", blank=True)
    height = models.CharField("肩高范围", max_length=50, help_text="例如: 55-65cm", blank=True)
    lifespan = models.CharField("寿命", max_length=50, help_text="例如: 10-12年", blank=True)
    temperament = models.TextField("性格特点", blank=True)
    origin = models.CharField("原产地", max_length=100, blank=True)
    is_popular = models.BooleanField("是否热门", default=False)
    is_published = models.BooleanField("是否上架", default=True)
    created_at = models.DateTimeField("创建时间", auto_now_add=True)
    updated_at = models.DateTimeField("更新时间", auto_now=True)

    class Meta:
        verbose_name = "狗狗"
        verbose_name_plural = "狗狗"
        ordering = ["-is_popular", "-created_at"]

    def __str__(self):
        return "{0} - {1}".format(self.category.name, self.name)

    def get_absolute_url(self): pass


class Post(models.Model):
    CATEGORY_CHOICES = [
        ("share", "🙌 日常分享"),
        ("help", "🆘 求助"),
    ]
    author = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="作者", related_name="posts")
    title = models.CharField("标题", max_length=200)
    content = models.TextField("内容")
    category = models.CharField("分类", max_length=10, choices=CATEGORY_CHOICES, default="share")
    image_url = models.URLField("图片链接", max_length=500, blank=True)
    created_at = models.DateTimeField("发布时间", auto_now_add=True)
    updated_at = models.DateTimeField("更新时间", auto_now=True)

    class Meta:
        verbose_name = "帖子"
        verbose_name_plural = "帖子"
        ordering = ["-created_at"]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("pets:post_detail", args=[self.pk])


class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, verbose_name="帖子", related_name="comments")
    author = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="作者", related_name="comments")
    content = models.TextField("评论内容")
    created_at = models.DateTimeField("评论时间", auto_now_add=True)

    class Meta:
        verbose_name = "评论"
        verbose_name_plural = "评论"
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.author.username} 评论了 {self.post.title}"
class ProductCategory(models.Model):
    name = models.CharField("分类名称", max_length=50)
    slug = models.SlugField("标识", max_length=50, unique=True)
    icon = models.CharField("图标", max_length=50, blank=True)
    sort_order = models.IntegerField("排序", default=0)

    class Meta:
        verbose_name = "产品分类"
        verbose_name_plural = "产品分类"
        ordering = ["sort_order"]

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField("产品名称", max_length=200)
    category = models.ForeignKey(ProductCategory, on_delete=models.CASCADE, verbose_name="分类", related_name="products")
    price = models.DecimalField("价格", max_digits=10, decimal_places=2)
    image_url = models.URLField("图片链接", max_length=500, blank=True)
    description = models.TextField("描述", blank=True)
    stock = models.IntegerField("库存", default=0)
    is_published = models.BooleanField("是否上架", default=True)
    created_at = models.DateTimeField("创建时间", auto_now_add=True)

    class Meta:
        verbose_name = "产品"
        verbose_name_plural = "产品"
        ordering = ["-created_at"]

    def __str__(self):
        return self.name


class Cart(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="用户", related_name="carts")
    created_at = models.DateTimeField("创建时间", auto_now_add=True)

    class Meta:
        verbose_name = "购物车"
        verbose_name_plural = "购物车"

    def __str__(self):
        return f"{self.user.username}的购物车"


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, verbose_name="购物车", related_name="items")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name="产品")
    quantity = models.IntegerField("数量", default=1)

    class Meta:
        verbose_name = "购物车项"
        verbose_name_plural = "购物车项"

    def __str__(self):
        return f"{self.product.name} x {self.quantity}"


class Order(models.Model):
    STATUS_CHOICES = [
        ("pending", "待付款"),
        ("paid", "已付款"),
        ("shipped", "已发货"),
        ("completed", "已完成"),
        ("cancelled", "已取消"),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="用户", related_name="orders")
    phone = models.CharField("联系电话", max_length=20)
    address = models.TextField("收货地址")
    total = models.DecimalField("总金额", max_digits=10, decimal_places=2, default=0)
    status = models.CharField("状态", max_length=20, choices=STATUS_CHOICES, default="pending")
    created_at = models.DateTimeField("创建时间", auto_now_add=True)

    class Meta:
        verbose_name = "订单"
        verbose_name_plural = "订单"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.username}的订单 #{self.pk}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, verbose_name="订单", related_name="items")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name="产品")
    quantity = models.IntegerField("数量")
    price = models.DecimalField("单价", max_digits=10, decimal_places=2)

    class Meta:
        verbose_name = "订单项"
        verbose_name_plural = "订单项"

    def __str__(self):
        return f"{self.product.name} x {self.quantity}"