from django.db import models
from pgvector.django import VectorField


class Segment(models.Model):
    name = models.CharField(max_length=100)
    centroid = VectorField(dimensions=1536)


class Case(models.Model):
    name = models.CharField(max_length=150)
    niche_raw = models.CharField(max_length=150)
    niche_vec = VectorField(dimensions=1536)
    segment = models.ForeignKey(
        Segment, null=True, on_delete=models.SET_NULL, related_name='cases'
    )
    result = models.TextField()

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
