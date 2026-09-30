from django.db import models

class PlatformVisit(models.Model):
    platform = models.CharField(max_length=20, unique=True)
    count = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.platform}: {self.count}"
