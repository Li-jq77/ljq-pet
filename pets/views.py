from django.views.generic import ListView, DetailView
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.generic.edit import CreateView, UpdateView
from django.urls import reverse_lazy
from django.contrib import messages
from datetime import date, timedelta, datetime
import json
from django.db.models import Q

from .models import (PetCategory, Dog, PetProfile, WeightRecord,
                     Vaccination, Deworming, Reminder,
                     Post, Comment,
                     ProductCategory, Product, Cart, CartItem, Order, OrderItem)

def get_all_categories():
    return PetCategory.objects.all()

def get_dog_categories():
    return PetCategory.objects.filter(name__contains="犬")

def get_cat_categories():
    return PetCategory.objects.filter(name__contains="猫")

def get_profile_context(request):
    return {
        "categories": get_all_categories(),
        "dog_categories": get_dog_categories(),
        "cat_categories": get_cat_categories(),
        "pets_count": request.user.pets.filter(is_active=True).count(),
    }

class IndexView(ListView):
    model = Dog
    template_name = "pets/index.html"
    context_object_name = "dogs"
    def get_queryset(self):
        return Dog.objects.filter(is_published=True)[:12]
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["categories"] = get_all_categories()
        context["dog_categories"] = get_dog_categories()
        context["cat_categories"] = get_cat_categories()
        context["popular_dogs"] = Dog.objects.filter(is_published=True, is_popular=True)[:6]
        return context

class CategoryView(ListView):
    model = Dog
    template_name = "pets/category.html"
    context_object_name = "dogs"
    paginate_by = 12
    def get_queryset(self):
        self.category = PetCategory.objects.get(slug=self.kwargs["slug"])
        return Dog.objects.filter(is_published=True, category=self.category)
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["category"] = self.category
        context["categories"] = get_all_categories()
        context["dog_categories"] = get_dog_categories()
        context["cat_categories"] = get_cat_categories()
        return context

class DogDetailView(DetailView):
    model = Dog
    template_name = "pets/dog_detail.html"
    context_object_name = "dog"
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["categories"] = get_all_categories()
        context["dog_categories"] = get_dog_categories()
        context["cat_categories"] = get_cat_categories()
        context["related_dogs"] = Dog.objects.filter(is_published=True, category=self.object.category).exclude(pk=self.object.pk)[:4]
        return context

# ---- Auth ----

def login_view(request):
    if request.user.is_authenticated:
        return redirect("pets:index")
    if request.method == "POST":
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect(request.GET.get("next", "pets:index"))
    else:
        form = AuthenticationForm()
    return render(request, "pets/login.html", {"form": form, "categories": get_all_categories(), "dog_categories": get_dog_categories(), "cat_categories": get_cat_categories()})

def register_view(request):
    if request.user.is_authenticated:
        return redirect("pets:index")
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("pets:index")
    else:
        form = UserCreationForm()
    return render(request, "pets/register.html", {"form": form, "categories": get_all_categories(), "dog_categories": get_dog_categories(), "cat_categories": get_cat_categories()})

def logout_view(request):
    logout(request)
    return redirect("pets:index")

# ---- Profile ----

@login_required
def profile_view(request):
    my_pets = request.user.pets.filter(is_active=True)
    today = date.today()
    week_later = today + timedelta(days=7)
    upcoming = Reminder.objects.filter(pet__owner=request.user, reminder_date__gte=today, reminder_date__lte=week_later, is_completed=False).order_by("reminder_date")
    reminders_by_day = {}
    for r in upcoming:
        key = r.reminder_date.isoformat()
        if key not in reminders_by_day:
            reminders_by_day[key] = []
        reminders_by_day[key].append(r)
    next_vacc = Reminder.objects.filter(pet__owner=request.user, reminder_type="vaccination", reminder_date__gte=today, is_completed=False).order_by("reminder_date").first()
    next_dew = Reminder.objects.filter(pet__owner=request.user, reminder_type="deworming", reminder_date__gte=today, is_completed=False).order_by("reminder_date").first()
    context = get_profile_context(request)
    context.update({"my_pets": my_pets, "all_my_pets": request.user.pets.all(), "upcoming_reminders": upcoming, "reminders_by_day": reminders_by_day, "next_vaccination": next_vacc, "next_deworming": next_dew, "week_dates": [(today + timedelta(days=i)) for i in range(7)]})
    return render(request, "pets/profile.html", context)

