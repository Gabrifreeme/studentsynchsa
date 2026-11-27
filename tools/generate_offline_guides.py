import os

OUT = r'C:\Users\gabri\Documents\LibSyncStudent\assets\offline\guides'
os.makedirs(OUT, exist_ok=True)

# id: (short, full name, province, town/campus note, website, deadline, fees, kind)
U = {
 'uchenn': ("UCT", "University of Cape Town", "Western Cape", "Rondebosch, Cape Town", "https://www.uct.ac.za", "Opened 1 April 2026; undergraduate applications closed 31 July 2026. No late applications. Residence applications also closed 31 July 2026. Postgraduate applications close 31 October 2026.", "First-year tuition roughly R62,340 to R113,510 depending on faculty (2026 local-student figures). Astronomy, engineering and medicine are at the higher end.", "Traditional university"),
 'wits': ("Wits", "University of the Witwatersrand", "Gauteng", "Braamfontein & East Campus, Johannesburg", "https://www.wits.ac.za", "Health Sciences, Architecture, Audiology, Speech-Language Pathology and Film & TV closed 30 June 2026. All other undergraduate programmes and residence applications closed 30 September 2026. No late applications.", "Average first-year tuition about R47,930 to R83,760 (2026), charged per course or module.", "Traditional university"),
 'su': ("SUN", "Stellenbosch University", "Western Cape", "Stellenbosch, with satellite campuses", "https://www.su.ac.za", "2027 undergraduate applications closed 31 July 2026. No late applications. Residence applications closed on the same date.", "First-year tuition roughly R52,900 to R87,950 (2026), depending on faculty.", "Traditional university"),
 'up': ("UP", "University of Pretoria", "Gauteng", "Hatfield, Pretoria (multiple campuses)", "https://www.up.ac.za", "Applications opened 1 April 2026 and closed 30 June 2026 — the earliest major closing date. Veterinary Science closed 31 May 2026. No late applications.", "Estimated first-year tuition R30,000 to R98,000 depending on faculty (2026). Initial fee payable before registration.", "Traditional university"),
 'ukzn': ("UKZN", "University of KwaZulu-Natal", "KwaZulu-Natal", "Pietermaritzburg, Durban, Westville, Edgewood", "https://ukzn.ac.za", "Undergraduate applications via CAO closed 30 September 2026. Medicine (MBChB) closed 30 June 2026.", "Approximate full-time first-year fees R47,854 to R68,224 (2026); engineering around R64,167 to R64,910. Residence R48,896 to R59,168 per year.", "Traditional university"),
 'nwu': ("NWU", "North-West University", "North West", "Potchefstroom, Mahikeng, Vanderbijlpark", "https://www.nwu.ac.za", "Applications opened 1 June 2026 and closed 31 August 2026. Selection courses closed 30 June 2026. Postgraduate applications open until 30 November 2026.", "Estimated first-year tuition R51,865 to R80,071 (2026) depending on qualification, e.g. Accounting R80,072, Engineering R70,345, Education R61,912.", "Traditional university"),
 'ufs': ("UFS", "University of the Free State", "Free State", "Bloemfontein, Qwaqwa, Sasolburg", "https://www.ufs.ac.za", "Undergraduate applications for 2027 closed 30 September 2026. No late applications. Always confirm on the official site as some years close earlier.", "Estimated first-year tuition around R49,130 (2026), charged per module.", "Traditional university"),
 'ru': ("RU", "Rhodes University", "Eastern Cape", "Grahamstown / Makhanda", "https://www.ru.ac.za", "Rhodes lists a standing 30 September closing date for new students. No 2027-specific notice was published, so confirm on the official site.", "First-year tuition roughly R63,519 to R71,254 (2026).", "Traditional university"),
 'ufh': ("UFH", "University of Fort Hare", "Eastern Cape", "Alice, East London, Bhisho", "https://www.ufh.ac.za", "Applications opened 1 May 2026 and closed 31 October 2026. Master's and honours also closed 31 October 2026; doctoral applications close 31 March 2027.", "Check the official fee booklet — fees vary by faculty and are usually at the lower end of the range.", "Traditional university"),
 'ul': ("UL", "University of Limpopo", "Limpopo", "Turfloop, near Polokwane", "https://www.ul.ac.za", "Undergraduate applications closed 30 September 2026. Medicine (MBChB) and international applicants closed 30 July 2026.", "First-year BCom from about R39,000 (2026) — among the most affordable traditional universities.", "Traditional university"),
 'univen': ("UNIVEN", "University of Venda", "Limpopo", "Thohoyandou", "https://www.univen.ac.za", "Applications opened 1 May 2026 and closed 30 September 2026. Online applications are free.", "Estimated first-year tuition around R35,160 (2026). No application fee for 2027.", "Traditional university"),
 'wsu': ("WSU", "Walter Sisulu University", "Eastern Cape", "East London, Butterworth, Mthatha, Komani", "https://www.wsu.ac.za", "Applications opened 1 June 2026 and closed 31 October 2026. International applicants closed 30 September 2026.", "No current official fee document was found online — check the WSU student fees page directly.", "Comprehensive university"),
 'uwc': ("UWC", "University of the Western Cape", "Western Cape", "Bellville, Cape Town", "https://www.uwc.ac.za", "Applications opened 1 April 2026 and generally closed at the end of September 2026. Some programmes close earlier — check your qualification.", "Check the official UWC fee booklet for your faculty; fees are generally mid-range.", "Traditional university"),
 'unisa': ("UNISA", "University of South Africa", "Gauteng", "Pretoria (mostly distance and online learning)", "https://www.unisa.ac.za", "Different cycle from residential universities: undergraduate applications closed 9 October 2026. Master's and doctoral applications closed 20 November 2026. Check the Unisa website for the next opening.", "Distance-learning fees vary by module. Unisa does not have campus residence in the traditional sense.", "Distance-learning university"),
 'spu': ("SPU", "Sol Plaatje University", "Northern Cape", "Kimberley", "https://www.spu.ac.za", "Undergraduate and postgraduate applications for 2027 were open until 31 October 2026.", "No current fee document found online — check the official SPU fees page.", "Traditional university"),
 'smu': ("SMU", "Sefako Makgatho Health Sciences University", "Gauteng", "Ga-Rankuwa, Pretoria", "https://www.smu.ac.za", "Applications opened 1 April 2026 and closed 31 July 2026. Health-sciences programmes fill early.", "Health-sciences fee structure — check the official SMU fees page for your programme.", "Health-sciences university"),
 'ump': ("UMP", "University of Mpumalanga", "Mpumalanga", "Mbombela / Nelspruit", "https://www.ump.ac.za", "Applications opened 1 June 2026 and close 30 November 2026 — one of the last public universities still open. Postgraduate applications close 30 January 2027. No application fee for 2027.", "Estimated first-year tuition R43,969 to R48,041 (2026).", "Traditional university"),
 'cput': ("CPUT", "Cape Peninsula University of Technology", "Western Cape", "Cape Town, Bellville, Wellington", "https://www.cput.ac.za", "Applications opened 11 May 2026. Most undergraduate programmes closed 30 September 2026, some earlier — confirm your programme on the CPUT site.", "Tuition varies by programme; check the official CPUT fee booklet. Residence and textbooks are extra.", "University of technology"),
 'dut': ("DUT", "Durban University of Technology", "KwaZulu-Natal", "Durban, Pietermaritzburg", "https://www.dut.ac.za", "Applications for 2027 opened 1 March 2026 and closed 30 September 2026 via CAO. Some programmes close earlier.", "Check the official DUT fees page for your department; technology programmes vary widely.", "University of technology"),
 'tut': ("TUT", "Tshwane University of Technology", "Gauteng", "Pretoria (multiple campuses)", "https://www.tut.ac.za", "Applications opened 1 April 2026 and the main deadline was 31 July 2026. TUT may consider late applications while spaces remain; a late fee may apply. Contact 086 110 2421.", "Fees vary by programme; check the official TUT fee schedule before budgeting.", "University of technology"),
 'cut': ("CUT", "Central University of Technology", "Free State", "Bloemfontein, Welkom", "https://www.cut.ac.za", "Applications opened 1 April 2026 and closed 30 September 2026. CUT states there are no late or walk-in applications.", "Check the official CUT fees booklet for your programme.", "University of technology"),
 'vut': ("VUT", "Vaal University of Technology", "Gauteng", "Vanderbijlpark", "https://www.vut.ac.za", "Applications opened 21 May 2026 and closed 30 October 2026 for national applicants. International applicants closed 30 September 2026; several diplomas and BEd closed 31 July 2026.", "Check the official VUT fees page for your programme.", "University of technology"),
 'mru': ("MUT", "Mangosuthu University of Technology", "KwaZulu-Natal", "Umlazi, Durban", "https://www.mut.ac.za", "Applications for 2027 opened 1 March 2026 and generally closed 30 September 2026 via CAO.", "Check the official MUT fee schedule — technology programmes vary by department.", "University of technology"),
 'zululand': ("UNIZULU", "University of Zululand", "KwaZulu-Natal", "KwaDlangezwa, near Richards Bay", "https://www.unizulu.ac.za", "Standing undergraduate deadline through CAO is 30 September 2026. No 2027-specific notice published — confirm on the official site.", "Check the official UNIZULU fees page for your programme.", "Traditional university"),
 'mandela': ("NMU", "Nelson Mandela University", "Eastern Cape", "Gqeberha (Port Elizabeth), with George campus", "https://www.mandela.ac.za", "Applications for 2027 opened 13 April 2026. The final closing date was not confirmed on the official site — check before relying on a date. Online applications for 2027 are free.", "Check the official NMU student accounts guide for your faculty; fees vary by programme. No application fee for 2027 online applications.", "Comprehensive university"),
 'uj': ("UJ", "University of Johannesburg", "Gauteng", "Auckland Park, Doornfontein and Soweto campuses", "https://www.uj.ac.za", "Applications opened 1 April 2026 and closed 31 October 2026 at 12:00. UJ does not accept late applications.", "Estimated first-year tuition R49,800 to R87,000 (2026), depending on faculty and programme.", "Comprehensive university"),
}

