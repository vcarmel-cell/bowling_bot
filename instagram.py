import os
import time
import requests

GRAPH_API_VERSION = "v19.0"
BASE_URL = f"https://graph.facebook.com/{GRAPH_API_VERSION}"


class InstagramAPI:
    def __init__(self):
        self.token = os.environ["META_ACCESS_TOKEN"]
        self.user_id = os.environ["INSTAGRAM_ACCOUNT_ID"]

    def _create_container(self, image_url: str, caption: str) -> str:
        resp = requests.post(
            f"{BASE_URL}/{self.user_id}/media",
            data={
                "image_url": image_url,
                "caption": caption,
                "access_token": self.token,
            },
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()["id"]

    def _wait_for_container(self, container_id: str, retries: int = 10) -> None:
        for _ in range(retries):
            resp = requests.get(
                f"{BASE_URL}/{container_id}",
                params={"fields": "status_code", "access_token": self.token},
                timeout=15,
            )
            resp.raise_for_status()
            status = resp.json().get("status_code")
            if status == "FINISHED":
                return
            if status == "ERROR":
                raise RuntimeError(f"Media container failed: {resp.json()}")
            time.sleep(5)
        raise TimeoutError("Media container did not finish processing in time")

    def _publish_container(self, container_id: str) -> str:
        resp = requests.post(
            f"{BASE_URL}/{self.user_id}/media_publish",
            data={"creation_id": container_id, "access_token": self.token},
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()["id"]

    def post(self, image_url: str, caption: str) -> str:
        container_id = self._create_container(image_url, caption)
        self._wait_for_container(container_id)
        post_id = self._publish_container(container_id)
        return post_id
