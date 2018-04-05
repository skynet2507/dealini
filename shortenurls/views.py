# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import json
import logging
import uuid

from django.core.exceptions import ValidationError
from django.http import HttpResponse, HttpResponsePermanentRedirect
from requests import RequestException

from shortenurls.const import SHORT_URL_LENGTH, ORIGINAL_URL_MEMCACHE_KEY
from shortenurls.exceptions import URLException
from shortenurls.helpers import add_to_memcache, get_memcached_value
from shortenurls.models import Url, UrlVisits, UrlVisitors


def generate_short_url(request):
    json_data = json.loads(request.body)
    url_to_short = json_data.get("url")
    cached = False
    # If url doesn't contain http or https, add to the url
    if "http" not in url_to_short:
        url_to_short = "http://"+url_to_short
    try:
        Url.check_url_validation(url_to_short)
    except (ValidationError, RequestException):
        return HttpResponse("Provided URL is not valid.", status=400)
    status_code = 200
    memcache_format = ORIGINAL_URL_MEMCACHE_KEY.format(url_to_short)
    try:
        # check memcache first
        url_obj = get_memcached_value(memcache_format)
        if url_obj is None:
            # Original url is not in memcache: check database
            url_obj = Url.fetch(original_url=url_to_short)
        else:
            cached = True
    except Url.DoesNotExist:
        # Original url doesn't exist
        url_obj = None
    # Generate shorten url
    if url_obj is None:
        while True:
            # Generating short_url based on SHORT_URL_LENGTH constant
            short_url = str(uuid.uuid4())[:SHORT_URL_LENGTH]
            # Keep in mind that short_url must be unique!
            if not Url.short_url_exist(short_url):
                # Shorted URL is unique
                break

        url_obj = Url.create(original_url=url_to_short, shorten_url=short_url)
        status_code = 201
    if not cached:
        if add_to_memcache(memcache_format, url_obj):
            logging.info("Cache stored.")
    resp = ("https://" if request.is_secure() else "http://") + (request.META['HTTP_HOST'] if 'HTTP_HOST' in request.META else "")+"/url/"+url_obj.shorten_url
    return HttpResponse(json.dumps({"shortenUrl": resp}), status=status_code)


def get_url(request, url):
    try:
        url_obj = Url.check_short_url(url)
        visit = UrlVisits.mark_visit(url_obj.id, request.META['REMOTE_ADDR'])
        visitor = UrlVisitors.mark_visitor(request.META, visit.id)
        return HttpResponsePermanentRedirect(url_obj.original_url)
    except URLException as fail:
        return HttpResponse(fail)


def urls_list(request):
    try:
        resp = Url.fetch_all(request.META['HTTP_HOST'], request.is_secure(), **request.GET)
    except Exception as error:
        return HttpResponse(error, status=500)
    return HttpResponse(json.dumps(resp), status=200, content_type="application/json")


def get_url_visits(request, pk):
    try:
        resp = Url.get_all_visits(pk)
    except Exception as error:
        return HttpResponse(error, status=500)
    return HttpResponse(json.dumps(resp), status=200, content_type="application/json")


def get_url_visitors(request, pk):
    try:
        resp = Url.get_all_visitors(pk)
    except Exception as error:
        return HttpResponse(error, status=500)
    return HttpResponse(json.dumps(resp), status=200, content_type="application/json")