# ---- Pet CRUD ----

@method_decorator(login_required, name="dispatch")
class PetCreateView(CreateView):
    model = PetProfile
    template_name = "pets/pet_form.html"
    fields = ["name", "species", "breed", "gender", "birthday", "adopted_date", "avatar_url", "color", "notes"]
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(get_profile_context(self.request))
        context["form_title"] = "添加新宠物"
        context["form_subtitle"] = "为你的毛孩子建立健康档案吧 🐾"
        context["submit_text"] = "添加宠物"
        return context
    def form_valid(self, form):
        form.instance.owner = self.request.user
        messages.success(self.request, f"🎉 成功添加 {form.instance.name}")
        return super().form_valid(form)
    def get_success_url(self):
        return reverse_lazy("pets:pet_detail", args=[self.object.pk])

@method_decorator(login_required, name="dispatch")
class PetUpdateView(UpdateView):
    model = PetProfile
    template_name = "pets/pet_form.html"
    fields = ["name", "species", "breed", "gender", "birthday", "adopted_date", "avatar_url", "color", "microchip_id", "notes", "is_active"]
    def dispatch(self, request, *args, **kwargs):
        pet = self.get_object()
        if pet.owner != request.user:
            messages.error(request, "这不是你的宠物哦 🐾")
            return redirect("pets:profile")
        return super().dispatch(request, *args, **kwargs)
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(get_profile_context(self.request))
        context["form_title"] = f"编辑 {self.object.name} 的档案"
        context["submit_text"] = "保存修改"
        return context
    def form_valid(self, form):
        messages.success(self.request, f"✅ {form.instance.name} 已更新！")
        return super().form_valid(form)
    def get_success_url(self):
        return reverse_lazy("pets:pet_detail", args=[self.object.pk])

@login_required
def pet_detail_view(request, pk):
    pet = get_object_or_404(PetProfile, pk=pk)
    if pet.owner != request.user:
        messages.error(request, "这不是你的宠物哦 🐾")
        return redirect("pets:profile")
    weight_records = pet.weight_records.order_by("recorded_at")
    vaccinations = pet.vaccinations.order_by("-administered_date")
    dewormings = pet.dewormings.order_by("-administered_date")
    reminders = pet.reminders.filter(is_completed=False).order_by("reminder_date")[:10]
    context = get_profile_context(request)
    context.update({"pet": pet, "weight_records": weight_records, "vaccinations": vaccinations, "dewormings": dewormings, "reminders": reminders})
    return render(request, "pets/pet_detail.html", context)

@login_required
def pet_delete_view(request, pk):
    pet = get_object_or_404(PetProfile, pk=pk)
    if pet.owner != request.user:
        return redirect("pets:profile")
    pet_name = pet.name
    pet.delete()
    messages.success(request, f"已移除 {pet_name} 的档案")
    return redirect("pets:profile")

# ---- Weight ----

@login_required
def add_weight_record(request, pet_pk):
    pet = get_object_or_404(PetProfile, pk=pet_pk)
    if pet.owner != request.user:
        return redirect("pets:profile")
    if request.method == "POST":
        weight = request.POST.get("weight")
        recorded_at = request.POST.get("recorded_at", date.today())
        if weight:
            WeightRecord.objects.create(pet=pet, weight=weight, recorded_at=recorded_at)
            messages.success(request, f"⚖️ 已记录 {pet.name} 的体重：{weight}kg")
        return redirect("pets:pet_detail", pk=pet_pk)
    return redirect("pets:pet_detail", pk=pet_pk)

@login_required
def delete_weight_record(request, pk):
    record = get_object_or_404(WeightRecord, pk=pk)
    pet_pk = record.pet.pk
    if record.pet.owner != request.user:
        return redirect("pets:profile")
    record.delete()
    return redirect("pets:pet_detail", pk=pet_pk)

