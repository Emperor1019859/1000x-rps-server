from locust import HttpUser, between, task


class RPSUser(HttpUser):
    wait_time = between(0.1, 0.5)  # Simulate some delay between requests

    @task
    def get_root(self):
        self.client.get("/")

    @task(3)  # Higher weight for the queue endpoint
    def post_queue(self):
        self.client.post("/queue")
