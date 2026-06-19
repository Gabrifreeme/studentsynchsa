import 'package:flutter/material.dart';
import 'package:studentsyncsa/core/constants/app_constants.dart';
import 'package:studentsyncsa/core/theme/app_theme.dart';
import 'package:studentsyncsa/domain/models/student_profile.dart';
import 'package:studentsyncsa/presentation/widgets/common_widgets.dart';

class ApsCalculatorScreen extends StatefulWidget {
  const ApsCalculatorScreen({super.key});

  @override
  State<ApsCalculatorScreen> createState() => _ApsCalculatorScreenState();
}

class _ApsCalculatorScreenState extends State<ApsCalculatorScreen> {
  final List<_SubjectEntry> _subjects = [];
  bool _lifeOrientationIncluded = false;

  int get _aps => _calculateAps();

  int _calculateAps() {
    int total = 0;
    int count = 0;
    for (final s in _subjects) {
      if (s.mark > 0 && (s.isLifeOrientation ? _lifeOrientationIncluded : true)) {
        total += _percentageToAps(s.mark);
        count++;
      }
    }
    // APS is best 6 subjects excluding Life Orientation unless selected
    return total;
  }

  int _percentageToAps(double percentage) {
    if (percentage >= 80) return 7;
    if (percentage >= 70) return 6;
    if (percentage >= 60) return 5;
    if (percentage >= 50) return 4;
    if (percentage >= 40) return 3;
    if (percentage >= 30) return 2;
    return 1;
  }

  int _subjectsCounted() {
    return _lifeOrientationIncluded
        ? _subjects.where((s) => s.mark > 0).length
        : _subjects.where((s) => s.mark > 0 && !s.isLifeOrientation).length;
  }

  @override
  Widget build(BuildContext context) {
    return GradientBackground(
      child: Scaffold(
        backgroundColor: Colors.transparent,
        appBar: AppBar(title: const Text('APS Calculator')),
        body: Column(
          children: [
            // APS Score Display
            Container(
              margin: const EdgeInsets.all(16),
              padding: const EdgeInsets.all(24),
              decoration: BoxDecoration(
                gradient: const LinearGradient(
                  colors: [AppColors.primary, AppColors.primaryDark],
                  begin: Alignment.topLeft,
                  end: Alignment.bottomRight,
                ),
                borderRadius: BorderRadius.circular(20),
              ),
              child: Column(
                children: [
                  const Text('Your APS Score',
                      style: TextStyle(color: Colors.white70, fontSize: 14)),
                  const SizedBox(height: 8),
                  Text(
                    '$_aps',
                    style: const TextStyle(
                      color: Colors.white,
                      fontSize: 56,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    'Based on ${_subjectsCounted()} subjects',
                    style: const TextStyle(color: Colors.white60, fontSize: 12),
                  ),
                  const SizedBox(height: 12),
                  _apsBars(),
                ],
              ),
            ),

            // Subjects list
            Expanded(
              child: ListView.builder(
                padding: const EdgeInsets.symmetric(horizontal: 16),
                itemCount: _subjects.length + 1,
                itemBuilder: (_, i) {
                  if (i == _subjects.length) {
                    return Padding(
                      padding: const EdgeInsets.symmetric(vertical: 16),
                      child: OutlinedButton.icon(
                        onPressed: () {
                          setState(() => _subjects.add(_SubjectEntry()));
                        },
                        icon: const Icon(Icons.add, size: 18),
                        label: const Text('Add Subject'),
                      ),
                    );
                  }
                  return _buildSubjectRow(i);
                },
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _apsBars() {
    final rating = _aps ~/ 7;
    final maxBars = 6;
    return Row(
      mainAxisAlignment: MainAxisAlignment.center,
      children: List.generate(maxBars, (i) {
        final filled = i < rating;
        return Container(
          width: 8,
          height: 20,
          margin: const EdgeInsets.symmetric(horizontal: 2),
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(4),
            color: filled ? Colors.white : Colors.white24,
          ),
        );
      }),
    );
  }

  Widget _buildSubjectRow(int index) {
    final subject = _subjects[index];
    return Padding(
      padding: const EdgeInsets.only(bottom: 8),
      child: AppCard(
        child: Row(
          children: [
            Expanded(
              flex: 3,
              child: DropdownButtonFormField<String>(
                value: subject.name.isEmpty ? null : subject.name,
                hint: const Text('Subject', style: TextStyle(fontSize: 13)),
                items: AppConstants.subjects
                    .map((s) => DropdownMenuItem(
                        value: s,
                        child: Text(s, style: const TextStyle(fontSize: 12))))
                    .toList(),
                onChanged: (v) {
                  if (v != null) {
                    setState(() {
                      subject.name = v;
                      subject.isLifeOrientation =
                          v.toLowerCase().contains('life orientation');
                    });
                  }
                },
              ),
            ),
            const SizedBox(width: 8),
            SizedBox(
              width: 60,
              child: TextFormField(
                initialValue: subject.mark == 0 ? '' : subject.mark.toInt().toString(),
                keyboardType: TextInputType.number,
                decoration: const InputDecoration(
                  labelText: '%',
                  contentPadding: EdgeInsets.symmetric(horizontal: 8, vertical: 10),
                ),
                onChanged: (v) {
                  setState(() => subject.mark = double.tryParse(v) ?? 0);
                },
              ),
            ),
            const SizedBox(width: 4),
            Text(
              '${_percentageToAps(subject.mark)}',
              style: const TextStyle(
                color: AppColors.primaryLight,
                fontWeight: FontWeight.bold,
                fontSize: 16,
              ),
            ),
            IconButton(
              icon: const Icon(Icons.remove_circle_outline,
                  color: AppColors.error, size: 20),
              onPressed: () => setState(() => _subjects.removeAt(index)),
            ),
          ],
        ),
      ),
    );
  }
}

class _SubjectEntry {
  String name = '';
  double mark = 0;
  bool isLifeOrientation = false;
}