# ---- Vaccination ----

@login_required
def add_vaccination(request, pet_pk):
    pet = get_object_or_404(PetProfile, pk=pet_pk)
    if pet.owner != request.user:
        return redirect("pets:profile")
    if request.method == "POST":
        vaccine_type = request.POST.get("vaccine_type")
        vaccine_name = request.POST.get("vaccine_name", "")
        dose_number = request.POST.get("dose_number", 1)
        administered_date = request.POST.get("administered_date")
        next_due_date = request.POST.get("next_due_date", "") or None
        clinic = request.POST.get("clinic", "")
        notes = request.POST.get("notes", "")
        if vaccine_type and administered_date:
            vacc = Vaccination.objects.create(pet=pet, vaccine_type=vaccine_type, vaccine_name=vaccine_name, dose_number=dose_number, administered_date=administered_date, next_due_date=next_due_date, clinic=clinic, notes=notes)
            messages.success(request, f"💉 已记录 {pet.name} 的疫苗接种")
            if next_due_date:
                Reminder.objects.create(pet=pet, reminder_type="vaccination", title=f"{pet.name} 的疫苗 - 第{dose_number}针", reminder_date=next_due_date)
        return redirect("pets:pet_detail", pk=pet_pk)
    return redirect("pets:pet_detail", pk=pet_pk)

@login_required
def delete_vaccination(request, pk):
    vacc = get_object_or_404(Vaccination, pk=pk)
    pet_pk = vacc.pet.pk
    if vacc.pet.owner != request.user:
        return redirect("pets:profile")
    vacc.delete()
    return redirect("pets:pet_detail", pk=pet_pk)

# ---- Deworming ----

@login_required
def add_deworming(request, pet_pk):
    pet = get_object_or_404(PetProfile, pk=pet_pk)
    if pet.owner != request.user:
        return redirect("pets:profile")
    if request.method == "POST":
        deworming_type = request.POST.get("deworming_type")
        product_name = request.POST.get("product_name", "")
        administered_date = request.POST.get("administered_date")
        next_due_date = request.POST.get("next_due_date", "") or None
        if deworming_type and administered_date:
            dw = Deworming.objects.create(pet=pet, deworming_type=deworming_type, product_name=product_name, administered_date=administered_date, next_due_date=next_due_date)
            messages.success(request, f"🪱 已记录 {pet.name} 的驱虫")
            if next_due_date:
                Reminder.objects.create(pet=pet, reminder_type="deworming", title=f"{pet.name} 的驱虫", reminder_date=next_due_date)
        return redirect("pets:pet_detail", pk=pet_pk)
    return redirect("pets:pet_detail", pk=pet_pk)

@login_required
def delete_deworming(request, pk):
    dw = get_object_or_404(Deworming, pk=pk)
    pet_pk = dw.pet.pk
    if dw.pet.owner != request.user:
        return redirect("pets:profile")
    dw.delete()
    return redirect("pets:pet_detail", pk=pet_pk)

# ---- Reminders ----

@login_required
def calendar_view(request):
    my_pets = request.user.pets.filter(is_active=True)
    today = date.today()
    year = request.GET.get("year", today.year)
    month = request.GET.get("month", today.month)
    try: cur_year, cur_month = int(year), int(month)
    except: cur_year, cur_month = today.year, today.month
    start_date = date(cur_year, cur_month, 1)
    if cur_month == 12:
        end_date = date(cur_year + 1, 1, 1) - timedelta(days=1)
    else:
        end_date = date(cur_year, cur_month + 1, 1) - timedelta(days=1)
    reminders = Reminder.objects.filter(pet__owner=request.user, reminder_date__gte=start_date, reminder_date__lte=end_date).order_by("reminder_date")
    cal_days = []
    for _ in range(start_date.weekday()):
        cal_days.append(None)
    for day in range(1, end_date.day + 1):
        d = date(cur_year, cur_month, day)
        cal_days.append({"day": day, "date": d, "is_today": d == today, "is_past": d < today, "reminders": [r for r in reminders if r.reminder_date.day == day]})
    context = get_profile_context(request)
    context.update({"my_pets": my_pets, "reminders": reminders, "calendar_days": cal_days, "cur_year": cur_year, "cur_month": cur_month})
    return render(request, "pets/calendar.html", context)

