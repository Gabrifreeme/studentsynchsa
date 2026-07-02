import json
import requests
import litserve as ls
from openai import OpenAI

# IMPORTANT: Replace with your actual OpenAI API key
client = OpenAI(api_key="your-openai-api-key-here")
MODEL = "gpt-3.5-turbo"

WEATHER_TOOL = {
    "type": "function",
    "function": {
        "name": "get_current_weather",
        "description": "Get the current weather in a given location",
        "parameters": {
            "type": "object",
            "properties": {
                "location": {
                    "type": "string",
                    "description": "The city and state, e.g. San Francisco, CA",
                }
            },
            "required": ["location"],
        },
    },
}

SCRAPE_TOOL = {
    "type": "function",
    "function": {
        "name": "scrape_website",
        "description": "Scrape content from a website",
        "parameters": {
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "The URL of the website to scrape",
                }
            },
            "required": ["url"],
        },
    },
}

TOOLS = [WEATHER_TOOL, SCRAPE_TOOL]

def get_current_weather(location: str) -> str:
    print(f"Tool called: get_current_weather({location})")
    return json.dumps({"location": location, "temperature": "25", "conditions": "sunny"})

def scrape_website(url: str) -> str:
    print(f"Tool called: scrape_website({url})")
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        return json.dumps({"url": url, "snippet": resp.text[:500]})
    except Exception as e:
        return json.dumps({"url": url, "error": str(e)})

TOOL_IMPL = {"get_current_weather": get_current_weather, "scrape_website": scrape_website}

class AgentAPI(ls.LitAPI):
    def setup(self, device):
        pass

    def predict(self, request):
        prompt = request.get("prompt", "What's the weather like in London?")
        messages = [{"role": "user", "content": prompt}]
        resp = client.chat.completions.create(model=MODEL, messages=messages, tools=TOOLS)
        msg = resp.choices[0].message

        if msg.tool_calls:
            messages.append(msg)
            for tc in msg.tool_calls:
                fn = tc.function
                args = json.loads(fn.arguments)
                result = TOOL_IMPL[fn.name](**args)
                messages.append({"role": "tool", "tool_call_id": tc.id, "content": result})
            resp = client.chat.completions.create(model=MODEL, messages=messages)
            return resp.choices[0].message.content
        else:
            return msg.content

if __name__ == "__main__":
    api = AgentAPI()
    server = ls.LitServer(api, accelerator="cpu")
    server.run(port=8000)