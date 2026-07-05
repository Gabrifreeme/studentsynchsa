import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:studentsyncsa/data/datasources/local/hive_database.dart';

enum SidebarPosition { left, right }

final sidebarProvider = StateNotifierProvider<SidebarNotifier, SidebarPosition>((ref) {
  return SidebarNotifier();
});

class SidebarNotifier extends StateNotifier<SidebarPosition> {
  SidebarNotifier() : super(SidebarPosition.right) {
    _load();
  }

  void _load() {
    final saved = HiveDatabase.settings.get('sidebarPosition');
    if (saved == 'left') {
      state = SidebarPosition.left;
    } else {
      state = SidebarPosition.right;
    }
  }

  void setPosition(SidebarPosition position) {
    state = position;
    HiveDatabase.settings.put('sidebarPosition', position.name);
  }

  void toggle() {
    setPosition(state == SidebarPosition.left ? SidebarPosition.right : SidebarPosition.left);
  }
}
