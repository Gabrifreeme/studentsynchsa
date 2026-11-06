# ACEsi Research Tool Command Examples

## Web Search Command:
CALL: web_search {"query": "real estate rental agencies Sandton Johannesburg 28.014870 -26.111097 10km radius", "max_results": 10}

## Webfetch Command (example from first result):
CALL: webfetch {"url": "https://www.etchellsandyoung.co.za/rental-agents-in-randburg-and-sandton", "format": "markdown"}

## Write File Command:
CALL: write_file {"path": "notes/rental_agencies_sandton_10km.md", "content": "FORMATTED_RESEARCH_HERE"}

## JSON Format (alternative):
{
  "command": "web_search",
  "args": {
    "query": "real estate rental agencies Sandton Johannesburg 28.014870 -26.111097 10km radius",
    "max_results": 10
  }
}

## Usage Pattern for Your Task

ACEsi, research and list 10 real-estate rental agencies within a 10 km radius of -26.111097, 28.014870. For each one provide:

#1: Start with web search
CALL: web_search {"query": "real estate rental agencies Sandton Johannesburg 28.014870 -26.111097 10km radius", "max_results": 10}

#2-11: For each agency URL from search results, fetch full content
CALL: webfetch {"url": "https://www.etchellsandyoung.co.za/rental-agents-in-randburg-and-sandton", "format": "markdown"}
CALL: webfetch {"url": "http://www.letcor.co.za/", "format": "markdown"}
... (repeat for all 10 agencies) ...

#12: Compile and save results
CALL: write_file {"path": "notes/rental_agencies_sandton_10km.md", "content": "FORMATTED_RESEARCH_HERE"}

#13: Final summary
FINAL: Found 10 rental agencies... (your summary here)

## Important Notes
- Always webfetch source pages after web_search to get full contact details
- Each tool call takes one turn - emit ONE call per turn
- webfetch requires proper URL with http:// or https://
- Format the research results clearly before writing to file