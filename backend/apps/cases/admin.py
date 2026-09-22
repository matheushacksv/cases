import csv
import io

from django.contrib import admin, messages
from django.shortcuts import redirect, render
from django.urls import path

from . import services
from .embeddings import embed
from .models import Case, Segment
from .schemas import CaseInDTO

COLS = {'nome': 'name', 'nicho': 'niche_raw', 'resultado': 'result'}


@admin.register(Case)
class CaseAdmin(admin.ModelAdmin):
    list_display = ('name', 'niche_raw', 'segment', 'created_at')
    list_filter = ('segment',)
    search_fields = ('name', 'niche_raw', 'result')
    # niche_vec fora do form: como readonly quebrava a página (pgvector devolve
    # numpy.ndarray, e o admin faz "value in field.empty_values" pra exibir
    # readonly, o que levanta ValueError em array com >1 elemento).
    exclude = ('niche_vec',)
    readonly_fields = ('created_at', 'updated_at')

    def save_model(self, request, obj, form, change):
        # obj.niche_vec é numpy.ndarray quando populado: "not array" levanta
        # ValueError (truth value ambíguo p/ array com >1 elemento).
        if 'niche_raw' in form.changed_data or obj.niche_vec is None:
            segment, vec = services.assign_segment(obj.niche_raw.strip())
            obj.niche_vec = vec
            if not change:
                obj.segment = segment
        super().save_model(request, obj, form, change)

    def get_urls(self):
        my = [
            path(
                'import-csv/',
                self.admin_site.admin_view(self.import_csv),
                name='cases_case_import_csv',
            )
        ]
        return my + super().get_urls()

    def import_csv(self, request):
        if request.method == 'POST':
            ok, errs = self._do_import(request.FILES['csv_file'])
            if ok:
                self.message_user(
                    request, f'{ok} case(s) importado(s).', messages.SUCCESS
                )
            for e in errs:
                self.message_user(request, e, messages.ERROR)
            return redirect('..')
        return render(
            request,
            'admin/cases/case/import_csv.html',
            {**self.admin_site.each_context(request), 'title': 'Importar CSV'},
        )

    @staticmethod
    def _do_import(f):
        raw = f.read().decode('utf-8-sig', errors='replace')
        try:
            dialect = csv.Sniffer().sniff(raw[:1024], delimiters=';,')
        except csv.Error:
            dialect = csv.excel
        reader = csv.DictReader(io.StringIO(raw), dialect=dialect)
        ok, errs = 0, []
        for i, row in enumerate(reader, start=2):
            try:
                data = CaseInDTO(
                    **{field: (row.get(col) or '') for col, field in COLS.items()}
                )
                services.create_case(data)
                ok += 1
            except Exception as ex:
                errs.append(f'Linha {i}: {ex}')
        return ok, errs


@admin.register(Segment)
class SegmentAdmin(admin.ModelAdmin):
    # centroid é um vetor de 1536 dims: ninguém digita isso. Se some sozinho
    # a partir do "name" (mesma lógica que assign_segment usa pra semear um
    # segmento novo), igual o CaseAdmin já faz com niche_vec.
    exclude = ('centroid',)
    list_display = ('name',)
    search_fields = ('name',)

    def save_model(self, request, obj, form, change):
        # mesmo motivo do CaseAdmin acima: "not array" quebra em numpy.ndarray.
        if 'name' in form.changed_data or obj.centroid is None:
            obj.centroid = embed(obj.name.strip())
        super().save_model(request, obj, form, change)
