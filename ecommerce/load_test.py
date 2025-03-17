from locust import HttpUser, TaskSet, task, between

class RecommendationLoadTest(TaskSet):
    """Simulates multiple users requesting AI recommendations."""

    @task
    def load_test_recommendations(self):
        """Simulate a user requesting AI recommendations."""
        self.client.get("/cart/")  # Endpoint where recommendations are fetched

class WebsiteUser(HttpUser):
    """Simulates user behavior on the e-commerce platform."""
    tasks = [RecommendationLoadTest]
    wait_time = between(1, 3)  # Users will wait between 1-3 seconds before making another request