APPLY = {
 'uchenn': 'https://applyonline.uct.ac.za/',
 'wits': 'https://www.wits.ac.za/undergraduate/apply-to-wits/',
 'su': 'https://student.sun.ac.za/signup/',
 'up': 'https://www.up.ac.za/apply',
 'ukzn': 'https://applications.ukzn.ac.za/',
 'nwu': 'https://www.nwu.ac.za/apply',
 'ufs': 'https://www.ufs.ac.za/apply',
 'ru': 'https://ross.ru.ac.za/ugadmissions',
 'ufh': 'https://www.ufh.ac.za/apply',
 'ul': 'https://ulc-prod-webserver.ul.ac.za/pls/prodi41/gen.gw1pkg.gw1view',
 'univen': 'https://univenierp01.univen.ac.za/pls/prodi41/gen.gw1pkg.gw1startup?x_processcode=ITS_OAP',
 'wsu': 'https://applications.wsu.ac.za/',
 'uwc': 'https://student.uwc.ac.za/',
 'unisa': 'https://www.unisa.ac.za/apply',
 'spu': 'https://applications-prod.spu.ac.za/',
 'smu': 'https://www.smu.ac.za/apply',
 'ump': 'https://www.ump.ac.za/apply',
 'cput': 'https://www.cput.ac.za/study-at-cput/undergraduate/apply',
 'dut': 'https://onlineapps.dut.ac.za/',
 'tut': 'https://www.tut.ac.za/index.php/apply/apply-online',
 'cut': 'https://www.cut.ac.za/admission-online',
 'vut': 'https://www.vut.ac.za/apply',
 'mru': 'https://www.mut.ac.za/apply',
 'zululand': 'https://www.cao.ac.za/',
 'mandela': 'https://apps.mandela.ac.za/e-portal/Profile/CreateProfile',
 'uj': 'https://registration.uj.ac.za/pls/prodi41/gen.gw1pkg.gw1startup?x_processcode=ITS_OAP',
}

