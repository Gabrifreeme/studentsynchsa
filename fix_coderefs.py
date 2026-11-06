with open('C:\\Users\\chris\\LipSyncStudent\\ACEsi.html','r',encoding='utf-8',errors='ignore') as f:
    content = f.read()
content = content.replace('codeEditor.textContent = ', 'codeEditor.setValue(')
content = content.replace('const c = codeEditor.textContent;', 'const c = codeEditor.getValue();')
content = content.replace('const content = codeEditor.textContent;', 'const content = codeEditor.getValue();')
content = content.replace('const editorCode = codeEditor.textContent.trim();', 'const editorCode = codeEditor.getValue().trim();')
content = content.replace('_savedEditorContent = codeEditor.textContent;', '_savedEditorContent = codeEditor.getValue();')
content = content.replace('codeEditor.innerHTML = highlightDartCode(codeEditor.textContent);', 'codeEditor.getWrapperElement().style.background = "#000000";')
with open('C:\\Users\\chris\\LipSyncStudent\\ACEsi.html','w',encoding='utf-8') as f:
    f.write(content)
print('replaced')
