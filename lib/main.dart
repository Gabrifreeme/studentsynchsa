import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:studentsynchsa/core/router/app_router.dart';
import 'package:studentsynchsa/core/theme/app_theme.dart';
import 'package:studentsynchsa/data/datasources/local/hive_database.dart';
import 'package:studentsynchsa/services/ai_service.dart';
import 'package:studentsynchsa/services/notification_service.dart';
import 'package:studentsynchsa/services/sync_service.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  SystemChrome.setPreferredOrientations([
    DeviceOrientation.portraitUp,
    DeviceOrientation.portraitDown,
  ]);
  SystemChrome.setSystemUIOverlayStyle(
    const SystemUiOverlayStyle(
      statusBarColor: Colors.transparent,
      statusBarIconBrightness: Brightness.light,
    ),
  );

  await HiveDatabase.init();
  await NotificationService.init();
  SyncService.init();
  AiService.warmUp();

  runApp(
    const ProviderScope(
      child: StudentSynchSAApp(),
    ),
  );
}

class StudentSynchSAApp extends ConsumerWidget {
  const StudentSynchSAApp({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return MaterialApp.router(
      title: 'StudentSynchSA',
      debugShowCheckedModeBanner: false,
      theme: AppTheme.dark,
      scrollBehavior: const NoScrollbarBehavior(),
      routerConfig: appRouter,
    );
  }
}
