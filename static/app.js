/**
 * Created by brett on 14/12/2015.
 */

angular.module('app', ['chart.js'])

.controller('PanelController',['$http', '$timeout', '$scope', function($http, $timeout, $scope) {
    var self = this;
    self.updating = true;
    $scope.data = [];
    $scope.times = [];
    $scope.series = ['Target', 'Value'];
    $scope.options = {'animation': false};
    $scope.targetSetter = 1;
    $scope.settingTarget = false;
    $scope.settingText = '';
    self.updatePromise = null;

    self.getUpdate = function() {
        return $http.get('/status')
            .success(function(data) {
                $scope.data = [data.targets, data.values];
                $scope.times = data.times;
            })
            .error(function(err) {
                console.log(err);
            })

    };

    self.periodicUpdate = function() {
        if(self.updating) {
            self.getUpdate()
                .then(function() {
                    $timeout(self.periodicUpdate, 1000);
                });
        } else {
            $timeout(self.periodicUpdate, 1000);
        }
    };

    self.nowSetting = function() {
        $scope.settingTarget = true;
        $scope.settingText = 'Now setting...';
    };

    self.doneSetting = function() {
        $scope.settingTarget = false;
        $scope.settingText = 'Set Target Temp.'
    };

    $scope.setTarget = function() {
        $scope.settingTarget = true;
        $http.post('/target/' + $scope.targetSetter.toString())
            .success(function() {
                self.doneSetting();
            })
            .error(function(err) {
                console.log(err);
                self.doneSetting();
            });
    };

    self.doneSetting();
    self.periodicUpdate();
}]);
