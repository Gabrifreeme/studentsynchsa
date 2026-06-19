import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:studentsyncsa/main.dart';

Widget createTestApp() => const ProviderScope(child: studentsyncsaApp());

void main() {
  testWidgets('App renders without error', (WidgetTester tester) async {
    await tester.pumpWidget(createTestApp());
    await tester.pump();
    expect(find.byType(studentsyncsaApp), findsOneWidget);
  });
}
