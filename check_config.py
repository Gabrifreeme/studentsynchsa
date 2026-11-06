import yaml
c = yaml.safe_load(open('ace_config.yaml', 'r', encoding='utf-8'))
print('default_context:', c['global']['default_context'])
print('contexts:', list(c['contexts'].keys()))
print('lipsyncstudent name:', c['contexts']['lipsyncstudent']['name'])
