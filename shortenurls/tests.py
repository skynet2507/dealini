# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import datetime
import json

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone
from requests import RequestException

from models import Url, UrlVisits, UrlVisitors
from shortenurls.exceptions import URLException
from django.core.urlresolvers import reverse


class UrlModelTest(TestCase):
    def setUp(self):
        self.url1 = Url.create(original_url="testing", shorten_url="1", last_visit_from="me")
        self.url2 = Url.create(original_url="http://testing2", shorten_url="tstng2", last_visit_from="me")
        self.url3 = Url.create(original_url="https://www.football-italia.net/", shorten_url="daaf1", last_visit_from="127.0.0.1")
        self.url = Url.create(save=False, original_url="testing", shorten_url="tstng", last_visit_from="me")
        self.visit1 = UrlVisits.create(url_id=self.url3.id)
        self.visitor = UrlVisitors.create(url_visit=self.visit1)

    def test_url_creation_width_save(self):
        now = timezone.now()
        self.assertLess(self.url1.created, now)

    def test_url_creation_without_save(self):
        urls = Url.fetch(single=False)
        self.assertEqual(len(urls), 3)
        self.assertNotIn(self.url, urls)

    def test_invalid_url_missing_schema(self):
        exception = None
        try:
            Url.check_url_validation(self.url1.original_url)
        except (ValidationError, RequestException) as error:
            exception = error.message
        self.assertIsNotNone(exception)
        self.assertIn("No schema supplied.", exception)

    def test_invalid_url_invalid_url(self):
        exception = None
        try:
            Url.check_url_validation(self.url2.original_url)
        except (ValidationError, RequestException) as error:
            exception = error.message
        self.assertIsNotNone(exception)
        self.assertIn("Failed to establish a new connection", exception.message)

    def test_valid_url(self):
        exception = None
        try:
            Url.check_url_validation(self.url3.original_url)
        except URLException as error:
            exception = error.message
        self.assertEqual(None, exception)

    def test_duplicated_short_url(self):
        exist = Url.short_url_exist(self.url1.shorten_url)
        self.assertTrue(exist)

    def test_not_duplicated_short_url(self):
        exist = Url.short_url_exist("dummy")
        self.assertFalse(exist)

    def test_invalid_short_url_characters(self):
        exception = None
        try:
            Url.check_short_url(self.url1.shorten_url)
        except URLException as error:
            exception = error.message
        self.assertIsNotNone(exception)
        self.assertIn("Invalid short url", exception)

    def test_invalid_short_url_doesnt_exist(self):
        exception = None
        try:
            Url.check_short_url(self.url.shorten_url)
        except URLException as error:
            exception = error.message
        self.assertIsNotNone(exception)
        self.assertIn("not found", exception)

    def test_correct_short_url(self):
        url = Url.check_short_url(self.url3.shorten_url)
        self.assertEqual(url, self.url3)

    def test_json_response(self):
        resp = self.url3.json("testhost:8080", True)
        self.assertEqual(resp['id'], self.url3.id)
        self.assertEqual(resp['shortUrl'], "https://testhost:8080/url/" + self.url3.shorten_url)
        json_params = ['id', 'shortUrl', 'redirectUrl', 'created', 'lastIP']
        for param in json_params:
            self.assertIn(param, resp)

    def test_all_visits_of_url(self):
        visits = Url.get_all_visits(self.url3)
        self.assertIn(self.visit1.json(), visits)

    def test_get_all_visitors_of_url(self):
        visitors = Url.get_all_visitors(self.url3)
        self.assertIn(self.visitor.json(), visitors)

    def test_non_existing_visit_and_visitors(self):
        self.assertEqual(0, len(Url.get_all_visits(12)))
        self.assertEqual(0, len(Url.get_all_visitors(3)))


