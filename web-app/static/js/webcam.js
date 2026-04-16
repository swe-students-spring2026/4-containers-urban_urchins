(function () {
    var video = document.getElementById("webcam-video");
    var canvas = document.getElementById("webcam-canvas");
    var snapshot = document.getElementById("webcam-snapshot");
    var btnStart = document.getElementById("btn-start-camera");
    var btnCapture = document.getElementById("btn-capture");
    var btnRetake = document.getElementById("btn-retake");
    var btnAnalyze = document.getElementById("btn-analyze");

    var stream = null;

    btnStart.addEventListener("click", function () {
        navigator.mediaDevices
            .getUserMedia({ video: true })
            .then(function (mediaStream) {
                stream = mediaStream;
                video.srcObject = stream;
                video.style.display = "block";
                btnStart.disabled = true;
                btnStart.textContent = "Camera On";
                btnCapture.disabled = false;
            })
            .catch(function () {
                alert("Could not access camera. Please allow camera permissions.");
            });
    });

    btnCapture.addEventListener("click", function () {
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        canvas.getContext("2d").drawImage(video, 0, 0);

        snapshot.src = canvas.toDataURL("image/jpeg");
        snapshot.style.display = "block";
        video.style.display = "none";

        btnCapture.style.display = "none";
        btnRetake.style.display = "inline-block";
        btnAnalyze.style.display = "inline-block";
    });

    btnRetake.addEventListener("click", function () {
        snapshot.style.display = "none";
        video.style.display = "block";
        btnCapture.style.display = "inline-block";
        btnRetake.style.display = "none";
        btnAnalyze.style.display = "none";
    });

    btnAnalyze.addEventListener("click", function() {
        canvas.toBlob(function (blob) {
            var formData = new FormData();
            formData.append("image", blob, "webcam-capture.jpg");

            fetch("/upload", { method: "POST", body: formData })
                .then(function (response) {
                    if (response.redirected) {
                        window.location.href = response.url;
                    }
                })
                .catch(function () {
                    alert("Upload failed. Please try again.");
                });
        }, "image/jpeg");
    });
})();
