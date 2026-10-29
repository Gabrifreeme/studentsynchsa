$js = @"
const field = document.getElementById('oapCitizenType');
if (field) {
  field.value = 'Y';
  field.dispatchEvent(new Event('change', {bubbles:true}));
  field.dispatchEvent(new Event('input', {bubbles:true}));
  field.dispatchEvent(new Event('blur', {bubbles:true}));
  const descField = document.getElementById('oapCitizenType_desc');
  if (descField) descField.value = 'Yes';
  if (field.onchange) field.onchange.call(field);
}
"@

$body = @{
    javascript = $js
    target_url = "https://univenierp01.univen.ac.za"
} | ConvertTo-Json -Depth 3

Invoke-RestMethod -Uri "http://localhost:5000/js_inject" -Method Post -ContentType "application/json" -Body $body