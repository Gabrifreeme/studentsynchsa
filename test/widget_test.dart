import 'package:flutter_test/flutter_test.dart';
import 'package:studentsynchsa/main.dart';

void main() {
  testWidgets('App renders without error', (WidgetTester tester) async {
    await tester.pumpWidget(const StudentSynchSAApp());
    await tester.pump();
    expect(find.byType(StudentSynchSAApp), findsOneWidget);
  });
}