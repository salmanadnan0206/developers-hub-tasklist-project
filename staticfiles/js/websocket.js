const socket = new WebSocket("ws://" + window.location.host + "/ws/notifications/");

socket.onmessage = function(event) {
    const data = JSON.parse(event.data);
    displayNotification(data.message, data.timestamp);
};

function displayNotification(message, timestamp) {
    const notificationContainer = document.getElementById("notification-container");
    const notificationElement = document.createElement("div");
    notificationElement.classList.add("notification");
    notificationElement.innerHTML = `<strong>${timestamp}</strong>: ${message}`;
    notificationContainer.appendChild(notificationElement);

    // Remove after 5 seconds
    setTimeout(() => {
        notificationElement.remove();
    }, 5000);
}
