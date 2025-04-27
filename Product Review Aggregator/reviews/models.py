from django.db import models

# Create your models here.

class ReviewAnalysis(models.Model):
    url = models.URLField(max_length=500)
    pros = models.TextField()
    cons = models.TextField()
    overview = models.TextField()
    five_star_percentage = models.FloatField()
    four_star_percentage = models.FloatField()
    three_star_percentage = models.FloatField()
    two_star_percentage = models.FloatField()
    one_star_percentage = models.FloatField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Review Analysis for {self.url}"
