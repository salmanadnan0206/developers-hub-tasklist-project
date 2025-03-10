console.log("📡 WebSocket script loaded.");

// Store WebSocket instance globally
let socket;
const maxRetries = 5;
let retryCount = 0;

document.addEventListener("DOMContentLoaded", function () {
    connectWebSocket(); // Initialize WebSocket connection

    // Function to establish WebSocket connection
    function connectWebSocket() {
        const userSessionId = document.cookie.split('; ').find(row => row.startsWith('sessionid='))?.split('=')[1];

        if (!userSessionId) {
            console.warn("⚠️ No session ID found. WebSocket authentication might fail.");
        }

        if (socket && socket.readyState === WebSocket.OPEN) return; // Prevent duplicate connections

        socket = new WebSocket(`ws://${window.location.host}/ws/notifications/?sessionid=${userSessionId}`);

        socket.onopen = function () {
            console.log("✅ WebSocket connection established.");
            retryCount = 0; // Reset retry count upon successful connection
        };

        socket.onerror = function (error) {
            console.error("❌ WebSocket error:", error);
        };

        socket.onmessage = function (event) {
            const data = JSON.parse(event.data);
            console.log("📩 Received WebSocket message:", data);
            showRealTimeNotification(data.message);
        };

        socket.onclose = function (event) {
            console.warn("⚠️ WebSocket disconnected. Reconnecting in 3 seconds...");
            if (retryCount < maxRetries) {
                retryCount++;
                setTimeout(connectWebSocket, 3000);
            } else {
                console.error("❌ Max reconnection attempts reached. Please check your server.");
            }
        };
    }

    // Function to display notifications in real-time
    function showRealTimeNotification(message) {
        let notificationBox = document.getElementById("notificationBox");

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

    // Fetch notifications periodically to ensure updates
    async function fetchNotifications() {
        try {
            const response = await fetch("/notifications/", {
                method: "GET",
                headers: { "Content-Type": "application/json" },
                credentials: "include"
            });

            if (!response.ok) {
                console.error("❌ Failed to fetch notifications:", response.status);
                return;
            }

            const data = await response.json();
            displayStoredNotifications(data.notifications);
        } catch (error) {
            console.error("❌ Error fetching notifications:", error);
        }
    }

    // Function to display stored notifications from API
    function displayStoredNotifications(notifications) {
        let notificationBox = document.getElementById("notificationBox");
        notificationBox.innerHTML = ""; // Clear previous notifications

        const now = new Date().getTime();

        notifications.forEach(notification => {
            const notificationTime = new Date(notification.timestamp).getTime();
            const elapsedSeconds = (now - notificationTime) / 1000;

            if (elapsedSeconds > 10) return; // Ignore old notifications

            let notificationElement = document.createElement("div");
            notificationElement.classList.add("notification");
            notificationElement.innerHTML = `<p>🚀 ${notification.message} <small>${notification.timestamp}</small></p>`;

            notificationBox.appendChild(notificationElement);

            // Automatically remove after 5 seconds
            setTimeout(() => {
                if (notificationBox.contains(notificationElement)) {
                    notificationBox.removeChild(notificationElement);
                }
            }, 5000);
        });
    }

    // Fetch notifications on page load
    fetchNotifications();

    // Refresh notifications every 10 seconds
    setInterval(fetchNotifications, 10000);
});