class UrlVisitsModelTest(TestCase):
    def setUp(self):
        self.url = Url.create(original_url="https://www.football-italia.net/", shorten_url="daaf1", last_visit_from="127.0.0.1")
        self.visit1 = UrlVisits.create(url_id=self.url.id)
        self.visit2 = UrlVisits.create(save=False, url_id=self.url.id)
        self.visit3 = UrlVisits.create(url_id=self.url.id)
        # self.visit3 = UrlVisits.create(url_id=self.url.id)
        self.url_to_test = "https://google.com"

    def test_creating_with_save(self):
        self.assertIn(self.visit1, UrlVisits.fetch(single=False, url_id=self.url.id))

    def test_creating_without_save(self):
        self.assertNotIn(self.visit2, UrlVisits.fetch(single=False))

    def test_single_fetch(self):
        resp = UrlVisits.fetch(url_id=self.url.id, id=self.visit1.id)
        self.assertEqual(resp, self.visit1)

    def test_fetch_non_existing_visit(self):
        exception = None
        try:
            UrlVisits.fetch(url_id=2)
        except URLException as error:
            exception = error.message
        self.assertIsNotNone(exception)
        self.assertIn("not exist", exception.message)

    def test_fetch_all(self):
        exception = None
        resp = []
        try:
            resp = UrlVisits.fetch(single=False)
        except URLException as error:
            exception = error.message
        self.assertIsNone(exception)
        self.assertIn(self.visit1, resp)
        self.assertNotIn(self.visit2, resp)

    def test_mark_visit(self):
        exception = None
        try:
            visit = UrlVisits.mark_visit(self.url.id, "1.2.3.4")
        except Exception as error:
            exception = error.message
        self.assertIsNone(exception)
        self.assertEqual(visit.visits, 1)
        self.assertEqual(visit.last_visit_from, "1.2.3.4")
        self.assertLess(visit.last_visit_at, datetime.datetime.now())

    def test_json_response(self):
        resp = self.visit1.json()
        json_params = ['id', 'visits', 'created', 'lastVisitAt', 'lastIP']
        for param in json_params:
            self.assertIn(param, resp)
        self.assertEqual(resp['id'], self.visit1.id)
        self.assertEqual(resp['lastIP'], "")
        self.assertEqual(resp['lastVisitAt'], None)

    def test_getting_url(self):
        resp = self.client.post(reverse("generate_url"), data=json.dumps({"url": self.url_to_test}), content_type="application/json")
        self.assertIn(resp.status_code, [200, 201])
        self.assertIn("shortenUrl", resp.content.decode("utf-8"))

    def test_wrong_url(self):
        resp = self.client.post(reverse("generate_url"), data=json.dumps({"url":"??"}), content_type="application/json")
        self.assertEqual(resp.status_code, 400)
        self.assertIn("Provided URL is not valid", resp.content.decode("utf-8"))

    def test_empty_url(self):
        resp = self.client.post(reverse("generate_url"), data=json.dumps({"url":""}), content_type="application/json")
        self.assertEqual(resp.status_code, 400)
        self.assertIn("Provided URL is not valid", resp.content.decode("utf-8"))

    def test_redirection(self):
        resp = self.client.post(reverse("generate_url"), data=json.dumps({"url": self.url_to_test}), content_type="application/json")
        self.assertIn(resp.status_code, [200, 201])
        self.assertIn("shortenUrl", resp.content.decode("utf-8"))

        short_url = json.loads(resp.content.decode("utf-8"))['shortenUrl'].split("/url/")[1]
        request = self.client.get(reverse("retrieve_url", kwargs={"url": short_url}))
        self.assertIn(request.status_code, [200, 301])


class UrlVisitorModelTest(TestCase):
    def setUp(self):
        self.url = Url.create(original_url="https://www.football-italia.net/", shorten_url="daaf1", last_visit_from="127.0.0.1")
        self.visit = UrlVisits.create(url_id=self.url.id)
        self.visitor = UrlVisitors.create(url_visit=self.visit, remote_address="1.1.1.1")
        self.visitor2 = UrlVisitors.create(save=False, url_visit=self.visit)
        self.visitor3 = UrlVisitors.create(url_visit=self.visit, remote_address="1.1.1.1")

    def test_creating_with_save(self):
        self.assertIn(self.visitor, UrlVisitors.fetch(single=False, url_visit=self.visit))

    def test_creating_without_save(self):
        self.assertNotIn(self.visitor2, UrlVisitors.fetch(single=False))

    def test_single_fetch(self):
        resp = UrlVisitors.fetch(url_visit=self.visit, id=self.visitor.id)
        self.assertEqual(resp, self.visitor)

    def test_fetch_non_existing_visit(self):
        exception = None
        try:
            UrlVisitors.fetch(url_visit=2)
        except UrlVisitors.DoesNotExist as error:
            exception = error.message
        self.assertIsNotNone(exception)
        self.assertIn("not exist", exception)

    def test_fetch_all(self):
        exception = None
        resp = []
        try:
            resp = UrlVisitors.fetch(single=False)
        except URLException as error:
            exception = error.message
        self.assertIsNone(exception)
        self.assertIn(self.visitor, resp)
        self.assertNotIn(self.visitor2, resp)

    def test_mark_visitor_with_same_remote_address(self):
        meta = {"REMOTE_ADDR": "1.1.1.1", "HTTP_USER_AGENT": "Chrome"}
        exception = None
        try:
            visitor = UrlVisitors.mark_visitor(meta, self.visit.id)
        except Exception as error:
            exception = error.message
        self.assertIsNotNone(exception)
        self.assertIn("More than 1", exception)

    def test_mark_visitor(self):
        meta = {"REMOTE_ADDR": "1.1.1.2", "HTTP_USER_AGENT": "Chrome"}
        exception = None
        try:
            visitor = UrlVisitors.mark_visitor(meta, self.visit.id)
        except Exception as error:
            exception = error.message
        self.assertIsNone(exception)
        self.assertEqual(visitor.remote_address, meta['REMOTE_ADDR'])
        self.assertEqual(visitor.visits, 1)
        self.assertEqual(visitor.url_visit_id, self.visit.id)
        self.assertLess(visitor.last_visit, datetime.datetime.now())
        url = Url.objects.get(urlvisits__urlvisitors=visitor)
        self.assertEqual(url.last_visit_from, visitor.remote_address)

    def test_json(self):
        resp = self.visitor.json()
        json_params = ['id', 'visits', 'firstVisit', 'lastVisit', 'ip', 'userAgent']
        for param in json_params:
            self.assertIn(param, resp)
        self.assertEqual(resp['id'], self.visitor.id)
        self.assertEqual(resp['lastVisit'], None)
        self.assertEqual(resp['lastVisit'], self.visitor.last_visit)

