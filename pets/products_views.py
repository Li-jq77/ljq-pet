def product_list_view(request, slug=None):
                                                                                                                                                    """产品列表页面"""
                                                                                                                                                    categories = ProductCategory.objects.all()
                                                                                                                                                    if slug:
                                                                                                                                                        current_cat = get_object_or_404(ProductCategory,
                                                                                                                                                        slug=slug)
                                                                                                                                                        products = Product.objects.filter(
                                                                                                                                                        is_published=True,
                                                                                                                                                        category=current_cat)
                                                                                                                                                        else:
                                                                                                                                                            current_cat =
                                                                                                                                                            None

                                                                                                                                                            products = Product.objects.filter(is_published=True)
                                                                                                                                                            context = get_profile_context(request)
                                                                                                                                                            context.update({
                                                                                                                                                            "categories": get_all_categories(),
                                                                                                                                                            "dog_categories": get_dog_categories(),
                                                                                                                                                            "cat_categories": get_cat_categories(),
                                                                                                                                                            "product_categories": categories,
                                                                                                                                                            "current_category": current_cat,
                                                                                                                                                            "products": products,
                                                                                                                                                            })
                                                                                                                                                            return render(request, "pets/product_list.html", context)

                                                                                                                                                            @login_required

                                                                                                                                                            def add_to_cart(request, product_pk):
                                                                                                                                                                """添加到购物车"""
                                                                                                                                                                product = get_object_or_404(Product,
                                                                                                                                                                pk=product_pk)
                                                                                                                                                                cart, _ = Cart.objects.get_or_create(user=request.user)
                                                                                                                                                                item, created = CartItem.objects.get_or_create(
                                                                                                                                                                cart=cart,
                                                                                                                                                                product=product)
                                                                                                                                                                if
                                                                                                                                                                not created:
                                                                                                                                                                    item.quantity += 1
                                                                                                                                                                    item.save()
                                                                                                                                                                    messages.success(request, f"✅ {product.name} 已加入购物车")
                                                                                                                                                                    return redirect("pets:cart")

                                                                                                                                                                    @login_required

                                                                                                                                                                    def remove_from_cart(request, item_pk):
                                                                                                                                                                        """从购物车移除"""
                                                                                                                                                                        item = get_object_or_404(
                                                                                                                                                                        CartItem, pk=item_pk,
                                                                                                                                                                        cart__user=request.user)
                                                                                                                                                                        item.delete()
                                                                                                                                                                        messages.success(request, "已从购物车移除")
                                                                                                                                                                        return redirect("pets:cart")

                                                                                                                                                                        @login_required

                                                                                                                                                                        def cart_view(request):
                                                                                                                                                                            """购物车页面"""
                                                                                                                                                                            cart = Cart.objects.filter(
                                                                                                                                                                            user=request.user).first()
                                                                                                                                                                            items = cart.items.all()
                                                                                                                                                                            if cart else []
                                                                                                                                                                            total = sum(
                                                                                                                                                                            item.product.price *
                                                                                                                                                                            item.quantity
                                                                                                                                                                            f
                                                                                                                                                                            or item
                                                                                                                                                                            in items)
                                                                                                                                                                            context = get_profile_context(request)
                                                                                                                                                                            context.update({
                                                                                                                                                                            "cart": cart,
                                                                                                                                                                            "cart_items": items,
                                                                                                                                                                            "total": total,
                                                                                                                                                                            "categories": get_all_categories(),
                                                                                                                                                                            "dog_categories": get_dog_categories(),
                                                                                                                                                                            "cat_categories": get_cat_categories(),
                                                                                                                                                                            })
                                                                                                                                                                            return render(request, "pets/cart.html", context)

                                                                                                                                                                            @login_required

                                                                                                                                                                            def checkout_view(request):
                                                                                                                                                                                """确认订单页面"""
                                                                                                                                                                                cart = Cart.objects.filter(
                                                                                                                                                                                user=request.user).first()
                                                                                                                                                                                if
                                                                                                                                                                                not cart
                                                                                                                                                                                or
                                                                                                                                                                                not cart.items.exists():
                                                                                                                                                                                    messages.warning(request, "购物车是空的哦 🛒")
                                                                                                                                                                                    return redirect("pets:cart")
                                                                                                                                                                                    items = cart.items.all()
                                                                                                                                                                                    total = sum(
                                                                                                                                                                                    item.product.price * item.quantity
                                                                                                                                                                                    f
                                                                                                                                                                                    or item
                                                                                                                                                                                    in items)
                                                                                                                                                                                    if request.method == "POST":
                                                                                                                                                                                        phone = request.POST.get("phone", "")
                                                                                                                                                                                        address = request.POST.get(
                                                                                                                                                                                        "address", "")
                                                                                                                                                                                        if
                                                                                                                                                                                        not phone
                                                                                                                                                                                        or
                                                                                                                                                                                        not address:
                                                                                                                                                                                            messages.error(
                                                                                                                                                                                            request, "请填写联系电话和收货地址")
                                                                                                                                                                                            else:
                                                                                                                                                                                                order = Order.objects.create(

                                                                                                                                                                                                user=request.user, phone=phone,
                                                                                                                                                                                                address=address,
                                                                                                                                                                                                total=total)
                                                                                                                                                                                                f
                                                                                                                                                                                                or item
                                                                                                                                                                                                in items:
                                                                                                                                                                                                    OrderItem.objects.create(

                                                                                                                                                                                                    order=order, product=item.product,
                                                                                                                                                                                                    quantity=item.quantity,
                                                                                                                                                                                                    price=item.product.price)
                                                                                                                                                                                                    cart.items.all().delete()
                                                                                                                                                                                                    messages.success(
                                                                                                                                                                                                    request, "🎉 订单已创建！请尽快完成支付")
                                                                                                                                                                                                    return redirect(
                                                                                                                                                                                                    "pets:order_detail", pk=order.pk)
                                                                                                                                                                                                    context = get_profile_context(
                                                                                                                                                                                                    request)
                                                                                                                                                                                                    context.update({
                                                                                                                                                                                                    "cart_items": items,
                                                                                                                                                                                                    "total": total,
                                                                                                                                                                                                    "categories": get_all_categories(),
                                                                                                                                                                                                    "dog_categories": get_dog_categories(),
                                                                                                                                                                                                    "cat_categories": get_cat_categories(),
                                                                                                                                                                                                    })
                                                                                                                                                                                                    return render(
                                                                                                                                                                                                    request, "pets/checkout.html", context)

                                                                                                                                                                                                    @login_required

                                                                                                                                                                                                    def order_list_view(
                                                                                                                                                                                                    request):
                                                                                                                                                                                                        """订单列表"""
                                                                                                                                                                                                        orders = Order.objects.filter(
                                                                                                                                                                                                        user=request.user)
                                                                                                                                                                                                        context = get_profile_context(
                                                                                                                                                                                                        request)
                                                                                                                                                                                                        context.update({
                                                                                                                                                                                                        "orders": orders,
                                                                                                                                                                                                        "categories": get_all_categories(),
                                                                                                                                                                                                        "dog_categories": get_dog_categories(),
                                                                                                                                                                                                        "cat_categories": get_cat_categories(),
                                                                                                                                                                                                        })
                                                                                                                                                                                                        return render(
                                                                                                                                                                                                        request, "pets/order_list.html", context)

                                                                                                                                                                                                        @login_required

                                                                                                                                                                                                        def order_detail_view(
                                                                                                                                                                                                        request, pk):
                                                                                                                                                                                                            """订单详情"""
                                                                                                                                                                                                            order = get_object_or_404(
                                                                                                                                                                                                            Order, pk=pk, user=request.user)
                                                                                                                                                                                                            context = get_profile_context(
                                                                                                                                                                                                            request)
                                                                                                                                                                                                            context.update({
                                                                                                                                                                                                            "order": order,
                                                                                                                                                                                                            "categories": get_all_categories(),
                                                                                                                                                                                                            "dog_categories": get_dog_categories(),
                                                                                                                                                                                                            "cat_categories": get_cat_categories(),
                                                                                                                                                                                                            })
                                                                                                                                                                                                            return render(
                                                                                                                                                                                                            request, "pets/order_detail.html", context)

                                                                                                                                                                                                            @login_required

                                                                                                                                                                                                            def cancel_order_view(
                                                                                                                                                                                                            request, pk):
                                                                                                                                                                                                                """取消订单"""
                                                                                                                                                                                                                order = get_object_or_404(
                                                                                                                                                                                                                Order, pk=pk,
                                                                                                                                                                                                                user=request.user)
                                                                                                                                                                                                                if order.status == "pending":
                                                                                                                                                                                                                    order.status = "cancelled"
                                                                                                                                                                                                                    order.save()
                                                                                                                                                                                                                    messages.success(
                                                                                                                                                                                                                    request, "订单已取消")
                                                                                                                                                                                                                    else:
                                                                                                                                                                                                                        messages.error(
                                                                                                                                                                                                                        request, "当前订单状态无法取消")
                                                                                                                                                                                                                        return redirect(
                                                                                                                                                                                                                        "pets:order_detail", pk=pk)

                                                                                                                                                                                                                        @login_required

                                                                                                                                                                                                                        def pay_order_view(
                                                                                                                                                                                                                        request, pk):
                                                                                                                                                                                                                            """模拟支付"""
                                                                                                                                                                                                                            order = get_object_or_404(
                                                                                                                                                                                                                            Order, pk=pk,
                                                                                                                                                                                                                            user=request.user)
                                                                                                                                                                                                                            if order.status == "pending":
                                                                                                                                                                                                                                order.status = "paid"
                                                                                                                                                                                                                                order.save()
                                                                                                                                                                                                                                messages.success(
                                                                                                                                                                                                                                request, "💳 支付成功！感谢您的购买 🎉")
                                                                                                                                                                                                                                else:
                                                                                                                                                                                                                                    messages.error(
                                                                                                                                                                                                                                    request, "当前订单状态无法支付")
                                                                                                                                                                                                                                    return redirect(
                                                                                                                                                                                                                                    "pets:order_detail", pk=pk)


