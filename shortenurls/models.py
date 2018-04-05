# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import logging

import datetime
import requests
from django.core.exceptions import ValidationError
from django.core.validators import URLValidator
from django.db import models
from requests import RequestException

from shortenurls.const import SHORT_URL_LENGTH, SHORT_URL_MEMCACHE_KEY, DATE_FORMAT, DATETIME_FORMAT
from shortenurls.exceptions import URLException
from shortenurls.helpers import get_memcached_value, add_to_memcache


class Url(models.Model):
    original_url = models.CharField(max_length=255, validators=[URLValidator])
    shorten_url = models.CharField(max_length=255)
    created = models.DateTimeField(auto_now_add=True)
    last_visit_at = models.DateTimeField(blank=True, null=True)
    last_visit_from = models.CharField(max_length=39)

    def __str__(self):
        return self.original_url

    @staticmethod
    def check_url_validation(url):
        """ Check if provided URL is valid. First we check if URL is URL-like then try to reach the provided address to see if exists.
        """
        URLValidator(url)
        requests.get(url)

    @staticmethod
    def short_url_exist(url):
        url_exist = True
        try:
            Url.fetch(shorten_url=url)
        except Url.DoesNotExist:
            url_exist = False
        return url_exist

    @staticmethod
    def create(save=True, **kwargs):
        url_obj = Url(**kwargs)
        if save:
            url_obj.save()
        return url_obj

    @staticmethod
    def check_short_url(url):
        if len(url) != SHORT_URL_LENGTH:
            raise URLException("Invalid short url")

        memcache_format = SHORT_URL_MEMCACHE_KEY.format(url)
        url_obj = get_memcached_value(memcache_format)
        if url_obj is None:
            try:
                url_obj = Url.fetch(shorten_url=url)
            except Url.DoesNotExist:
                raise URLException("Short URL not found")
            if not add_to_memcache(memcache_format, url_obj):
                logging.warning("Memcaching for short url failed")
        return url_obj

    @staticmethod
    def update_last_visit(url_id, remote_address):
        url = Url.fetch(id=url_id)
        url.last_visit_from = remote_address
        url.last_visit_at = datetime.datetime.now()
        url.save()

    def json(self, host, secure):
        return {
            "id": self.id,
            "shortUrl": ("https://" if secure else "http://") + host+"/url/"+self.shorten_url,
            "redirectUrl": self.original_url,
            "created": datetime.datetime.strftime(self.created, DATE_FORMAT),
            "lastIP": self.last_visit_from,
        }

    @staticmethod
    def fetch(single=True, **kwargs):
        """ Fetch can return filtered by"""
        if single:
            resp = Url.objects.get(**kwargs)
        else:
            limit = 0
            resp = Url.objects.all()
            if "results" in kwargs:
                limit = int(kwargs['results'][0])
            if "from_date" in kwargs:
                day = datetime.datetime.strptime(kwargs['from_date'][0], DATE_FORMAT).date()
                beginning_of_day = datetime.datetime.combine(day, datetime.datetime.min.time())
                resp = resp.filter(created__gte=beginning_of_day)
            if "to_date" in kwargs:
                day = datetime.datetime.strptime(kwargs['to_date'][0], DATE_FORMAT).date()
                end_of_day = datetime.datetime.combine(day, datetime.datetime.max.time())
                resp = resp.filter(created__lte=end_of_day)
            if "date" in kwargs:
                day = datetime.datetime.strptime(kwargs['date'][0], DATE_FORMAT).date()
                beginning_of_day = datetime.datetime.combine(day, datetime.datetime.min.time())
                end_of_day = datetime.datetime.combine(day, datetime.datetime.max.time())
                resp = resp.filter(created__gte=beginning_of_day, created__lte=end_of_day)
            if "order_by" in kwargs:
                resp = resp.order_by(kwargs['order_by'][0])
            if limit != 0:
                resp = resp[:limit]
        return resp

    @staticmethod
    def fetch_all(host, secure=False, **kwargs):
        urls = Url.fetch(single=False, **kwargs)
        resp = []
        for url in urls:
            visits = UrlVisits.fetch(single=False, url_id=url.id)
            no_of_visits = 0
            for visit in visits:
                no_of_visits += visit.visits
            url_resp = url.json(host, secure)
            url_resp['visits'] = no_of_visits
            resp.append(url_resp)
        return resp

    @staticmethod
    def get_all_visits(id):
        resp = []
        visits = UrlVisits.fetch(single=False, url_id=id)
        for v in visits:
            resp.append(v.json())
        return resp

    @staticmethod
    def get_all_visitors(id):
        try:
            resp = []
            visitors = UrlVisitors.fetch(single=False, url_visit__url_id=id)
            for v in visitors:
                resp.append(v.json())
        except URLException as error:
            raise URLException(error)
        return resp


