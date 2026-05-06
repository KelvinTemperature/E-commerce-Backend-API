from django.db import models

# Create your models here.
class Product(models.Model):
    name = models.CharField(max_length=255, blank=False)
    description = models.TextField(null=True, blank=True, default='')
    price = models.DecimalField(max_digits=20, decimal_places=2)
    stock = models.IntegerField(default=0)
    created_at  = models.DateTimeField(auto_now_add=True)
    last_update = models.DateTimeField(auto_now=True)
    

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name