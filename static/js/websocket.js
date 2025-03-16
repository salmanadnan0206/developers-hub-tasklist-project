console.log("📡 WebSocket script loaded.");

// Store WebSocket instance globally
let socket;
const maxRetries = 5;
let retryCount = 0;

document.addEventListener("DOMContentLoaded", function () {
    connectWebSocket(); // Initialize WebSocket connection

    function connectWebSocket() {
        const userSessionId = document.cookie.split('; ').find(row => row.startsWith('sessionid='))?.split('=')[1];

        if (!userSessionId) {
            console.warn("⚠️ No session ID found. WebSocket authentication might fail.");
        }

        if (socket && socket.readyState === WebSocket.OPEN) return; // Prevent duplicate connections

        socket = new WebSocket(`ws://${window.location.host}/ws/notifications/?sessionid=${userSessionId}`);

        socket.onopen = function () {
            console.log("✅ WebSocket connection established.");
            retryCount = 0;
        };

        socket.onerror = function (error) {
            console.error("❌ WebSocket error:", error);
        };

        socket.onmessage = function (event) {
            try {
                const data = JSON.parse(event.data);
                if (data.message) {
                    console.log("📩 Received WebSocket message:", data);
                    showRealTimeNotification(data.message);
                } else {
                    console.warn("⚠️ Received invalid WebSocket data:", data);
                }
            } catch (e) {
                console.error("❌ Error parsing WebSocket message:", e);
            }
        };

        socket.onclose = function () {
            console.warn("⚠️ WebSocket disconnected. Reconnecting in 3 seconds...");
            if (retryCount < maxRetries) {
                retryCount++;
                setTimeout(connectWebSocket, 3000);
            } else {
                console.error("❌ Max reconnection attempts reached.");
            }
        };
    }

    function showRealTimeNotification(message) {
        let notificationBox = document.getElementById("notificationBox");
        if (!notificationBox) return;

        let notification = document.createElement("div");
        notification.className = "notification";
        notification.innerHTML = `<p>🚀 ${message} <small>${new Date().toLocaleTimeString()}</small></p>`;

        notificationBox.appendChild(notification);

        // Remove after 5 seconds
        setTimeout(() => {
            if (notificationBox.contains(notification)) {
                notificationBox.removeChild(notification);
            }
        }, 5000);
    }

    // Fetch notifications periodically
    async function fetchNotifications() {
        try {
            const response = await fetch("/json_notifications/", {
                method: "GET",
                headers: { "Content-Type": "application/json" },
                credentials: "include"
            });

            if (!response.ok) {
                console.error(`❌ Failed to fetch notifications (HTTP ${response.status}):`, await response.text());
                return;
            }

            const data = await response.json();
            if (!data.notifications) throw new Error("Invalid JSON format");

            displayStoredNotifications(data.notifications);
        } catch (error) {
            console.error("❌ Error fetching notifications:", error.message);
        }
    }

    function displayStoredNotifications(notifications) {
        let notificationBox = document.getElementById("notificationBox");
        if (!notificationBox) return;

        notificationBox.innerHTML = ""; // Clear previous notifications

        notifications.forEach(notification => {
            let notificationElement = document.createElement("div");
            notificationElement.classList.add("notification");
            notificationElement.innerHTML = `<p>🚀 ${notification.message} <small>${notification.timestamp}</small></p>`;

            notificationBox.appendChild(notificationElement);

            // Remove after 5 seconds
            setTimeout(() => {
                if (notificationBox.contains(notificationElement)) {
                    notificationBox.removeChild(notificationElement);
                }
            }, 5000);
        });
    }

    fetchNotifications();
    setInterval(fetchNotifications, 10000);
});
