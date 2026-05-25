from django.db import models
from django.conf import settings
from store.models import Product


class Order(models.Model):

    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        PAID    = 'paid',    'Paid'
        FAILED  = 'failed',  'Failed'

    user              = models.ForeignKey(
                            settings.AUTH_USER_MODEL,
                            on_delete=models.CASCADE,
                            related_name='orders'
                        )
    status            = models.CharField(
                            max_length=10,
                            choices=Status.choices,
                            default=Status.PENDING
                        )
    total_price       = models.DecimalField(
                            max_digits=10,
                            decimal_places=2,
                            default=0.00
                        )
    payment_reference = models.CharField(
                            max_length=255,
                            blank=True,
                            null=True,
                            unique=True
                        )
    created_at        = models.DateTimeField(auto_now_add=True)
    updated_at        = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Order #{self.id} — {self.user.email} — {self.status}"

    def calculate_total(self):
        """
        Loops through all order items and sums their subtotals.
        Called after all items are added to the order.
        """
        self.total_price = sum(item.subtotal for item in self.items.all())
        self.save()


class OrderItem(models.Model):

    order       = models.ForeignKey(
                      Order,
                      on_delete=models.CASCADE,
                      related_name='items'
                  )
    product     = models.ForeignKey(
                      Product,
                      on_delete=models.CASCADE,
                      related_name='order_items'
                  )
    quantity    = models.PositiveIntegerField(default=1)
    unit_price  = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal    = models.DecimalField(max_digits=10, decimal_places=2)

    def save(self, *args, **kwargs):
        """
        Auto-calculate subtotal before saving.
        subtotal = unit_price × quantity
        """
        self.subtotal = self.unit_price * self.quantity
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.quantity} × {self.product.name} @ {self.unit_price}"