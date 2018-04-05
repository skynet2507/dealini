let dealiniApp = angular.module("DealiniApp", ['ngMaterial', 'ngclipboard'])
dealiniApp.config(function ($httpProvider) {
    $httpProvider.defaults.xsrfCookieName = 'csrftoken';
    $httpProvider.defaults.xsrfHeaderName = 'X-CSRFToken';
})
dealiniApp.controller("HomeController", function ($scope, DealiniFactory, $mdToast) {
    $scope.url = {
        URL: null,
        shortUrl: null
    }
    $scope.disableShort = false;
    $scope.showCustomToast = function (message, error = false, delay = null) {
        $mdToast.show({
            hideDelay: delay,
            position: 'top right',
            controller: 'ToastCtrl',
            templateUrl: '/static/toast/toast-template.html',
            locals: {text: message, error: error}
        });
    };
    $scope.shortUrl = function () {
        if (!$scope.url.URL || $scope.url.URL.length === 0) {
            $scope.showCustomToast("Provide us a valid URL address", true)
            return
        }
        DealiniFactory.shortUrl($scope.url.URL).then(function (success) {
            $scope.url.shortUrl = success.data.shortenUrl;
            $scope.disableShort = true;
            $scope.showCustomToast($scope.url.shortUrl);
        }, function (err) {
            $scope.url.shortUrl = null;
            $scope.showCustomToast(err.data, err);
        })
    }
    $scope.checkUrls = function(){
        window.location.href = "/all"
    }

    $scope.resetResults = function(){
        $scope.url.URL = null;
        $scope.url.shortUrl = null;
    }
})

dealiniApp.controller('ToastCtrl', function ($scope, $mdToast, text, error) {
    $scope.url = text;
    $scope.error = error;
    $scope.close = function () {
        $mdToast.hide()
    }
})

dealiniApp.controller("UrlsController", function ($scope, DealiniFactory, $mdMenu, $filter, $mdDialog, $mdToast) {
    let params = "";

    function initValues() {
        $scope.filter = {
            fromDate: null,
            toDate: null,
            date: null,
            minToDate: null,
            filterRange: false,
            filterDate: false,
            sort: null,
            order: "+",
            visits: null,
            limit: null
        }
        params = "";
    }

    initValues();
    $scope.showCustomToast = function (message, error = false, delay = null) {
        $mdToast.show({
            hideDelay: delay,
            position: 'top right',
            controller: 'ToastCtrl',
            templateUrl: '/static/toast/toast-template-query.html',
            locals: {text: message, error: error}
        });
    };

    $scope.queryUrls = function (params = "") {
        $scope.showCustomToast("Processing...");
        DealiniFactory.fetchUrls(params).then(function (success) {
            $scope.showCustomToast("Done!", false, 1500);
            $scope.urls = success.data;
        }, function (error) {
            $scope.showCustomToast("Something went wrong", true, 1500);
            console.log(error);
        })
    }
    $scope.queryUrls();

    $scope.urlDetails = function (url) {
        $mdDialog.show({
            controller: DialogController,
            templateUrl: '/static/dialog/url.html',
            parent: angular.element(document.body),
            clickOutsideToClose: true,
            locals: {url: url}
        })
            .then(function (answer) {
                $scope.status = 'You said the information was "' + answer + '".';
            }, function () {
                $scope.status = 'You cancelled the dialog.';
            });
    }
    $scope.$watch("filter.fromDate", function (val) {
        $scope.filter.minToDate = val;
        if (val > $scope.filter.toDate) {
            $scope.filter.toDate = val;
        }
    })
    $scope.showDateFilters = function (kind) {
        $scope.filter.filterDate = false;
        $scope.filter.filterRange = false;
        switch (kind) {
            case "range":
                $scope.filter.filterRange = true;
                $scope.filter.date = null;
                $scope.filter.fromDate = new Date();
                $scope.filter.toDate = new Date();
                $scope.filter.minToDate = new Date();
                break;
            case "date":
                $scope.filter.filterDate = true;
                $scope.filter.date = new Date();
                $scope.filter.fromDate = null;
                $scope.filter.toDate = null;
                $scope.filter.minToDate = null;
                break;
        }
    }
    $scope.resetFilters = function () {
        $scope.queryUrls();
        initValues();
    };
    $scope.regenerateUrl = function () {
        params = ""
        if ($scope.filter.fromDate && $scope.filter.toDate) {
            if ($scope.filter.fromDate > $scope.filter.toDate) {
                $scope.showCustomToast("From date must be before due date", true);
                return;
            }
            dateToString($scope.filter.fromDate);
            if (isFirstParam()) {
                params += "?from_date=" + dateToString($scope.filter.fromDate) + "&to_date=" + dateToString($scope.filter.toDate)
            } else {
                params += "&from_date=" + dateToString($scope.filter.fromDate) + "&to_date=" + dateToString($scope.filter.toDate)
            }
        }
        if ($scope.filter.date) {
            if (isFirstParam()) {
                params += "?date=" + dateToString($scope.filter.date)
            } else {
                params += "&date=" + dateToString($scope.filter.date)
            }
        }
        if ($scope.filter.sort) {
            if (isFirstParam()) {
                params += "?order_by=" + ($scope.filter.order !== "+" ? $scope.filter.order : "") + $scope.filter.sort
            } else {
                params += "&order_by=" + ($scope.filter.order !== "+" ? $scope.filter.order : "") + $scope.filter.sort
            }
        }
        if ($scope.filter.limit) {
            if ($scope.filter.limit <= 0) {
                $scope.filter.limit = null;
                return;
            }
            if (isFirstParam()) {
                params += "?results=" + $scope.filter.limit
            } else {
                params += "&results=" + $scope.filter.limit
            }
        }
    }

    $scope.$watch("filter", function () {
        $scope.regenerateUrl();
    }, true)

    function isFirstParam() {
        if (params.indexOf("?") === -1) {
            return true;
        }
        return false;
    }

    function dateToString(date) {
        return $filter("date")(date, "dd/MM/yyyy")
    }

    $scope.applyQuery = function () {
        $scope.queryUrls(params);
    }

    function DialogController($scope, $mdDialog, url, DealiniFactory) {
        $scope.url = url;

        $scope.getVisits = function(){
            DealiniFactory.getUrlVisits($scope.url.id).then(function(success){
                $scope.visits = success.data
            }, function(error){
                console.error(error)
            })
        }
        $scope.getVisitors = function(){
            DealiniFactory.getUrlVisitors($scope.url.id).then(function(success){
                $scope.visitors = success.data;
            }, function(error){
                console.error(error)
            })
        }
        $scope.getVisits();
        $scope.getVisitors();
        $scope.hide = function () {
            $mdDialog.hide();
        };

        $scope.cancel = function () {
            $mdDialog.cancel();
        };
    }

})