TMPL = '''<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{short} Offline Guide</title>
<style>
:root{{--bg:#070707;--card:#141414;--fg:#ffa500;--muted:#ffa500;--line:#ffa500;}}
*{{box-sizing:border-box}}
body{{margin:0;background:var(--bg);color:var(--fg);font-family:system-ui,-apple-system,Segoe UI,Roboto,Arial;line-height:1.6;padding:16px}}
h1{{font-size:1.5rem;margin:0 0 4px}} h2{{font-size:1.05rem;margin:0 0 8px}}
.header{{text-align:center;padding:12px 0 20px}}
.sub{{color:var(--muted);font-size:.9rem}}
.section{{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:14px;margin:12px 0}}
.section p,.section li{{color:var(--muted);font-size:.95rem}}
ul,ol{{margin:6px 0 0 18px;padding:0}}
a{{color:#ffa500}}
.note{{color:var(--muted);font-size:.85rem;border-left:3px solid #ffa500;padding-left:10px}}
.badge{{display:inline-block;border:1px solid var(--line);border-radius:20px;padding:3px 10px;font-size:.8rem;margin:2px}}
footer{{text-align:center;color:var(--muted);font-size:.8rem;padding:18px}}
</style></head><body>
<div class="header"><h1>{short}</h1><div class="sub">{full}</div>
<div>{province} &middot; {campus} &middot; {kind}</div>
<div><span class="badge">STUDY 2027</span><span class="badge">OFFLINE GUIDE</span></div></div>
<div class="section"><h2>1. Application dates for 2027 entry</h2><p>{deadline}</p>
<p class="note">Dates were checked in November 2026. Universities change deadlines without warning — always confirm on the official website before you rely on a date.</p></div>
<div class="section"><h2>2. Fees and funding</h2><p>{fees}</p><ul>
<li>Tuition is usually charged per module or course — your final bill depends on the subjects you register for.</li>
<li>Residence, meals, books, transport and registration levies are separate from tuition.</li>
<li>If your household income is R350,000 or less per year, check NSFAS — it can cover tuition and residence at public universities.</li>
<li>Ask the university for a written fee quotation before you register.</li></ul></div>
<div class="section"><h2>3. What to prepare before you apply</h2><ol>
<li>A certified copy of your ID or passport.</li>
<li>Your latest school results and subjects (and predicted results if you are still in Grade 12).</li>
<li>Your APS score — most universities publish a calculator on their site.</li>
<li>Proof of address and any supporting documents the portal asks for.</li>
<li>A working email address you check daily — all updates go there.</li></ol>
<p class="note">Complete the application yourself. Many universities will not accept applications submitted by agents.</p></div>
<div class="section"><h2>4. Accommodation</h2><ul>
<li>Residence applications often close on the same date as, or before, the main application deadline — apply early.</li>
<li>Ask whether the residence fee includes meals, and what the deposit is.</li>
<li>Check the official residence page for application dates, room types and contact details.</li>
<li>Verify the campus location — {campus} — before arranging transport or a lease.</li></ul></div>
<div class="section"><h2>5. Student life</h2><ul>
<li>Join at least one student society or club in your first month — it is the fastest way to find friends and support.</li>
<li>{life}</li>
<li>Use the campus health service, counselling and academic support early — you do not have to wait until you are struggling.</li>
<li>Part-time work and study support are available; ask the student affairs office.</li></ul></div>
<div class="section"><h2>6. Official links</h2>
<p><a href="{site}">Official university website: {site}</a></p>
<p><a href="{apply}">Apply online - official application page</a></p>
<p class="note">This guide is for offline planning only. The official website is the final source of truth for fees, deadlines and entry requirements.</p></div>
<footer>ACEsi offline guide &middot; compiled November 2026 &middot; verify all details at {site}</footer>
</body></html>
'''

LIFE = {
 'University of technology': 'Universities of technology are practical and career-focused; expect project work, workplace learning and industry-linked qualifications.',
 'Traditional university': 'Traditional universities usually offer a broad academic range with research opportunities and a strong postgraduate pathway.',
 'Comprehensive university': 'Comprehensive universities combine academic degrees with career-focused programmes across several campuses.',
 'Distance-learning university': 'Distance learning gives you flexibility; set up a regular study schedule and use the online student portal daily.',
 'Health-sciences university': 'Health-sciences programmes are intensive and often have early closing dates and additional selection requirements.',
}

for uid, (short, full, province, campus, site, deadline, fees, kind) in U.items():
    html = TMPL.format(short=short, full=full, province=province, campus=campus,
                       site=site, apply=APPLY[uid], deadline=deadline, fees=fees,
                       life=LIFE.get(kind, ''), kind=kind)
    with open(os.path.join(OUT, uid + '.html'), 'w', encoding='utf-8') as f:
        f.write(html)
    print(uid, len(html))
print('generated', len(U), 'guides')
