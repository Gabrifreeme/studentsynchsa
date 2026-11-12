import 'package:flutter_inappwebview/flutter_inappwebview.dart';
import 'package:flutter/material.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:lipsyncstudent/core/router/app_router.dart';
import 'package:lipsyncstudent/core/theme/app_theme.dart';
import 'package:lipsyncstudent/data/datasources/local/hive_database.dart';
import 'package:lipsyncstudent/services/ai_service.dart';
import 'package:lipsyncstudent/services/notification_service.dart';
import 'package:lipsyncstudent/services/sync_service.dart';


void main() async {
  // Enable WebView remote debugging for Android
  WidgetsFlutterBinding.ensureInitialized();
  // Only set WebView debugging on mobile platforms
  if (!kIsWeb) {
    await InAppWebViewController.setWebContentsDebuggingEnabled(true);
  }
  
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
      child: LipSyncStudentApp(),
    ),
  );
}

class LipSyncStudentApp extends ConsumerWidget {
  const LipSyncStudentApp({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return MaterialApp.router(
      title: 'LipSyncStudent',
      debugShowCheckedModeBanner: false,
      theme: AppTheme.dark,
      scrollBehavior: const NoScrollbarBehavior(),
      routerConfig: appRouter,
    );
  }
}
