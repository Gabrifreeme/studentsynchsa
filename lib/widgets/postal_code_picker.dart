import 'package:flutter/material.dart';
import '../models/postal_code.dart';
import '../services/postal_code_repository.dart';

/// Show postal code picker modal
/// 
/// Returns the selected postal code or null if cancelled
Future<PostalCode?> showPostalCodePicker({
  required BuildContext context,
  List<PostalCode>? codes,
  PostalCode? initial,
  List<PostalCode> recents = const [],
}) async {
  // Ensure context is valid
  if (!context.mounted) return null;

  final all = codes ?? await PostalCodeRepository.ensureLoaded();

  // Context may have been released while awaiting.
  if (!context.mounted) return null;
  
  // Use showModalBottomSheet with proper return type
  return showModalBottomSheet<PostalCode>(
    context: context,
    isScrollControlled: true,
    useSafeArea: true,
    backgroundColor: Colors.transparent,
    builder: (context) => PostalCodePickerSheet(
      codes: all,
      initial: initial,
      recents: recents,
    ),
  );
}

/// Postal Code Picker Sheet Widget
/// 
/// Displays a searchable list of postal codes with selection capability
class PostalCodePickerSheet extends StatefulWidget {
  final List<PostalCode> codes;
  final PostalCode? initial;
  final List<PostalCode> recents;

  const PostalCodePickerSheet({
    super.key,
    required this.codes,
    this.initial,
    this.recents = const [],
  });

  @override
  State<PostalCodePickerSheet> createState() => _PostalCodePickerSheetState();
}

