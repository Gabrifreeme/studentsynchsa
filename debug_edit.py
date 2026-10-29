path = "C:\\Users\\chris\\LipSyncStudent\\ACESi.html"
with open(path, "r", encoding="utf-8") as f:
    content = f.read()

# Find the exact start of the chat input flex div
start = content.find('display:flex;gap:8px;padding:8px;border-top:1px solid #ff9d00;background:#000;">')
print("Start index:", start)

# Find the end of this div (the closing </div> that matches)
# We need to find the </div> that comes after the chat-file input
end_marker = '</div>'
# Find the first </div> after the chat-file input line
chat_file_end = content.find("this.files[0].name + '</div>'>", start)
after_input = content.find('\n', chat_file_end)
next_newline = content.find('\n', after_input + 1)
# The closing </div> should be on the next line
div_close = content.find('</div>', after_input)
print("Div close index:", div_close)
end = div_close + len('</div>')

old = content[start:end]
print("OLD STRING:")
print(repr(old))
print("---")
print(old)