@login_required
def add_reminder(request, pet_pk):
    pet = get_object_or_404(PetProfile, pk=pet_pk)
    if pet.owner != request.user: return redirect("pets:profile")
    if request.method == "POST":
        title = request.POST.get("title")
        reminder_date = request.POST.get("reminder_date")
        if title and reminder_date:
            Reminder.objects.create(pet=pet, reminder_type="custom", title=title, description=request.POST.get("description", ""), reminder_date=reminder_date)
        return redirect("pets:pet_detail", pk=pet_pk)
    return redirect("pets:pet_detail", pk=pet_pk)

@login_required
def complete_reminder(request, pk):
    reminder = get_object_or_404(Reminder, pk=pk)
    if reminder.pet.owner != request.user: return redirect("pets:profile")
    reminder.is_completed = True
    reminder.completed_at = datetime.now()
    reminder.save()
    if reminder.repeat_interval_days:
        n = reminder.reminder_date + timedelta(days=reminder.repeat_interval_days)
        Reminder.objects.create(pet=reminder.pet, reminder_type=reminder.reminder_type, title=reminder.title, reminder_date=n, repeat_interval_days=reminder.repeat_interval_days)
    return redirect(request.GET.get("next", "pets:profile"))

@login_required
def delete_reminder(request, pk):
    reminder = get_object_or_404(Reminder, pk=pk)
    if reminder.pet.owner != request.user: return redirect("pets:profile")
    reminder.delete()
    return redirect(request.GET.get("next", "pets:profile"))

@login_required
def generate_smart_reminders(request, pet_pk):
    pet = get_object_or_404(PetProfile, pk=pet_pk)
    if pet.owner != request.user: return redirect("pets:profile")
    today = date.today()
    count = 0
    for rtype, title, days, repeat in [("checkup","年度体检",30,365),("nails","剪指甲",14,14),("weight","称体重",7,30),("teeth","刷牙",3,7),("bath","洗澡",21,30)]:
        d = today + timedelta(days=days)
        if not Reminder.objects.filter(pet=pet, reminder_type=rtype, reminder_date=d).exists():
            Reminder.objects.create(pet=pet, reminder_type=rtype, title=title, reminder_date=d, repeat_interval_days=repeat)
            count += 1
    if not Reminder.objects.filter(pet=pet, reminder_type="deworming").exists():
        Reminder.objects.create(pet=pet, reminder_type="deworming", title=f"{pet.name} 的驱虫日", reminder_date=today+timedelta(days=60), repeat_interval_days=90)
        count += 1
    messages.success(request, f"🤖 已智能生成 {count} 条提醒！")
    return redirect("pets:pet_detail", pk=pet_pk)

# ---- Post/Comment ----

class PostListView(ListView):
    model = Post
    template_name = "pets/post_list.html"
    context_object_name = "posts"
    paginate_by = 12
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["categories"] = get_all_categories()
        context["dog_categories"] = get_dog_categories()
        context["cat_categories"] = get_cat_categories()
        return context

@login_required
def post_create_view(request):
    if request.method == "POST":
        title = request.POST.get("title")
        content = request.POST.get("content")
        category = request.POST.get("category", "share")
        if title and content:
            Post.objects.create(author=request.user, title=title, content=content, category=category)
            return redirect("pets:post_list")
    return render(request, "pets/post_form.html", {"categories": get_all_categories(), "dog_categories": get_dog_categories(), "cat_categories": get_cat_categories()})

def post_detail_view(request, pk):
    post = get_object_or_404(Post, pk=pk)
    if request.method == "POST" and request.user.is_authenticated:
        content = request.POST.get("content")
        if content:
            Comment.objects.create(post=post, author=request.user, content=content)
            return redirect("pets:post_detail", pk=pk)
    return render(request, "pets/post_detail.html", {"categories": get_all_categories(), "dog_categories": get_dog_categories(), "cat_categories": get_cat_categories(), "post": post, "comments": post.comments.all()})

