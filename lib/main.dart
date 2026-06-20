
import 'package:flutter/material.dart';

void main() {
  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'University UI',
      theme: ThemeData.dark().copyWith(
        scaffoldBackgroundColor: const Color(0xFF0B0B0F), // Main Background Color: Deep black/very dark grey
        cardColor: const Color(0xFF16161E), // Card Background Color
        appBarTheme: const AppBarTheme(
          backgroundColor: Color(0xFF0B0B0F),
          elevation: 0,
        ),
        textTheme: const TextTheme(
          bodyLarge: TextStyle(color: Colors.white),
          bodyMedium: TextStyle(color: Colors.white),
          titleLarge: TextStyle(color: Colors.white),
        ),
      ),
      home: const UniversityListPage(),
    );
  }
}

class University {
  final String name;
  final String abbreviation;
  final String province;
  final String logoColor; // "Blue" or "Red"
  final String badgeType; // "No NBT or fee" or "Fee: R200"

  University({
    required this.name,
    required this.abbreviation,
    required this.province,
    required this.logoColor,
    required this.badgeType,
  });
}

class UniversityListPage extends StatelessWidget {
  const UniversityListPage({super.key});

  final List<University> universities = const [
    University(
      name: "Cape Peninsula University of Technology",
      abbreviation: "CPUT",
      province: "Western Cape",
      logoColor: "Blue",
      badgeType: "No NBT or fee",
    ),
    University(
      name: "Central University of Technology",
      abbreviation: "CUT",
      province: "Free State",
      logoColor: "Red",
      badgeType: "No NBT or fee",
    ),
    University(
      name: "Durban University of Technology",
      abbreviation: "DUT",
      province: "KwaZulu-Natal",
      logoColor: "Red",
      badgeType: "Fee: R200",
    ),
    University(
      name: "Mangosuthu University of Technology",
      abbreviation: "MUT",
      province: "KwaZulu-Natal",
      logoColor: "Red",
      badgeType: "No NBT or fee",
    ),
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text("Universities"),
      ),
      body: ListView.builder(
        padding: const EdgeInsets.all(16.0),
        itemCount: universities.length,
        itemBuilder: (context, index) {
          return Padding(
            padding: const EdgeInsets.only(bottom: 16.0),
            child: UniversityCard(university: universities[index]),
          );
        },
      ),
    );
  }
}

class UniversityCard extends StatelessWidget {
  final University university;

  const UniversityCard({super.key, required this.university});

  @override
  Widget build(BuildContext context) {
    final Color logoBgColor =
        university.logoColor == "Blue" ? Colors.blue : Colors.red;

    final Color badgeBgColor = university.badgeType == "No NBT or fee"
        ? const Color(0xFF0F380F) // Very dark green
        : const Color(0xFF2C0F2C); // Very dark purple
    final Color badgeTextColor = university.badgeType == "No NBT or fee"
        ? const Color(0xFF38EB38) // Bright neon green
        : const Color(0xFFC764C7); // Bright purple

    return Container(
      padding: const EdgeInsets.all(16.0),
      decoration: BoxDecoration(
        color: Theme.of(context).cardColor, // Dark grey for card
        borderRadius: BorderRadius.circular(20.0), // Highly rounded corners
        border: Border.all(
          color: const Color(0xFF2A2A35), // Subtle lighter grey border
          width: 0.8,
        ),
      ),
      child: Row(
        children: [
          // Left Section: Institution Logo
          Container(
            width: 60.0,
            height: 60.0,
            decoration: BoxDecoration(
              color: logoBgColor,
              borderRadius: BorderRadius.circular(15.0), // Squircle-like
            ),
            child: const Icon(
              Icons.apartment, // Building icon
              color: Colors.white,
              size: 30.0,
            ),
          ),
          const SizedBox(width: 16.0), // Spacing

          // Middle Section: Typography & Details
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  "${university.name} (${university.abbreviation})",
                  style: const TextStyle(
                    color: Colors.white,
                    fontWeight: FontWeight.bold,
                    fontSize: 17.0,
                  ),
                ),
                const SizedBox(height: 4.0),
                Row(
                  children: [
                    Icon(
                      Icons.location_on_outlined,
                      color: Colors.grey[400],
                      size: 16.0,
                    ),
                    const SizedBox(width: 4.0),
                    Text(
                      university.province,
                      style: TextStyle(
                        color: Colors.grey[400],
                        fontSize: 13.5,
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 8.0),
                // Tag/Badge
                Container(
                  padding:
                      const EdgeInsets.symmetric(horizontal: 10.0, vertical: 5.0),
                  decoration: BoxDecoration(
                    color: badgeBgColor,
                    borderRadius: BorderRadius.circular(20.0), // Pill-shaped
                  ),
                  child: Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      if (university.badgeType == "Fee: R200") ...[
                        Icon(Icons.description_outlined,
                            color: badgeTextColor, size: 16.0),
                        const SizedBox(width: 4.0),
                      ],
                      Text(
                        university.badgeType,
                        style: TextStyle(
                          color: badgeTextColor,
                          fontSize: 12.0,
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ),

          // Right Section: Action Buttons
          Column(
            children: [
              // Primary Button ("Apply")
              Container(
                decoration: BoxDecoration(
                  borderRadius: BorderRadius.circular(30.0), // Pill-shaped
                  gradient: const LinearGradient(
                    colors: [
                      Color(0xFF8A2BE2), // Light purple
                      Color(0xFF00BFFF), // Bright light blue
                    ],
                    begin: Alignment.topLeft,
                    end: Alignment.bottomRight,
                  ),
                ),
                child: ElevatedButton(
                  onPressed: () {
                    // Handle apply action
                  },
                  style: ElevatedButton.styleFrom(
                    backgroundColor: Colors.transparent, // Make button background transparent to show gradient
                    shadowColor: Colors.transparent,
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(30.0),
                    ),
                    padding: const EdgeInsets.symmetric(horizontal: 20.0, vertical: 12.0),
                  ),
                  child: const Row(
                    children: [
                      Icon(Icons.auto_awesome, color: Colors.white, size: 18.0),
                      SizedBox(width: 8.0),
                      Text(
                        "Apply",
                        style: TextStyle(
                          color: Colors.white,
                          fontWeight: FontWeight.bold,
                          fontSize: 15.0,
                        ),
                      ),
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 8.0),
              // Secondary Button (External Link)
              InkWell(
                onTap: () {
                  // Handle external link action
                },
                child: Container(
                  width: 40.0, // Square shape
                  height: 40.0,
                  decoration: BoxDecoration(
                    color: Colors.grey.withOpacity(0.1), // Transparent or matching card's dark grey
                    borderRadius: BorderRadius.circular(10.0), // Rounded corners
                  ),
                  child: Icon(
                    Icons.open_in_new, // External link icon
                    color: Colors.grey[600],
                    size: 20.0,
                  ),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }
}
