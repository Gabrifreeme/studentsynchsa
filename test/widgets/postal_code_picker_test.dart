import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:studentsyncsa/models/postal_code.dart';
import 'package:studentsyncsa/services/postal_code_repository.dart';
import 'package:studentsyncsa/widgets/postal_code_picker.dart';

void main() {
  testWidgets('selection returns the tapped postal code', (tester) async {
    await PostalCodeRepository.ensureLoaded();
    final codes = PostalCodeRepository.load();
    expect(codes, isNotEmpty);

    PostalCode? result;
    final navigatorKey = GlobalKey<NavigatorState>();
    await tester.pumpWidget(MaterialApp(
      navigatorKey: navigatorKey,
      home: Scaffold(
        body: Center(
          child: ElevatedButton(
            onPressed: () async {
              result = await showPostalCodePicker(
                context: navigatorKey.currentContext!,
              );
            },
            child: const Text('open'),
          ),
        ),
      ),
    ));

    await tester.tap(find.text('open'));
    await tester.pumpAndSettle();

    final target = codes.first;
    await tester.tap(find.text(target.code).first);
    await tester.pumpAndSettle();

    expect(result, isNotNull);
    expect(result?.code, target.code);
  });

  testWidgets('cancel returns null', (tester) async {
    await PostalCodeRepository.ensureLoaded();

    PostalCode? result;
    final navigatorKey = GlobalKey<NavigatorState>();
    await tester.pumpWidget(MaterialApp(
      navigatorKey: navigatorKey,
      home: Scaffold(
        body: Center(
          child: ElevatedButton(
            onPressed: () async {
              result = await showPostalCodePicker(
                context: navigatorKey.currentContext!,
              );
            },
            child: const Text('open'),
          ),
        ),
      ),
    ));

    await tester.tap(find.text('open'));
    await tester.pumpAndSettle();

    await tester.tap(find.text('Cancel'));
    await tester.pumpAndSettle();

    expect(result, isNull);
  });
}