class _PostalCodePickerSheetState extends State<PostalCodePickerSheet> {
  final TextEditingController _searchController = TextEditingController();
  List<PostalCode> _filteredCodes = [];
  List<PostalCode> _recentCodes = [];
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _initializeData();
  }

  void _initializeData() {
    // Set initial search query if there's an initial postal code
    if (widget.initial != null) {
      _searchController.text = widget.initial!.code;
    }

    // Load recent codes
    // Keep a mutable copy: `widget.recents` can be a const (unmodifiable) list.
    _recentCodes = List<PostalCode>.of(widget.recents);

    // Filter codes based on search
    _filterCodes('');

    setState(() {
      _isLoading = false;
    });
  }

  void _filterCodes(String query) {
    if (query.isEmpty) {
      _filteredCodes = widget.codes;
    } else {
      final lowerQuery = query.toLowerCase();
      _filteredCodes = widget.codes.where((code) {
        return code.code.toLowerCase().contains(lowerQuery) ||
            code.description.toLowerCase().contains(lowerQuery) ||
            (code.region != null && code.region!.toLowerCase().contains(lowerQuery)) ||
            (code.province != null && code.province!.toLowerCase().contains(lowerQuery));
      }).toList();
    }

    // Update UI
    setState(() {});
  }

  /// Select a postal code and return it
  /// 
  /// This is the key fix - use Navigator.pop with the correct context
  void _select(PostalCode code) {
    debugPrint('Selected postal code: ${code.code}');
    
    // Update recent codes
    if (mounted) {
      setState(() {
        _recentCodes.remove(code);
        _recentCodes.insert(0, code);
        if (_recentCodes.length > 10) {
          _recentCodes.removeRange(10, _recentCodes.length);
        }
      });
    }

    // Pop with the selected code
    if (mounted) {
      Navigator.of(context).pop(code);
    }
  }

  /// Cancel and close the picker
  void _cancel() {
    debugPrint('Cancelled postal code selection');
    
    if (mounted) {
      Navigator.of(context).pop(null);
    }
  }

  @override
  void dispose() {
    _searchController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: const BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      child: Column(
        children: [
          // Header
          Container(
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: Theme.of(context).colorScheme.primaryContainer,
              borderRadius: const BorderRadius.vertical(top: Radius.circular(20)),
            ),
            child: Row(
              children: [
                const Icon(Icons.location_city, color: Colors.white),
                const SizedBox(width: 8),
                Text(
                  'Select Postal Code',
                  style: Theme.of(context).textTheme.titleLarge?.copyWith(
                    color: Theme.of(context).colorScheme.onPrimaryContainer,
                    fontWeight: FontWeight.bold,
                  ),
                ),
                const Spacer(),
                // Close button
                IconButton(
                  icon: const Icon(Icons.close, color: Colors.white),
                  onPressed: _cancel,
                  tooltip: 'Close',
                ),
              ],
            ),
          ),

          // Search field
          Padding(
            padding: const EdgeInsets.all(16),
            child: TextField(
              controller: _searchController,
              decoration: InputDecoration(
                hintText: 'Search by code or description...',
                prefixIcon: const Icon(Icons.search),
                suffixIcon: _searchController.text.isNotEmpty
                    ? IconButton(
                        icon: const Icon(Icons.clear),
                        onPressed: () {
                          _searchController.clear();
                          _filterCodes('');
                        },
                      )
                    : null,
                border: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(12),
                ),
                filled: true,
                fillColor: Colors.grey[100],
              ),
              onChanged: _filterCodes,
            ),
          ),

          // Recent codes section
          if (_recentCodes.isNotEmpty) ...[
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 16),
              child: Row(
                children: [
                  const Icon(Icons.history, size: 16, color: Colors.grey),
                  const SizedBox(width: 8),
                  Text(
                    'Recent',
                    style: TextStyle(
                      fontWeight: FontWeight.bold,
                      color: Colors.grey[700],
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 8),
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: _recentCodes.map((code) {
                return Chip(
                  label: Text('${code.code} - ${code.description}'),
                  onDeleted: () {
                    setState(() {
                      _recentCodes.remove(code);
                    });
                  },
                );
              }).toList(),
            ),
            const SizedBox(height: 8),
          ],

          // Loading indicator
          if (_isLoading)
            const Padding(
              padding: EdgeInsets.all(32),
              child: Center(child: CircularProgressIndicator()),
            )
          else
            // Results count
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 16),
              child: Text(
                '${_filteredCodes.length} postal code${_filteredCodes.length != 1 ? 's' : ''} found',
                style: TextStyle(
                  color: Colors.grey[600],
                  fontSize: 14,
                ),
              ),
            ),

          // Postal code list
          Expanded(
            child: _filteredCodes.isEmpty
                ? const Center(
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        Icon(Icons.search_off, size: 64, color: Colors.grey),
                        SizedBox(height: 16),
                        Text(
                          'No postal codes found',
                          style: TextStyle(fontSize: 16, color: Colors.grey),
                        ),
                      ],
                    ),
                  )
                : ListView.builder(
                    padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                    itemCount: _filteredCodes.length,
                    itemBuilder: (context, index) {
                      final code = _filteredCodes[index];
                      return Material(
                        color: Colors.transparent,
                        child: ListTile(
                        leading: Container(
                          padding: const EdgeInsets.all(8),
                          decoration: BoxDecoration(
                            color: Theme.of(context).colorScheme.primaryContainer,
                            borderRadius: BorderRadius.circular(8),
                          ),
                          child: Text(
                            code.code,
                            style: const TextStyle(
                              fontWeight: FontWeight.bold,
                              fontSize: 16,
                            ),
                          ),
                        ),
                        title: Text(
                          code.description,
                          style: const TextStyle(fontWeight: FontWeight.w500),
                        ),
                        subtitle: code.region != null
                            ? Text('${code.region} ${code.province != null ? '• ${code.province}' : ''}')
                            : null,
                        onTap: () => _select(code),
                        tileColor: Colors.grey[50],
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(12),
                          side: BorderSide(color: Colors.grey[200]!),
                        ),
                      ));
                    },
                  ),
          ),

          // Footer with cancel button
          Container(
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: Colors.grey[100],
              borderRadius: const BorderRadius.vertical(top: Radius.circular(20)),
              boxShadow: [
                BoxShadow(
                  color: const Color(0x0D000000),
                  blurRadius: 10,
                  offset: const Offset(0, -2),
                ),
              ],
            ),
            child: SizedBox(
              width: double.infinity,
              child: OutlinedButton(
                onPressed: _cancel,
                style: OutlinedButton.styleFrom(
                  padding: const EdgeInsets.symmetric(vertical: 16),
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(12),
                  ),
                ),
                child: const Text(
                  'Cancel',
                  style: TextStyle(fontSize: 16),
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }
}
