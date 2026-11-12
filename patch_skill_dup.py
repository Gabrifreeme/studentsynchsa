import io, re
path = r"C:\Users\chris\LipSyncStudent\ACEsi.html"
with io.open(path, "r", encoding="utf-8", newline="") as f:
    html = f.read()

# Find the setSkill function body around the /memory/set call and inject the duplicate check
old_block = """        var fullKey = k.startsWith("skills.") ? k : "skills." + k;

        try {

          await fetch("http://127.0.0.1:5000/memory/set", {"""

new_block = """        var fullKey = k.startsWith("skills.") ? k : "skills." + k;

        try {

          // Duplicate check - verify the skill doesn't already exist
          var checkResp = await fetch("http://127.0.0.1:5000/memory/get?key=" + encodeURIComponent(fullKey));
          if (checkResp.ok) {
            var checkData = await checkResp.json();
            if (checkData && checkData.value !== undefined && checkData.value !== null) {
              if (window.showAceToast) window.showAceToast("Skill already exists: " + fullKey, 'error', 4000);
              return;
            }
          }

          await fetch("http://127.0.0.1:5000/memory/set", {"""

if old_block in html:
    html = html.replace(old_block, new_block)
    print("FRONTEND: Added duplicate check to setSkill()")
else:
    print("WARNING: Could not find setSkill block")

with io.open(path, "w", encoding="utf-8", newline="") as f:
    f.write(html)
print("PATCH COMPLETE")