# ---- Products ----

@login_required
def product_list_view(request, slug=None):
    categories = ProductCategory.objects.all()
    if slug:
        current_cat = get_object_or_404(ProductCategory, slug=slug)
        products = Product.objects.filter(is_published=True, category=current_cat)
    else:
        current_cat = None
        products = Product.objects.filter(is_published=True)
    context = get_profile_context(request)
    context.update({"product_categories": categories, "current_category": current_cat, "products": products})
    return render(request, "pets/product_list.html", context)

# ---- Cart ----

@login_required
def add_to_cart(request, product_pk):
    product = get_object_or_404(Product, pk=product_pk)
    cart, _ = Cart.objects.get_or_create(user=request.user)
    item, created = CartItem.objects.get_or_create(cart=cart, product=product)
    if not created:
        item.quantity += 1
        item.save()
    messages.success(request, f"✅ {product.name} 已加入购物车")
    return redirect("pets:cart")

@login_required
def remove_from_cart(request, item_pk):
    item = get_object_or_404(CartItem, pk=item_pk, cart__user=request.user)
    item.delete()
    return redirect("pets:cart")

@login_required
def cart_quantity(request, item_pk, action):
    item = get_object_or_404(CartItem, pk=item_pk, cart__user=request.user)
    if action == "inc":
        item.quantity += 1
        item.save()
    elif action == "dec":
        if item.quantity > 1:
            item.quantity -= 1
            item.save()
        else:
            item.delete()
    return redirect("pets:cart")

@login_required
def cart_view(request):
    cart = Cart.objects.filter(user=request.user).first()
    items = cart.items.all() if cart else []
    total = sum(item.product.price * item.quantity for item in items) if items else 0
    context = get_profile_context(request)
    context.update({"cart": cart, "cart_items": items, "total": total})
    return render(request, "pets/cart.html", context)

# ---- Orders ----

@login_required
def checkout_view(request):
    cart = Cart.objects.filter(user=request.user).first()
    if not cart or not cart.items.exists():
        messages.warning(request, "购物车是空的哦 🛒")
        return redirect("pets:cart")
    items = cart.items.all()
    total = sum(item.product.price * item.quantity for item in items)
    if request.method == "POST":
        phone = request.POST.get("phone", "")
        address = request.POST.get("address", "")
        if not phone or not address:
            messages.error(request, "请填写联系电话和收货地址")
        else:
            order = Order.objects.create(user=request.user, phone=phone, address=address, total=total)
            for item in items:
                OrderItem.objects.create(order=order, product=item.product, quantity=item.quantity, price=item.product.price)
            cart.items.all().delete()
            messages.success(request, "🎉 订单已创建！请尽快完成支付")
            return redirect("pets:order_detail", pk=order.pk)
    context = get_profile_context(request)
    context.update({"cart_items": items, "total": total})
    return render(request, "pets/checkout.html", context)

@login_required
def order_list_view(request):
    orders = Order.objects.filter(user=request.user)
    context = get_profile_context(request)
    context.update({"orders": orders})
    return render(request, "pets/order_list.html", context)

@login_required
def order_detail_view(request, pk):
    order = get_object_or_404(Order, pk=pk, user=request.user)
    context = get_profile_context(request)
    context.update({"order": order})
    return render(request, "pets/order_detail.html", context)

@login_required
def cancel_order_view(request, pk):
    order = get_object_or_404(Order, pk=pk, user=request.user)
    if order.status == "pending":
        order.status = "cancelled"
        order.save()
        messages.success(request, "订单已取消")
    return redirect("pets:order_detail", pk=pk)

@login_required
def pay_order_view(request, pk):
    order = get_object_or_404(Order, pk=pk, user=request.user)
    if order.status == "pending":
        order.status = "paid"
        order.save()
        messages.success(request, "💳 支付成功！感谢您的购买 🎉")
    return redirect("pets:order_detail", pk=pk)
