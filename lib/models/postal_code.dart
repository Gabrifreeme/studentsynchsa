import 'package:flutter/foundation.dart';

/// A single South African postal code record.
///
/// `code` is the 4-digit postal code (e.g. "0001"), `description` is the
/// suburb/town label, and `region`/`province` carry optional locality context.
/// Records are compared by value (code + description + region + province).
@immutable
class PostalCode {
  const PostalCode({
    required this.code,
    required this.description,
    this.region,
    this.province,
  });

  final String code;
  final String description;
  final String? region;
  final String? province;

  /// Parse a raw ITS string of the form `CODE - description`, or
  /// `CODE - suburb, city` (city becomes [region]).
  factory PostalCode.parse(String raw) {
    final dash = raw.indexOf(' - ');
    if (dash <= 0) {
      final trimmed = raw.trim();
      return PostalCode(code: trimmed, description: trimmed);
    }
    final code = raw.substring(0, dash).trim();
    final rest = raw.substring(dash + 3).trim();
    String? region;
    String description = rest;
    final comma = rest.indexOf(',');
    if (comma >= 0) {
      description = rest.substring(0, comma).trim();
      region = rest.substring(comma + 1).trim();
    }
    return PostalCode(code: code, description: description, region: region);
  }

  /// True when this record carries no postal code (e.g. an empty selection).
  bool get isEmpty => code.isEmpty;

  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      other is PostalCode &&
          other.code == code &&
          other.description == description &&
          other.region == region &&
          other.province == province;

  @override
  int get hashCode => Object.hash(code, description, region, province);

  @override
  String toString() => 'PostalCode($code, $description)';
}
