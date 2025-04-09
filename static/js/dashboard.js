// Function to fetch and update recent activity
async function updateRecentActivity() {
  try {
    const response = await fetch("/api/recent-activity");
    const activities = await response.json();

    const activityList = document.getElementById("activity-list");
    activityList.innerHTML = activities
      .map(
        (activity) => `
            <div class="activity-item">
                <i class="fas ${activity.icon} activity-icon"></i>
                <span>${activity.description}</span>
                <span class="activity-time">${activity.time}</span>
            </div>`
      )
      .join("");
  } catch (error) {
    console.error("Error fetching recent activity:", error);
  }
}
