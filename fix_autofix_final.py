with open('server.py', 'r', encoding='utf-8') as f:
    content = f.read()

# The broken block
old_block = '''      for name, endpoint, api_key, model in providers:
          if not api_key:
              tried.append("%s: no API key" % name)
              continue
          try:
              reply, _ = _chat_one(name, endpoint, api_key, model, msgs, tool_choice="none")
              if reply:
                  fixed = strip_code_fences(reply)
                  return jsonify({"ok": True, "fixed_code": fixed, "provider": name})
          except Exception as e:
              tried.append("%s: %s" % (name, str(e)))'''

# The perfect block
new_block = '''      tried = []
      for name, endpoint, api_key, model in providers:
          if not api_key:
              tried.append("%s: no API key" % name)
              continue
          try:
              # _chat_one returns (reply, tool_calls, error)
              reply, _, _ = _chat_one(name, endpoint, api_key, model, msgs, tool_choice="none")
              if reply:
                  fixed = strip_code_fences(reply)
                  return jsonify({"ok": True, "fixed_code": fixed, "provider": name})
          except Exception as e:
              tried.append("%s: %s" % (name, str(e)))
              
      return jsonify({"ok": False, "error": " | ".join(tried)})'''

content = content.replace(old_block, new_block)

with open('server.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('AutoFix loop fixed!')
