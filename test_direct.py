from litai import LLM, tool
import requests

@tool
def get_current_weather(location: str):
    """Get the current weather for a given location."""
    print(f"Tool called: get_current_weather({location})")
    return f"The weather in {location} is currently sunny and 25°C."

@tool
def scrape_website(url: str):
    """Scrape content from a given URL."""
    print(f"Tool called: scrape_website({url})")
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        return f"Content snippet from {url}: {resp.text[:500]}"
    except Exception as e:
        return f"Error scraping {url}: {e}"

llm = LLM(model="google/gemini-2.5-flash")

for prompt in [
    "What's the weather like in London?",
    "Tell me about the latest news from https://www.npr.org/",
]:
    print(f"\n=== Prompt: {prompt} ===")
    result = llm.chat(prompt, tools=[get_current_weather, scrape_website], auto_call_tools=True)
    print(f"Response: {result}")
