import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'dart:convert';

class QuickCopyScreen extends StatefulWidget {
  final String? profileJson;
  final String portalUrl;

  const QuickCopyScreen({this.profileJson, required this.portalUrl, super.key});

  @override
  State<QuickCopyScreen> createState() => _QuickCopyScreenState();
}

class _QuickCopyScreenState extends State<QuickCopyScreen> {
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      FocusScope.of(context).unfocus();
    });
  }

  Map<String, dynamic> get profile {
    try {
      var jsonStr = widget.profileJson;
      if (jsonStr == null || jsonStr.isEmpty) return {};
      return Map<String, dynamic>.from(jsonDecode(jsonStr));
    } catch (_) {
      return {};
    }
  }

  static const _fields = [
    'lastName', 'firstName', 'idNumber', 'email', 'phone', 'dateOfBirth',
    'initials', 'title', 'nationality', 'homeLanguage', 'province', 'postalCode'
  ];

  static const _labels = {
    'lastName': 'Surname',
    'firstName': 'First Name',
    'idNumber': 'ID Number',
    'email': 'Email',
    'phone': 'Phone',
    'dateOfBirth': 'Date of Birth',
    'initials': 'Initials',
    'title': 'Title',
    'nationality': 'Nationality',
    'homeLanguage': 'Home Language',
    'province': 'Province',
    'postalCode': 'Postal Code',
  };

  void _copy(String value) {
    Clipboard.setData(ClipboardData(text: value));
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('My Profile — Quick Copy')),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          ElevatedButton.icon(
            icon: const Icon(Icons.auto_fix_high),
            label: const Text('Enable Autofill Service'),
            style: ElevatedButton.styleFrom(padding: const EdgeInsets.symmetric(vertical: 16, horizontal: 24), backgroundColor: Colors.amber),
            onPressed: () {
              const platform = MethodChannel('lipsync.autofill');
              platform.invokeMethod('openAutofillSettings');
            },
          ),
          const SizedBox(height: 8),
          ElevatedButton.icon(
            icon: const Icon(Icons.public),
            label: const Text('Open Online Application'),
            style: ElevatedButton.styleFrom(padding: const EdgeInsets.symmetric(vertical: 16, horizontal: 24)),
            onPressed: () => ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Opening: ${widget.portalUrl}'))),
          ),
          const SizedBox(height: 16),
          ..._fields.map((k) {
            final label = _labels[k] ?? k;
            final value = (profile[k] ?? '').toString();
            return Card(
              child: ListTile(
                title: Text(label, style: const TextStyle(fontWeight: FontWeight.bold)),
                subtitle: Text(value.isEmpty ? '(empty)' : value),
                trailing: IconButton(
                  icon: const Icon(Icons.content_copy, color: Colors.green),
                  tooltip: 'Copy $label',
                  onPressed: value.isEmpty ? null : () {
                    _copy(value);
                    ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Copied $label')));
                  },
                ),
              ),
            );
          }),
        ],
      ),
    );
  }
}
