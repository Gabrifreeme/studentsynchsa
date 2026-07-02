import 'package:html/parser.dart' as html_parser;
import 'package:html/dom.dart' as dom;

class PortalFormField {
  final String name;
  final String type;
  final String label;
  final String currentValue;
  final List<String> options;
  final bool required;
  final int order;

  PortalFormField({
    required this.name,
    required this.type,
    this.label = '',
    this.currentValue = '',
    this.options = const [],
    this.required = false,
    this.order = 0,
  });
}

class PortalForm {
  final String action;
  final String method;
  final List<PortalFormField> fields;
  final Map<String, String> hiddenFields;

  PortalForm({
    this.action = '',
    this.method = 'POST',
    this.fields = const [],
    this.hiddenFields = const {},
  });
}

PortalForm parsePortalForm(String html, {String? currentUrl}) {
  final doc = html_parser.parse(html);
  final form = doc.querySelector('form');
  if (form == null) {
    return PortalForm();
  }

  final action = form.attributes['action'] ?? '';
  final method = (form.attributes['method'] ?? 'POST').toUpperCase();
  final hiddenFields = <String, String>{};
  final fields = <PortalFormField>[];
  int order = 0;

  void extractLabel(dom.Element input, List<dom.Element> all) {
    // Check for aria-label
    final aria = input.attributes['aria-label'];
    if (aria != null && aria.isNotEmpty) {
      input.attributes['_label'] = aria;
      return;
    }
    // Check for preceding label element
    final id = input.attributes['id'];
    if (id != null) {
      for (final el in all) {
        if (el.localName == 'label' && el.attributes['for'] == id) {
          input.attributes['_label'] = el.text.trim();
          return;
        }
      }
    }
    // Check parent label
    var parent = input.parent;
    while (parent != null) {
      if (parent.localName == 'label') {
        input.attributes['_label'] = parent.text.trim();
        return;
      }
      parent = parent.parent;
    }
    // Check preceding text in same td/div
    final siblings = input.parent?.nodes ?? [];
    final idx = siblings.indexOf(input);
    for (int i = idx - 1; i >= 0; i--) {
      final sib = siblings[i];
      if (sib is dom.Text && sib.text.trim().isNotEmpty) {
        input.attributes['_label'] = sib.text.trim();
        return;
      }
    }
  }

  final all = doc.querySelectorAll('*');
  for (final el in all) {
    final tag = el.localName;
    if (tag == 'input') {
      final t = (el.attributes['type'] ?? 'text').toLowerCase();
      final name = el.attributes['name'] ?? '';
      final value = el.attributes['value'] ?? '';

      if (t == 'hidden') {
        if (name.isNotEmpty) hiddenFields[name] = value;
        continue;
      }
      if (t == 'submit' || t == 'button' || t == 'reset' || t == 'image') {
        continue;
      }

      extractLabel(el, all);

      if (t == 'radio' || t == 'checkbox') {
        // Only add radio groups once
        final existing = fields.indexWhere((f) => f.name == name);
        if (existing == -1) {
          // Collect all options for this radio group
          final options = <String>[];
          for (final r in all) {
            if (r.localName == 'input' &&
                (r.attributes['type'] ?? '').toLowerCase() == t &&
                r.attributes['name'] == name) {
              options.add(r.attributes['value'] ?? '');
            }
          }
          fields.add(PortalFormField(
            name: name,
            type: t,
            label: el.attributes['_label'] ?? name,
            currentValue: value,
            options: options,
            required: el.attributes.containsKey('required'),
            order: order++,
          ));
        }
      } else {
        fields.add(PortalFormField(
          name: name,
          type: t,
          label: el.attributes['_label'] ?? el.attributes['placeholder'] ?? name,
          currentValue: value,
          required: el.attributes.containsKey('required'),
          order: order++,
        ));
      }
    } else if (tag == 'select') {
      final name = el.attributes['name'] ?? '';
      if (name.isEmpty) continue;
      extractLabel(el, all);

      final options = <String>[];
      String selectedValue = '';
      for (final opt in el.querySelectorAll('option')) {
        final v = opt.attributes['value'] ?? opt.text.trim();
        options.add(v);
        if (opt.attributes.containsKey('selected')) {
          selectedValue = v;
        }
      }

      fields.add(PortalFormField(
        name: name,
        type: 'select',
        label: el.attributes['_label'] ?? name,
        currentValue: selectedValue,
        options: options,
        required: el.attributes.containsKey('required'),
        order: order++,
      ));
    } else if (tag == 'textarea') {
      final name = el.attributes['name'] ?? '';
      if (name.isEmpty) continue;
      extractLabel(el, all);
      fields.add(PortalFormField(
        name: name,
        type: 'textarea',
        label: el.attributes['_label'] ?? el.attributes['placeholder'] ?? name,
        currentValue: el.text.trim(),
        required: el.attributes.containsKey('required'),
        order: order++,
      ));
    }
  }

  fields.sort((a, b) => a.order.compareTo(b.order));

  return PortalForm(
    action: action,
    method: method,
    fields: fields,
    hiddenFields: hiddenFields,
  );
}

String dumpForm(PortalForm form) {
  final buf = StringBuffer();
  buf.writeln('Form action: ${form.action}');
  buf.writeln('Form method: ${form.method}');
  buf.writeln('Hidden fields: ${form.hiddenFields.length}');
  for (final e in form.hiddenFields.entries) {
    buf.writeln('  ${e.key} = ${e.value}');
  }
  buf.writeln('\nVisible fields: ${form.fields.length}');
  for (final f in form.fields) {
    buf.writeln('  [$f.type] ${f.label}');
    buf.writeln('    name: ${f.name}');
    buf.writeln('    value: ${f.currentValue}');
    if (f.options.isNotEmpty) {
      buf.writeln('    options: ${f.options.take(5).join(', ')}${f.options.length > 5 ? '...' : ''}');
    }
  }
  return buf.toString();
}
