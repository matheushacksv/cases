from django.contrib import admin

from . import services
from .models import Case, Segment


@admin.register(Case)
class CaseAdmin(admin.ModelAdmin):
    list_display = ('name', 'niche_raw', 'segment', 'created_at')
    list_filter = ('segment',)
    search_fields = ('name', 'niche_raw', 'result')
    readonly_fields = ('niche_vec', 'created_at', 'updated_at')

    def save_model(self, request, obj, form, change):
        if 'niche_raw' in form.changed_data or not obj.niche_vec:
            segment, vec = services.assign_segment(obj.niche_raw.strip())
            obj.niche_vec = vec
            if not change:
                obj.segment = segment
        super().save_model(request, obj, form, change)


@admin.register(Segment)
class SegmentAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)
