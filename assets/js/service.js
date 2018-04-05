dealiniApp.factory("DealiniFactory", ['$q', '$http', function ($q, $http) {
    let factory = {};
    factory.shortUrl = function(url){
        let urlShorten = $q.defer();
        $http.post("/url/create", {"url": url}).then(function(success){
            urlShorten.resolve(success);
        }, function(error){
            urlShorten.reject(error)
        })
        return urlShorten.promise;
    }
    factory.fetchUrls = function(params){
        let urls = $q.defer()
        let url = "/url/all"+params
        $http.get(url).then(function(success){
            urls.resolve(success)
        }, function(error){
            urls.reject(error)
        })
        return urls.promise;
    };
    factory.getUrlVisits = function(id){
        let visits = $q.defer()
        $http.get("/url/"+id+"/visits").then(function(success){
            visits.resolve(success)
        }, function(error){
            visits.reject(error);
        })
        return visits.promise;
    }
    factory.getUrlVisitors = function(id){
        let visitors = $q.defer()
        $http.get("/url/"+id+"/visitors").then(function(success){
            visitors.resolve(success)
        }, function(error){
            visitors.reject(error);
        })
        return visitors.promise;
    }
    return factory;
}])