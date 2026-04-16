(function () {
    var EMOTIONS = ["happy", "sad", "angry", "surprise", "fear", "disgust", "neutral"];
    var chartContainer = document.getElementById("emotion-chart");

    function buildChart(results) {
        var counts = {};
        EMOTIONS.forEach(function (e) { counts[e] = 0; });

        results.forEach(function (r) {
            if (counts.hasOwnProperty(r.dominant_emotion)) {
                counts[r.dominant_emotion]++;
            }
        });

        var max = Math.max.apply(null, EMOTIONS.map(function (e) { return counts[e]; }));

        if (max === 0) {
            chartContainer.innerHTML = '<p class="empty-state">No data yet.</p>';
            return;
        }

        var html = "";
        EMOTIONS.forEach(function (e) {
            var pct = (counts[e] / max) * 100;
            html += '<div class="chart-bar-row">';
            html += '<span class="chart-bar-label">' + e + '</span>';
            html += '<div class="chart-bar-track"><div class="chart-bar-fill ' + e + '" style="width:' + pct + '%"></div></div>';
            html += '<span class="chart-bar-count">' + counts[e] + '</span>';
            html += '</div>';
        });

        chartContainer.innerHTML = html;
    }

    function poll() {
        fetch("/results")
            .then(function (res) { return res.json(); })
            .then(function (data) {
                buildChart(data);
            })
            .catch(function () {});
    }

    poll();
    setInterval(poll, 5000);
})();