django.contrib.auth.decorators

get_profile_context(request):    """获取个人中心通用上下文"""
                                                    reminders_by_day[key].append(r)
next_vaccination = Reminder.objects.filter(

CRUD ----------@method_decorator(login_required, name='dispatch')
                                                                                                                reminders_by_date[key].append(r)
first_weekday = start_date.weekday()  # 0=周一
                                                                                                                                    and pet_age_months < 12
default_reminders = []
default_reminders.append({        'type': 'checkup',
'title': f'{pet.name} 的年度体检'
'desc': '建议每年带毛孩子做一次全面体检，包括血常规、生化等'
'days_from_now': 30
'repeat': 365,    })
default_reminders.append({        'type': 'nails',
'title': f'给 {pet.name} 剪指甲'
'desc': '定期剪指甲，注意不要剪到血线哦'
'days_from_now': 14
'repeat': 14,    })
default_reminders.append({        'type': 'weight',
'title': f'给 {pet.name} 称体重'
'desc': '定期监测体重，保持健康体态'
'days_from_now': 7
'repeat': 30,    })
has_deworming = Reminder.objects.filter(pet=pet,
                                                                                                                                                                                                                                                                        not has_deworming:        default_reminders.append({            'type': 'deworming',
                                                                                                                                    'title': f'{pet.name} 的驱虫日'
                                                                                                                                    'desc': '建议每3个月进行一次体内驱虫，每月一次体外驱虫'
                                                                                                                                    'days_from_now': 60
                                                                                                                                    'repeat': 90,        })
default_reminders.append({        'type': 'teeth',
'title': f'给 {pet.name} 刷牙'
'desc': '定期清洁牙齿，预防牙结石和口臭'
'days_from_now': 3
'repeat': 7,    })
default_reminders.append({        'type': 'bath',
'title': f'给 {pet.name} 洗澡'
'desc': pet.species == 'cat'