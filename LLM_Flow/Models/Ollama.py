import requests

class OllamaModel:
    def __init__(self, host = "http://127.0.0.1:11434"):
        self.host = host

    def run(self, model :str, prompt :str) -> str:
        response = requests.post(
            f"{self.host}/api/generate",
            json={
                "model": model,
                "prompt": prompt,
                "stream": False
            },
            timeout=180
        )

        response.raise_for_status()
        
        return response.json()["response"]