class UrlVisits(models.Model):
    url = models.ForeignKey(Url)
    date = models.DateField(auto_now_add=True)
    visits = models.IntegerField(default=0)
    last_visit_at = models.DateTimeField(blank=True, null=True)
    last_visit_from = models.CharField(max_length=39)

    def __str__(self):
        return datetime.date.strftime(self.date, DATE_FORMAT)

    @staticmethod
    def fetch(single=True, **kwargs):
        try:
            if single:
                resp = UrlVisits.objects.get(**kwargs)
            else:
                resp = UrlVisits.objects.filter(**kwargs)
        except(UrlVisits.DoesNotExist, UrlVisits.MultipleObjectsReturned) as error:
            raise URLException(error)
        return resp

    @staticmethod
    def create(save=True, **kwargs):
        url_obj = UrlVisits(**kwargs)
        if save:
            url_obj.save()
        return url_obj

    @staticmethod
    def mark_visit(url_id, remote_addr):
        try:
            try:
                url_visit_obj = UrlVisits.fetch(date=datetime.date.today(), url_id=url_id)
            except Exception as error:
                if isinstance(error, UrlVisits.MultipleObjectsReturned):
                    raise URLException("There is more than 1 visit record for today")
                else:
                    url_visit_obj = UrlVisits.create(False, url_id=url_id)
            url_visit_obj.visits += 1
            url_visit_obj.last_visit_from = remote_addr
            url_visit_obj.last_visit_at = datetime.datetime.now()
            url_visit_obj.save()
        except Exception as error:
            raise URLException(error)
        return url_visit_obj

    def json(self):
        return {
            "id": self.id,
            "visits": self.visits,
            "created": datetime.date.strftime(self.date, DATE_FORMAT),
            "lastVisitAt": datetime.datetime.strftime(self.last_visit_at, DATETIME_FORMAT) if self.last_visit_at is not None else None,
            "lastIP": self.last_visit_from
        }


class UrlVisitors(models.Model):
    remote_address = models.CharField(max_length=39)
    user_agent = models.CharField(max_length=255)
    url_visit = models.ForeignKey(UrlVisits)
    visits = models.IntegerField(default=0)
    first_visit = models.DateTimeField(auto_now_add=True)
    last_visit = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return self.remote_address

    @staticmethod
    def fetch(single=True, **kwargs):
        if single:
            resp = UrlVisitors.objects.get(**kwargs)
        else:
            resp = UrlVisitors.objects.filter(**kwargs)
        return resp

    @staticmethod
    def create(save=True, **kwargs):
        url_obj = UrlVisitors(**kwargs)
        if save:
            url_obj.save()
        return url_obj

    def json(self):
        return {
            "id": self.id,
            "visits": self.visits,
            "firstVisit": datetime.datetime.strftime(self.first_visit, DATETIME_FORMAT),
            "lastVisit": datetime.datetime.strftime(self.last_visit, DATETIME_FORMAT) if self.last_visit is not None else None,
            "ip": self.remote_address,
            "userAgent": self.user_agent
        }

    @staticmethod
    def mark_visitor(meta, visit):
        visitor_remote_address = meta['REMOTE_ADDR']
        visitor_user_agent = meta['HTTP_USER_AGENT'] if "HTTP_USER_AGENT" in meta else "N/A"
        try:
            visitor = UrlVisitors.fetch(url_visit_id=visit, remote_address=visitor_remote_address)
        except(UrlVisitors.DoesNotExist, UrlVisitors.MultipleObjectsReturned) as error:
            if isinstance(error, UrlVisitors.MultipleObjectsReturned):
                raise URLException("More than 1 visitor for the same url marked")
            else:
                visitor = UrlVisitors.create(False, url_visit_id=visit, remote_address=visitor_remote_address, user_agent=visitor_user_agent)
        visitor.visits += 1
        visitor.last_visit = datetime.datetime.now()
        visitor.save()
        try:
            Url.update_last_visit(visitor.url_visit.url_id, visitor_remote_address)
        except (Url.DoesNotExist, Url.MultipleObjectsReturned) as error:
            raise URLException(error)
        return visitor
