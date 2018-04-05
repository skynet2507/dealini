# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin

# Register your models here.
from shortenurls.models import Url, UrlVisits, UrlVisitors


class VisitsInLine(admin.StackedInline):
    model = UrlVisits


class VisitorsInLine(admin.StackedInline):
    model = UrlVisitors


class URLAdmin(admin.ModelAdmin):
    inlines = [VisitsInLine]


class VisitsAdmin(admin.ModelAdmin):
    inlines = [VisitorsInLine]


admin.site.register(Url, URLAdmin)
admin.site.register(UrlVisits, VisitsAdmin)
