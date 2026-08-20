const String postalCodeJsData = '''
{c:'9880', d:'42nd HILL,Harrismith'}
{c:'6670', d:'AALWYNFLEUR'}
{c:'9301', d:'AANDRUS'}
{c:'9301', d:'AANDRUS,Bloemfontein'}
{c:'7301', d:'ABBOTSDALE'}
{c:'7300', d:'ABBOTSDALE'}
{c:'5241', d:'ABBOTSFORD'}
{c:'5241', d:'ABBOTSFORD,East London'}
{c:'5241', d:'ABBOTSFORD,Oos-Londen'}
{c:'2192', d:'ABBOTSFORD,Witspos'}
{c:'0608', d:'ABBOTSPOORT'}
{c:'0884', d:'ABEL'}
{c:'6270', d:'ABERDEEN'}
{c:'6270', d:'ABERDEEN,Aberdeen'}
{c:'1039', d:'ACKERVILLE'}
{c:'1034', d:'ACKERVILLE,Witbank'}
{c:'1360', d:'ACORNHOEK'}
{c:'1429', d:'ACTIVIA PARK'}
{c:'1401', d:'ACTIVIA PARK,Elandsfontein'}
{c:'5401', d:'ACTON CABA'}
{c:'3352', d:'ACTON HOMES'}
{c:'1501', d:'ACTONVILLE EXT 2,Benoni'}
{c:'1501', d:'ACTONVILLE EXT 3,Benoni'}
{c:'1501', d:'ACTONVILLE EXT 4,Benoni'}
{c:'1501', d:'ACTONVILLE EXT 5,Benoni'}
{c:'1501', d:'ACTONVILLE UIT 2,Benoni'}
{c:'1501', d:'ACTONVILLE UIT 3,Benoni'}
{c:'1501', d:'ACTONVILLE UIT 4,Benoni'}
{c:'1501', d:'ACTONVILLE UIT 5,Benoni'}
{c:'1506', d:'ACTONVILLE,Benoni'}
{c:'1501', d:'ACTONVILLE,Benoni'}
{c:'2571', d:'ADAMAYVIEW,Klerksdorp'}
{c:'4100', d:'ADAMS MISSION'}
{c:'6045', d:'ADCOCK VALE EXT,Port Elizabeth'}
{c:'6045', d:'ADCOCK VALE UIT,Port Elizabeth'}
{c:'6001', d:'ADCOCK VALE,Port Elizabeth'}
{c:'0712', d:'ADDNEY'}
{c:'6105', d:'ADDO'}
{c:'5760', d:'ADELAIDE'}
{c:'6282', d:'ADENDORP'}
{c:'7798', d:'ADMIRALS HILL'}
{c:'7490', d:'ADRIAANSE,Elsie`s River'}
{c:'7490', d:'ADRIAANSE,Elsiesrivier'}
{c:'5092', d:'ADVENT'}
{c:'1070', d:'AERORAND,Middelburg'}
{c:'1055', d:'AERORAND,Middelburg'}
{c:'0534', d:'AFGUNS'}
{c:'3294', d:'AFRICAN ENTERPRISE,Pietermarit'}
{c:'1739', d:'AGAVIA,Krugersdorp'}
{c:'8893', d:'AGGENEYS'}
{c:'2157', d:'AIRDLIN,Sunninghill'}
{c:'1501', d:'AIRFIELD,Benoni'}
{c:'2577', d:'ALABAMA'}
{c:'2091', d:'ALAN MANOR,Johannesburg'}
{c:'1401', d:'ALBEMARLE EXT 1,Germiston'}
{c:'1401', d:'ALBEMARLE EXT 2,Germiston'}
{c:'1401', d:'ALBEMARLE UIT 1,Germiston'}
{c:'1401', d:'ALBEMARLE UIT 2,Germiston'}
{c:'1410', d:'ALBEMARLE,Germiston'}
{c:'1401', d:'ALBEMARLE,Germiston'}
{c:'1449', d:'ALBERANTE EXT 1,Alberton'}
{c:'1449', d:'ALBERANTE EXT,Alberton'}
{c:'1449', d:'ALBERANTE UIT 1,Alberton'}
{c:'1449', d:'ALBERANTE UIT,Alberton'}
{c:'1449', d:'ALBERANTE,Alberton'}
{c:'6695', d:'ALBERTINIA'}
{c:'1450', d:'ALBERTON'}
{c:'1449', d:'ALBERTON'}
{c:'1449', d:'ALBERTON EXT 28,Alberton'}
{c:'1456', d:'ALBERTON NORTH'}
{c:'1449', d:'ALBERTON NORTH'}
{c:'1449', d:'ALBERTON UIT 28,Alberton'}
{c:'1456', d:'ALBERTON-NOORD'}
{c:'1449', d:'ALBERTON-NOORD'}
{c:'1448', d:'ALBERTSDAL EXT 6,Alberton'}
{c:'1448', d:'ALBERTSDAL EXT 7,Alberton'}
{c:'1448', d:'ALBERTSDAL UIT 6,Alberton'}
{c:'1448', d:'ALBERTSDAL UIT 7,Alberton'}
{c:'1448', d:'ALBERTSDAL,Alberton'}
{c:'2195', d:'ALBERTSKROON,Johannesburg'}
{c:'2195', d:'ALBERTSVILLE,Johannesburg'}
{c:'4240', d:'ALBERTSVILLE,Port Shepstone'}
{c:'8301', d:'ALBERTYNSHOF,Kimberley'}
{c:'7405', d:'ALBOWVILLE,Rugby'}
{c:'2194', d:'ALDARAPARK,Randburg'}
{c:'8290', d:'ALEXANDER BAY'}
{c:'8290', d:'ALEXANDERBAAI'}
{c:'2090', d:'ALEXANDRA'}
{c:'2014', d:'ALEXANDRA'}
{c:'3201', d:'ALEXANDRA,Pietermaritzburg'}
{c:'6185', d:'ALEXANDRIA'}
{c:'6005', d:'ALGOAPARK'}
{c:'6001', d:'ALGOAPARK'}
{c:'5700', d:'ALICE'}
{c:'6135', d:'ALICEDALE'}
{c:'7764', d:'ALICEDALE,Athlone'}
{c:'9750', d:'ALIWAL NORTH'}
{c:'9750', d:'ALIWAL-NOORD'}
{c:'0005', d:'ALKANTRANT'}
{c:'5052', d:'ALL SAINTS'}
{c:'3201', d:'ALLANDALE HEIGHTS,Pietermaritz'}
{c:'3201', d:'ALLANDALE,Pietermaritzburg'}
{c:'9490', d:'ALLANRIDGE'}
{c:'0909', d:'ALLDAYS'}
{c:'1619', d:'ALLEN GROVE,Kempton Park'}
{c:'1737', d:'ALLEN`S NEK'}
{c:'7945', d:'ALLENBY,Retreat'}
{c:'0512', d:'ALMA'}
{c:'6670', d:'ALOERIDGE,Riversdal'}
{c:'6670', d:'ALOERIDGE,Riversdale'}
{c:'5319', d:'ALOEVALE,Queenstown'}
{c:'1501', d:'ALPHEN PARK,Benoni'}
{c:'0081', d:'ALPHEN PARK,Pretoria'}
{c:'7785', d:'ALPHINE PARK,Mitchells Plain'}
{c:'1495', d:'ALRAPARK'}
{c:'1491', d:'ALRAPARK'}
{c:'1451', d:'ALRODE'}
{c:'1449', d:'ALRODE'}
{c:'3900', d:'ALTON,Richards Bay'}
{c:'3900', d:'ALTON,Richardsbaai'}
{c:'1785', d:'ALUNSA'}
{c:'2955', d:'AMAJUBA'}
{c:'2940', d:'AMAJUBA PARK,Newcastle'}
{c:'2092', d:'AMALGAM,Johannesburg'}
{c:'2786', d:'AMALIA'}
{c:'5252', d:'AMALINDA'}
{c:'5247', d:'AMALINDA'}
{c:'7550', d:'AMANDAGLEN,Durbanville'}
{c:'0362', d:'AMANDELBULT,Chromite'}
{c:'7580', d:'AMANDELRUG,Kuils River'}
{c:'7580', d:'AMANDELRUG,Kuilsrivier'}
{c:'7580', d:'AMANDELSIG,Kuils River'}
{c:'7580', d:'AMANDELSIG,Kuilsrivier'}
{c:'4126', d:'AMANZIMTOTI'}
{c:'4125', d:'AMANZIMTOTI'}
{c:'4344', d:'AMAWOTANA'}
{c:'8078', d:'AMC CLASSIC,Capemail'}
{c:'2490', d:'AMERSFOORT'}
{c:'7646', d:'AMSTELHOF,Paarl'}
{c:'2375', d:'AMSTERDAM'}
{c:'2194', d:'AMSTERDAM,Randburg'}
{c:'6210', d:'AMSTERDAMHOEK,Swartkops'}
{c:'8550', d:'ANDALUSIA PARK'}
{c:'1459', d:'ANDERBOLT,Boksburg'}
{c:'4230', d:'ANERLEY'}
{c:'0699', d:'ANNADALE,Pietersburg'}
{c:'7441', d:'ANNANDALE VILLAGE,Milnerton'}
{c:'7945', d:'ANNATY BANK,Tokai'}
{c:'1402', d:'ANNEX PARK,Germiston'}
{c:'1401', d:'ANNEX PARK,Germiston'}
{c:'0182', d:'ANNLIN EXT 1,Pretoria North'}
{c:'0182', d:'ANNLIN EXT 1,Pretoria-Noord'}
{c:'0182', d:'ANNLIN UIT 1,Pretoria North'}
{c:'0182', d:'ANNLIN UIT 1,Pretoria-Noord'}
{c:'0182', d:'ANNLIN,Pretoria North'}
{c:'0182', d:'ANNLIN,Pretoria-Noord'}
{c:'1711', d:'ANSFRERE'}
{c:'1709', d:'ANSFRERE'}
{c:'1541', d:'ANZAC,Brakpan'}
{c:'0739', d:'APEL'}
{c:'1876', d:'APPLE ORCHARDS,Walkerville'}
{c:'1739', d:'APPLE PARK,Krugersdorp'}
{c:'3900', d:'AQUADENE,Richards Bay'}
{c:'3900', d:'AQUADENE,Richardsbaai'}
{c:'0850', d:'AQUAPARK,Tzaneen'}
{c:'0464', d:'ARABIEDAM'}
{c:'7560', d:'ARAUNA,Brackenfell'}
{c:'3904', d:'ARBEX'}
{c:'2954', d:'ARBOR PARK'}
{c:'9305', d:'ARBORETUM'}
{c:'9301', d:'ARBORETUM'}
{c:'0850', d:'ARBORPARK,Tzaneen'}
{c:'0083', d:'ARCADIA'}
{c:'0007', d:'ARCADIA'}
{c:'8073', d:'ARCADIA MAIL ORDER CO.,Capemai'}
{c:'5201', d:'ARCADIA,East London'}
{c:'6300', d:'ARCADIA,Humansdorp'}
{c:'5201', d:'ARCADIA,Oos-Londen'}
{c:'6059', d:'ARCADIA,Port Elizabeth'}
{c:'1939', d:'ARCON PARK'}
{c:'1937', d:'ARCON PARK'}
{c:'7945', d:'ARDLEIGH PARK,Retreat'}
{c:'4092', d:'ARENA PARK,Chatsworth'}
{c:'7353', d:'ARENDSDALE'}
{c:'2001', d:'ARGYLE,Johannesburg'}
{c:'9602', d:'ARLINGTON'}
{c:'5247', d:'ARNOLDTON,East London'}
{c:'5247', d:'ARNOLDTON,Oos-Londen'}
{c:'1051', d:'ARNOT'}
{c:'2091', d:'ARTHUR`S PLACE,Johannesburg'}
{c:'7780', d:'ASCOT VILLAGE,Lansdowne'}
{c:'6720', d:'ASHBURN,Montagu'}
{c:'8301', d:'ASHBURNHAM,Kimberley'}
{c:'3201', d:'ASHBURTON,Pietermaritzburg'}
{c:'3216', d:'ASHDOWN,Plessislaer'}
{c:'4091', d:'ASHERVILLE,Durban'}
{c:'6280', d:'ASHERVILLE,Graaff-Reinet'}
{c:'0081', d:'ASHLEA GARDENS,Pretoria'}
{c:'3610', d:'ASHLEY,Pinetown'}
{c:'6715', d:'ASHTON'}
{c:'3610', d:'ASHWOOD'}
{c:'3605', d:'ASHWOOD'}
{c:'1401', d:'ASIATIC BAZAAR,Germiston'}
{c:'5413', d:'ASKEATON'}
{c:'8814', d:'ASKHAM'}
{c:'6667', d:'ASKRAAL'}
{c:'6059', d:'ASPEN HEIGHTS,Port Elizabeth'}
{c:'4052', d:'ASSEGAI,Durban'}
{c:'1630', d:'ASTON MANOR'}
{c:'1619', d:'ASTON MANOR'}
{c:'2732', d:'ATAMELANG'}
{c:'4037', d:'ATHENA GARDENS,Durban'}
{c:'4126', d:'ATHLONE PARK,Amanzimtoti'}
{c:'7764', d:'ATHLONE,Cape Town'}
{c:'7760', d:'ATHLONE,Cape Town'}
{c:'4051', d:'ATHLONE,Durban'}
{c:'7764', d:'ATHLONE,Kaapstad'}
{c:'7760', d:'ATHLONE,Kaapstad'}
{c:'3201', d:'ATHLONE,Pietermaritzburg'}
{c:'2196', d:'ATHOLHURST,Johannesburg'}
{c:'2196', d:'ATHOLHURSTON,Johannesburg'}
{c:'2031', d:'ATHOLL EXT 12'}
{c:'2196', d:'ATHOLL GARDENS,Johannesburg'}
{c:'3630', d:'ATHOLL HEIGHTS,Westville'}
{c:'2031', d:'ATHOLL UIT 12'}
{c:'2196', d:'ATHOLL,Johannesburg'}
{c:'7384', d:'ATLANTIC,Capemail'}
{c:'7349', d:'ATLANTIS,Capemail'}
{c:'1465', d:'ATLASVILLE'}
{c:'1459', d:'ATLASVILLE EXT 1,Boksburg'}
{c:'1459', d:'ATLASVILLE UIT 1,Boksburg'}
{c:'1459', d:'ATLASVILLE,Boksburg'}
{c:'0749', d:'ATOK'}
{c:'0514', d:'ATOOM'}
{c:'7354', d:'ATTAWAY'}
{c:'0008', d:'ATTERIDGEVILLE EXT 2,Pretoria'}
{c:'0008', d:'ATTERIDGEVILLE EXT 3,Pretoria'}
{c:'0008', d:'ATTERIDGEVILLE UIT 2,Pretoria'}
{c:'0008', d:'ATTERIDGEVILLE UIT 3,Pretoria'}
{c:'0008', d:'ATTERIDGEVILLE,Pretoria'}
{c:'2092', d:'AUCKLAND PARK'}
{c:'2006', d:'AUCKLAND PARK'}
{c:'7130', d:'AUDAS,Somerset West'}
{c:'7130', d:'AUDAS,Somerset-Wes'}
{c:'8874', d:'AUGRABIES'}
{c:'7325', d:'AURORA'}
{c:'7550', d:'AURORA,Durbanville'}
{c:'4052', d:'AUSTERVILLE'}
{c:'4005', d:'AUSTERVILLE'}
{c:'7580', d:'AUSTINVILLE,Blackheath'}
{c:'1739', d:'AVALANO,Krugersdorp'}
{c:'6850', d:'AVIAN PARK,Worcester'}
{c:'4051', d:'AVOCA HILLS,Durban North'}
{c:'4051', d:'AVOCA HILLS,Durban-Noord'}
{c:'4051', d:'AVOCA,Durban North'}
{c:'4051', d:'AVOCA,Durban-Noord'}
{c:'7349', d:'AVONDALE,Atlantis'}
{c:'7530', d:'AVONDALE,Bellville'}
{c:'7500', d:'AVONDALE,Parow'}
{c:'6490', d:'AVONTUUR'}
{c:'7490', d:'AVONWOOD,Elsie`s River'}
{c:'7490', d:'AVONWOOD,Elsiesrivier'}
{c:'1750', d:'AZAADVILLE'}
{c:'2429', d:'AZALIA,Standerton'}
{c:'0183', d:'AZIATIC BAZAAR,Pretoria West'}
{c:'0183', d:'AZIATIC BAZAAR,Pretoria-Wes'}
{c:'7271', d:'BAARDSKEERDERSBOS'}
{c:'3850', d:'BABANANGO'}
{c:'0488', d:'BABETHU'}
{c:'0716', d:'BABIRWA'}
{c:'5015', d:'BADI'}
{c:'1190', d:'BADPLAAS'}
{c:'0329', d:'BAFOKENG'}
{c:'2192', d:'BAGLEYSTON,Johannesburg'}
{c:'0181', d:'BAILEYS MUCKLENEUK,Pretoria'}
{c:'2531', d:'BAILLIE PARK'}
{c:'2526', d:'BAILLIE PARK'}
{c:'9338', d:'BAIN`S VLEI'}
{c:'0611', d:'BAKENBERG'}
{c:'9701', d:'BAKENPARK,Bethlehem'}
{c:'1559', d:'BAKERTON,Springs'}
{c:'2742', d:'BAKERVILLE'}
{c:'4037', d:'BAKERVILLE GARDENS,Durban'}
{c:'7130', d:'BAKKERSHOOGTE,Somerset West'}
{c:'7130', d:'BAKKERSHOOGTE,Somerset-Wes'}
{c:'0746', d:'BAKONE'}
{c:'8001', d:'BAKOVEN,Cape Town'}
{c:'8001', d:'BAKOVEN,Kaapstad'}
{c:'0336', d:'BALEEMA'}
{c:'5740', d:'BALFOUR EXT'}
{c:'5740', d:'BALFOUR UIT'}
{c:'2410', d:'BALFOUR,Tvl'}
{c:'3275', d:'BALGOWAN'}
{c:'4420', d:'BALLITO'}
{c:'6529', d:'BALLOT VIEW,George'}
{c:'1037', d:'BALMORAL'}
{c:'5319', d:'BALMORAL,Queenstown'}
{c:'0619', d:'BALTIMORE'}
{c:'2842', d:'BAMAAKA'}
{c:'2843', d:'BAMARE-A-PHOGOLE'}
{c:'0432', d:'BAMOKGOKO'}
{c:'0800', d:'BANDELIERKOP'}
{c:'7600', d:'BANHOEK,Stellenbosch'}
{c:'5341', d:'BANKIES'}
{c:'8082', d:'BANKMED,Capemail'}
{c:'8001', d:'BANTRY BAY,Cape Town'}
{c:'8001', d:'BANTRYBAAI,Kaapstad'}
{c:'0337', d:'BAPO II'}
{c:'0269', d:'BAPONG'}
{c:'1510', d:'BAPSFONTEIN'}
{c:'6480', d:'BARANDAS'}
{c:'0338', d:'BARATHEO'}
{c:'2765', d:'BARBERSPAN'}
{c:'1309', d:'BARBERTON'}
{c:'1307', d:'BARBERTON'}
{c:'1300', d:'BARBERTON'}
{c:'1459', d:'BARDENE,Boksburg'}
{c:'9786', d:'BARKLY EAST'}
{c:'8375', d:'BARKLY WEST'}
{c:'9786', d:'BARKLY-OOS'}
{c:'8375', d:'BARKLY-WES'}
{c:'2148', d:'BARLOW PARK,Wendywood'}
{c:'5882', d:'BARODA'}
{c:'2945', d:'BARRY HERTZOG PARK,Ladysmith'}
{c:'2940', d:'BARRY HERTZOG PARK,Newcastle'}
{c:'6750', d:'BARRYDALE'}
{c:'1459', d:'BARTLETTS,Boksburg'}
{c:'1202', d:'BARVALE'}
{c:'1401', d:'BARVALLEN,Primrose'}
{c:'2061', d:'BASSONIA'}
{c:'2061', d:'BASSONIA EXT 1,Bassonia'}
{c:'2061', d:'BASSONIA UIT 1,Bassonia'}
{c:'9323', d:'BATHO,Bloemfontein'}
{c:'6166', d:'BATHURST'}
{c:'8476', d:'BATLHAROS'}
{c:'4092', d:'BAY VIEW,Chatsworth'}
{c:'6520', d:'BAY VIEW,Hartenbos'}
{c:'3966', d:'BAYALA'}
{c:'3770', d:'BAYNESFIELD'}
{c:'7441', d:'BAYRIDGE,Table View'}
{c:'5241', d:'BAYSVILLE,East London'}
{c:'5241', d:'BAYSVILLE,Oos-Londen'}
{c:'9301', d:'BAYSWATER,Bloemfontein'}
{c:'5109', d:'BAZIYA'}
{c:'5201', d:'BEACH,East London'}
{c:'7800', d:'BEACH,Hout Bay'}
{c:'7800', d:'BEACH,Houtbaai'}
{c:'5201', d:'BEACH,Oos-Londen'}
{c:'4051', d:'BEACHWOOD,Durban North'}
{c:'4051', d:'BEACHWOOD,Durban-Noord'}
{c:'5241', d:'BEACON BAY'}
{c:'5205', d:'BEACON BAY'}
{c:'5241', d:'BEACON BAY VALLEY EXT'}
{c:'5241', d:'BEACON BAY VALLEY UIT'}
{c:'7349', d:'BEACON HILL,Atlantis'}
{c:'7785', d:'BEACON VALLEY,Mitchells Plain'}
{c:'5241', d:'BEACONBAAI'}
{c:'5205', d:'BEACONBAAI'}
{c:'5241', d:'BEACONBAAIVALLEI,Oos-Londen'}
{c:'8315', d:'BEACONSFIELD'}
{c:'8301', d:'BEACONSFIELD'}
{c:'1939', d:'BEACONSFIELD,Vereeniging'}
{c:'7500', d:'BEACONVALE,Parow'}
{c:'6970', d:'BEAUFORT WEST'}
{c:'6970', d:'BEAUFORT-WES'}
{c:'9585', d:'BEAUMONT,Parys'}
{c:'9459', d:'BEDELIA,Welkom'}
{c:'5780', d:'BEDFORD'}
{c:'2007', d:'BEDFORD GARDENS,Bedfordview'}
{c:'2007', d:'BEDFORDPARK,Bedfordview'}
{c:'2008', d:'BEDFORDVIEW'}
{c:'2007', d:'BEDFORDVIEW'}
{c:'0408', d:'BEDWANG'}
{c:'1940', d:'BEDWORTH PARK'}
{c:'5016', d:'BEECHAMWOOD'}
{c:'0255', d:'BEESTEKRAAL'}
{c:'1779', d:'BEKKERSDAL'}
{c:'1772', d:'BEKKERSDAL'}
{c:'0481', d:'BELABELA'}
{c:'1192', d:'BELFAST'}
{c:'1153', d:'BELFAST'}
{c:'1152', d:'BELFAST'}
{c:'1301', d:'BELFAST'}
{c:'1194', d:'BELFAST'}
{c:'1193', d:'BELFAST'}
{c:'1102', d:'BELFAST'}
{c:'1101', d:'BELFAST'}
{c:'1100', d:'BELFAST'}
{c:'1151', d:'BELFAST'}
{c:'1130', d:'BELFAST'}
{c:'1121', d:'BELFAST'}
{c:'3201', d:'BELFORT,Pietermaritzburg'}
{c:'7764', d:'BELGRAVIA,Athlone'}
{c:'7530', d:'BELGRAVIA,Bellville'}
{c:'5201', d:'BELGRAVIA,East London'}
{c:'2094', d:'BELGRAVIA,Johannesburg'}
{c:'8301', d:'BELGRAVIA,Kimberley'}
{c:'5201', d:'BELGRAVIA,Oos-Londen'}
{c:'7507', d:'BELHAR'}
{c:'7490', d:'BELHAR'}
{c:'6837', d:'BELLA VISTA'}
{c:'6835', d:'BELLA VISTA'}
{c:'4094', d:'BELLAIR'}
{c:'4006', d:'BELLAIR'}
{c:'7530', d:'BELLAIR,Bellville'}
{c:'2091', d:'BELLAVISTA SOUTH,Johannesburg'}
{c:'2091', d:'BELLAVISTA,Johannesburg'}
{c:'2091', d:'BELLAVISTA-SUID,Johannesburg'}
{c:'0142', d:'BELLE OMBRE'}
{c:'2198', d:'BELLEVUE CENTRAL,Johannesburg'}
{c:'2198', d:'BELLEVUE EAST,Johannesburg'}
{c:'2198', d:'BELLEVUE SENTRAAL,Johannesburg'}
{c:'2198', d:'BELLEVUE,Johannesburg'}
{c:'3201', d:'BELLEVUE,Pietermaritzburg'}
{c:'8801', d:'BELLEVUE,Upington'}
{c:'2198', d:'BELLEVUE-OOS,Johannesburg'}
{c:'7530', d:'BELLRAIL,Bellville'}
{c:'5073', d:'BELLROCK'}
{c:'7655', d:'BELLVIEW,Wellington'}
{c:'7535', d:'BELLVILLE'}
{c:'7530', d:'BELLVILLE'}
{c:'7530', d:'BELLVILLE SOUTH,Bellville'}
{c:'7530', d:'BELLVILLE-SUID,Bellville'}
{c:'8720', d:'BELMONT'}
{c:'7570', d:'BELMONT PARK,Kraaifontein'}
{c:'7780', d:'BELTHORNE,Lansdowne'}
{c:'6570', d:'BELVEDERE,Knysna'}
{c:'4400', d:'BELVEDERE,Tongaat'}
{c:'7490', d:'BELVINIE,Matroosfontein'}
{c:'6025', d:'BEN KAMMA,Port Elizabeth'}
{c:'0699', d:'BENDOR PARK EXT 1,Pietersburg'}
{c:'0699', d:'BENDOR PARK EXT 6,Pietersburg'}
{c:'0699', d:'BENDOR PARK EXT 7,Pietersburg'}
{c:'0699', d:'BENDOR PARK UIT 1,Pietersburg'}
{c:'0699', d:'BENDOR PARK UIT 6,Pietersburg'}
{c:'0699', d:'BENDOR PARK UIT 7,Pietersburg'}
{c:'0699', d:'BENDOR PARK,Pietersburg'}
{c:'1220', d:'BENFARM'}
{c:'5411', d:'BENGU'}
{c:'2010', d:'BENMORE'}
{c:'2196', d:'BENMORE GARDENS,Johannesburg'}
{c:'7580', d:'BENNO PARK,Kuils River'}
{c:'7580', d:'BENNO PARK,Kuilsrivier'}
{c:'1501', d:'BENONI'}
{c:'1500', d:'BENONI'}
{c:'1501', d:'BENONI EXT 4,Benoni'}
{c:'1501', d:'BENONI NORTH,Benoni'}
{c:'1502', d:'BENONI SOUTH'}
{c:'1501', d:'BENONI SOUTH'}
{c:'1501', d:'BENONI UIT 4,Benoni'}
{c:'1503', d:'BENONI WEST'}
{c:'1501', d:'BENONI WEST'}
{c:'1501', d:'BENONI-NOORD,Benoni'}
{c:'1502', d:'BENONI-SUID'}
{c:'1501', d:'BENONI-SUID'}
{c:'1503', d:'BENONI-WES'}
{c:'1501', d:'BENONI-WES'}
{c:'1504', d:'BENORYN'}
{c:'1501', d:'BENORYN'}
{c:'2094', d:'BENROSE'}
{c:'2011', d:'BENROSE'}
{c:'9764', d:'BENSONVALE'}
{c:'2195', d:'BERARIO,Johannesburg'}
{c:'0002', d:'BEREA PARK,Pretoria'}
{c:'4007', d:'BEREA ROAD,Durban'}
{c:'3630', d:'BEREA WEST,Westville'}
{c:'4001', d:'BEREA,Durban'}
{c:'5241', d:'BEREA,East London'}
{c:'2198', d:'BEREA,Johannesburg'}
{c:'5241', d:'BEREA,Oos-Londen'}
{c:'7232', d:'BEREAVILLE'}
{c:'4007', d:'BEREAWEG,Durban'}
{c:'3630', d:'BEREA-WES,Westville'}
{c:'1709', d:'BERGBRON EXT 1,Florida'}
{c:'1709', d:'BERGBRON EXT 19,Florida'}
{c:'1709', d:'BERGBRON EXT 2,Florida'}
{c:'1709', d:'BERGBRON EXT 3,Florida'}
{c:'1709', d:'BERGBRON UIT 1,Florida'}
{c:'1709', d:'BERGBRON UIT 19,Florida'}
{c:'1709', d:'BERGBRON UIT 2,Florida'}
{c:'1709', d:'BERGBRON UIT 3,Florida'}
{c:'1709', d:'BERGBRON,Florida'}
{c:'0707', d:'BERGNEK'}
{c:'2404', d:'BERGSIG'}
{c:'2403', d:'BERGSIG'}
{c:'9701', d:'BERGSIG,Bethlehem'}
{c:'7230', d:'BERGSIG,Caledon'}
{c:'6660', d:'BERGSIG,Calitzdorp'}
{c:'7550', d:'BERGSIG,Durbanville'}
{c:'6529', d:'BERGSIG,George'}
{c:'9880', d:'BERGSIG,Harrismith'}
{c:'6120', d:'BERGSIG,Kirkwood'}
{c:'7570', d:'BERGSIG,Kraaifontein'}
{c:'6720', d:'BERGSIG,Montagu'}
{c:'5319', d:'BERGSIG,Queenstown'}
{c:'8240', d:'BERGSIG,Springbok'}
{c:'6850', d:'BERGSIG,Worcester'}
{c:'3350', d:'BERGVILLE'}
{c:'2012', d:'BERGVLEI'}
{c:'7945', d:'BERGVLIET'}
{c:'7864', d:'BERGVLIET'}
{c:'3610', d:'BERKSHIRE DOWNS,Pinetown'}
{c:'5660', d:'BERLIN'}
{c:'7570', d:'BERNADINO HEIGHTS,Kraaifontein'}
{c:'7530', d:'BEROMA,Bellville'}
{c:'1459', d:'BERTON PARK,Boksburg'}
{c:'2094', d:'BERTRAMS,Johannesburg'}
{c:'2013', d:'BERTSHAM'}
{c:'3371', d:'BESTERS'}
{c:'2312', d:'BETHAL'}
{c:'2320', d:'BETHAL'}
{c:'2311', d:'BETHAL'}
{c:'2309', d:'BETHAL'}
{c:'2310', d:'BETHAL'}
{c:'0270', d:'BETHANIE'}
{c:'6059', d:'BETHELSDORP EXT 17,Port Elizab'}
{c:'6059', d:'BETHELSDORP EXT 18,Port Elizab'}
{c:'6059', d:'BETHELSDORP EXT 19,Port Elizab'}
{c:'6059', d:'BETHELSDORP EXT 20,Port Elizab'}
{c:'6059', d:'BETHELSDORP EXT 21,Port Elizab'}
{c:'6059', d:'BETHELSDORP EXT 22,Port Elizab'}
{c:'6059', d:'BETHELSDORP EXT 23,Port Elizab'}
{c:'6059', d:'BETHELSDORP EXT 24,Port Elizab'}
{c:'6059', d:'BETHELSDORP EXT 25,Port Elizab'}
{c:'6059', d:'BETHELSDORP EXT 26,Port Elizab'}
{c:'6059', d:'BETHELSDORP EXT 27,Port Elizab'}
{c:'6059', d:'BETHELSDORP EXT 28,Port Elizab'}
{c:'6059', d:'BETHELSDORP EXT 29,Port Elizab'}
{c:'6059', d:'BETHELSDORP EXT 30,Port Elizab'}
{c:'6059', d:'BETHELSDORP EXT 31,Port Elizab'}
{c:'6059', d:'BETHELSDORP EXT 32,Port Elizab'}
{c:'6059', d:'BETHELSDORP EXT 33,Port Elizab'}
{c:'6059', d:'BETHELSDORP EXT 34,Port Elizab'}
{c:'6059', d:'BETHELSDORP UIT 17,Port Elizab'}
{c:'6059', d:'BETHELSDORP UIT 18,Port Elizab'}
{c:'6059', d:'BETHELSDORP UIT 19,Port Elizab'}
{c:'6059', d:'BETHELSDORP UIT 20,Port Elizab'}
{c:'6059', d:'BETHELSDORP UIT 21,Port Elizab'}
{c:'6059', d:'BETHELSDORP UIT 22,Port Elizab'}
{c:'6059', d:'BETHELSDORP UIT 23,Port Elizab'}
{c:'6059', d:'BETHELSDORP UIT 24,Port Elizab'}
{c:'6059', d:'BETHELSDORP UIT 25,Port Elizab'}
{c:'6059', d:'BETHELSDORP UIT 26,Port Elizab'}
{c:'6059', d:'BETHELSDORP UIT 27,Port Elizab'}
{c:'6059', d:'BETHELSDORP UIT 28,Port Elizab'}
{c:'6059', d:'BETHELSDORP UIT 29,Port Elizab'}
{c:'6059', d:'BETHELSDORP UIT 30,Port Elizab'}
{c:'6059', d:'BETHELSDORP UIT 31,Port Elizab'}
{c:'6059', d:'BETHELSDORP UIT 32,Port Elizab'}
{c:'6059', d:'BETHELSDORP UIT 33,Port Elizab'}
{c:'6059', d:'BETHELSDORP UIT 34,Port Elizab'}
{c:'6059', d:'BETHELSDORP,Port Elizabeth'}
{c:'9701', d:'BETHLEHEM'}
{c:'9700', d:'BETHLEHEM'}
{c:'9992', d:'BETHULIE'}
{c:'7141', d:'BETTY`S BAY'}
{c:'7141', d:'BETTYSBAAI'}
{c:'2194', d:'BEVERLEY GARDENS,Randburg'}
{c:'6070', d:'BEVERLEY GROVE,Port Elizabeth'}
{c:'6020', d:'BEVERLEY HILLS,Port Elizabeth'}
{c:'3630', d:'BEVERLEY HILLS,Westville'}
{c:'7100', d:'BEVERLY PARK,Eerste River'}
{c:'7100', d:'BEVERLY PARK,Eersterivier'}
{c:'1459', d:'BEYERSPARK EXT 13,Boksburg'}
{c:'1459', d:'BEYERSPARK EXT 14,Boksburg'}
{c:'1459', d:'BEYERSPARK EXT 15,Boksburg'}
{c:'1459', d:'BEYERSPARK EXT 3,Boksburg'}
{c:'1459', d:'BEYERSPARK EXT 6,Boksburg'}
{c:'1459', d:'BEYERSPARK UIT 13,Boksburg'}
{c:'1459', d:'BEYERSPARK UIT 14,Boksburg'}
{c:'1459', d:'BEYERSPARK UIT 15,Boksburg'}
{c:'1459', d:'BEYERSPARK UIT 3,Boksburg'}
{c:'1459', d:'BEYERSPARK UIT 6,Boksburg'}
{c:'1459', d:'BEYERSPARK,Boksburg'}
{c:'2094', d:'BEZUIDENHOUTS VALLEY,Johannesb'}
{c:'2094', d:'BEZUIDENHOUTSVALLEI,Johannesbu'}
{c:'5760', d:'BEZUIDENHOUTVILLE,Adelaide'}
{c:'1521', d:'BHEKIMFUNDO'}
{c:'4033', d:'BHEKITHEMBA'}
{c:'3100', d:'BHEKUZULU,Vryheid'}
{c:'1194', d:'BHEVULA'}
{c:'4700', d:'BHONGWENI,Kokstad'}
{c:'0299', d:'BIERSPRUIT,Rustenburg'}
{c:'2755', d:'BIESIESVLEI'}
{c:'0436', d:'BINGLEY'}
{c:'1618', d:'BIRCH ACRES'}
{c:'1618', d:'BIRCH ACRES EXT 1,Kempton Park'}
{c:'1618', d:'BIRCH ACRES EXT 2,Kempton Park'}
{c:'1618', d:'BIRCH ACRES EXT 3,Kempton Park'}
{c:'1618', d:'BIRCH ACRES EXT 4,Kempton Park'}
{c:'1618', d:'BIRCH ACRES EXT 5,Kempton Park'}
{c:'1618', d:'BIRCH ACRES UIT 1,Kempton Park'}
{c:'1618', d:'BIRCH ACRES UIT 2,Kempton Park'}
{c:'1618', d:'BIRCH ACRES UIT 3,Kempton Park'}
{c:'1618', d:'BIRCH ACRES UIT 4,Kempton Park'}
{c:'1618', d:'BIRCH ACRES UIT 5,Kempton Park'}
{c:'1621', d:'BIRCHLEIGH'}
{c:'1618', d:'BIRCHLEIGH EXT 6,Kempton Park'}
{c:'1618', d:'BIRCHLEIGH NORTH EXT 1,Kempton'}
{c:'1618', d:'BIRCHLEIGH NORTH EXT 2,Kempton'}
{c:'1618', d:'BIRCHLEIGH NORTH EXT 3,Kempton'}
{c:'1618', d:'BIRCHLEIGH NORTH UIT 1,Kempton'}
{c:'1618', d:'BIRCHLEIGH NORTH UIT 2,Kempton'}
{c:'1618', d:'BIRCHLEIGH NORTH UIT 3,Kempton'}
{c:'1618', d:'BIRCHLEIGH NORTH,Kempton Park'}
{c:'1618', d:'BIRCHLEIGH UIT 6,Kempton Park'}
{c:'1618', d:'BIRCHLEIGH,Kempton Park'}
{c:'1618', d:'BIRCHLEIGH-NOORD EXT 1,Kempton'}
{c:'1618', d:'BIRCHLEIGH-NOORD EXT 2,Kempton'}
{c:'1618', d:'BIRCHLEIGH-NOORD EXT 3,Kempton'}
{c:'1618', d:'BIRCHLEIGH-NOORD UIT 1,Kempton'}
{c:'1618', d:'BIRCHLEIGH-NOORD UIT 2,Kempton'}
{c:'1618', d:'BIRCHLEIGH-NOORD UIT 3,Kempton'}
{c:'1618', d:'BIRCHLEIGH-NOORD,Kempton Park'}
{c:'2196', d:'BIRDHAVEN,Johannesburg'}
{c:'2015', d:'BIRNAM PARK'}
{c:'2196', d:'BIRNAM,Johannesburg'}
{c:'5605', d:'BISHO'}
{c:'7490', d:'BISHOP LAVIS,Lavistown'}
{c:'7700', d:'BISHOPSCOURT,Claremont'}
{c:'4008', d:'BISHOPSGATE'}
{c:'3203', d:'BISLEY'}
{c:'3201', d:'BISLEY HEIGHTS,Pietermaritzbur'}
{c:'3201', d:'BISLEY VALLEY,Pietermaritzburg'}
{c:'8200', d:'BITTERFONTEIN'}
{c:'5103', d:'BITYI'}
{c:'4800', d:'BIZANA'}
{c:'7581', d:'BLACKHEATH'}
{c:'7580', d:'BLACKHEATH'}
{c:'2195', d:'BLACKHEATH EXT 1,Johannesburg'}
{c:'2195', d:'BLACKHEATH UIT 1,Johannesburg'}
{c:'2195', d:'BLACKHEATH,Johannesburg'}
{c:'1032', d:'BLACKHILL'}
{c:'3201', d:'BLACKRIDGE,Pietermaritzburg'}
{c:'5414', d:'BLACKSTREAM'}
{c:'2194', d:'BLAIRGOWRIE,Randburg'}
{c:'1034', d:'BLANCHEVILLE,Witbank'}
{c:'6531', d:'BLANCO'}
{c:'6529', d:'BLANCO'}
{c:'2021', d:'BLANDFORD RIDGE,Bryanston'}
{c:'1559', d:'BLANWICK PARK,Springs'}
{c:'0292', d:'BLESKOP'}
{c:'9777', d:'BLIKANA'}
{c:'8470', d:'BLIKFONTEIN'}
{c:'8801', d:'BLIKKIES,Upington'}
{c:'2250', d:'BLINKPAN'}
{c:'3102', d:'BLOEDRIVIER'}
{c:'7570', d:'BLOEKOMBOS,Kraaifontein'}
{c:'2571', d:'BLOEKOMVILLE,Klerksdorp'}
{c:'6059', d:'BLOEMENDAL,Port Elizabeth'}
{c:'9301', d:'BLOEMFONTEIN'}
{c:'9300', d:'BLOEMFONTEIN'}
{c:'2660', d:'BLOEMHOF'}
{c:'7530', d:'BLOEMHOF,Bellville'}
{c:'8810', d:'BLOEMSMOND'}
{c:'9364', d:'BLOEMSPRUIT'}
{c:'9323', d:'BLOMANDA,Bloemfontein'}
{c:'7530', d:'BLOMMENDAL,Bellville'}
{c:'7530', d:'BLOMTUIN,Bellville'}
{c:'7530', d:'BLOMVLEI,Bellville'}
{c:'3102', d:'BLOOD RIVER'}
{c:'7443', d:'BLOUBERGRANT'}
{c:'7441', d:'BLOUBERGRANT'}
{c:'2153', d:'BLOUBERGRANT,Jukskeipark'}
{c:'7441', d:'BLOUBERGRISE,Table View'}
{c:'7436', d:'BLOUBERGSTRAND,Capemail'}
{c:'7441', d:'BLOUBERGSTRAND,Milnerton'}
{c:'7100', d:'BLUE DOWNS,Eerste River'}
{c:'7100', d:'BLUE DOWNS,Eersterivier'}
{c:'2021', d:'BLUE HEAVEN,Bryanston'}
{c:'3630', d:'BLUE HEIGHTS,Westville'}
{c:'1685', d:'BLUE HILLS,Halfway House'}
{c:'7785', d:'BLUE HORIZON,Mitchells Plain'}
{c:'4051', d:'BLUE RIDGE,Durban North'}
{c:'4051', d:'BLUE RIDGE,Durban-Noord'}
{c:'5319', d:'BLUE RISE,Queenstown'}
{c:'6210', d:'BLUEWATER BAY,Swartkops'}
{c:'4052', d:'BLUFF'}
{c:'4036', d:'BLUFF'}
{c:'2740', d:'BLYDEVILLE,Lichtenburg'}
{c:'4450', d:'BLYTHEDALE BEACH,Stanger'}
{c:'4963', d:'BLYTHSWOOD'}
{c:'2504', d:'BLYVOORUITSIG'}
{c:'2499', d:'BLYVOORUITSIG'}
{c:'6200', d:'BOAST VILLAGE,Port Elizabeth'}
{c:'1501', d:'BOATLAKE VILLAGE,Benoni'}
{c:'9323', d:'BOCHABELLA,Bloemfontein'}
{c:'0790', d:'BOCHUM'}
{c:'8943', d:'BOEGOEBERG'}
{c:'0561', d:'BOEKENHOUT'}
{c:'0299', d:'BOEKENHOUT,Rustenburg'}
{c:'9951', d:'BOESMANSKOP'}
{c:'6190', d:'BOESMANSRIVIERMOND'}
{c:'2571', d:'BOETRAND,Klerksdorp'}
{c:'9702', d:'BOHLOKONG,Theronville'}
{c:'8420', d:'BOICHOKO,Postmasburg'}
{c:'2625', d:'BOIKANYO'}
{c:'2537', d:'BOIKETLO'}
{c:'1901', d:'BOIPATONG'}
{c:'0308', d:'BOITEKONG'}
{c:'0339', d:'BOITUMELO'}
{c:'5042', d:'BOJENI'}
{c:'7764', d:'BOKMAKIERIE,Athlone'}
{c:'6189', d:'BOKNESSTRAND'}
{c:'1460', d:'BOKSBURG'}
{c:'1459', d:'BOKSBURG'}
{c:'1459', d:'BOKSBURG EAST,Boksburg'}
{c:'1478', d:'BOKSBURG EAST,Germiston'}
{c:'1461', d:'BOKSBURG NORTH,Boksburg'}
{c:'1459', d:'BOKSBURG NORTH,Boksburg'}
{c:'1459', d:'BOKSBURG SOUTH,Boksburg'}
{c:'1459', d:'BOKSBURG WEST,Boksburg'}
{c:'1461', d:'BOKSBURG-NOORD,Boksburg'}
{c:'1459', d:'BOKSBURG-NOORD,Boksburg'}
{c:'1478', d:'BOKSBURG-OOS'}
{c:'1459', d:'BOKSBURG-OOS,Boksburg'}
{c:'1459', d:'BOKSBURG-SUID,Boksburg'}
{c:'1459', d:'BOKSBURG-WES,Boksburg'}
{c:'0474', d:'BOLEU'}
{c:'4935', d:'BOLO RESERVE'}
{c:'9932', d:'BOLOKANANG,Petrusburg'}
{c:'0736', d:'BOLOPA'}
{c:'5325', d:'BOLOTWA'}
{c:'1739', d:'BOLTONIA,Krugersdorp'}
{c:'3201', d:'BOMBAY HEIGHTS,Pietermaritzbur'}
{c:'0009', d:'BON ACCORD'}
{c:'8612', d:'BONA-BONA'}
{c:'1622', d:'BONAERO PARK'}
{c:'1619', d:'BONAERO PARK EXT 1,Kempton Par'}
{c:'1619', d:'BONAERO PARK EXT 2,Kempton Par'}
{c:'1619', d:'BONAERO PARK EXT 3,Kempton Par'}
{c:'1619', d:'BONAERO PARK EXT,Kempton Park'}
{c:'1619', d:'BONAERO PARK UIT 1,Kempton Par'}
{c:'1619', d:'BONAERO PARK UIT 2,Kempton Par'}
{c:'1619', d:'BONAERO PARK UIT 3,Kempton Par'}
{c:'1619', d:'BONAERO PARK UIT,Kempton Park'}
{c:'1619', d:'BONAERO PARK,Kempton Park'}
{c:'8735', d:'BONGANI'}
{c:'6620', d:'BONGOLETHU,Oudtshoorn'}
{c:'9795', d:'BONGWENI,Colesberg'}
{c:'7784', d:'BONGWENI,Khayelitsha'}
{c:'1759', d:'BONGWENI,Randfontein'}
{c:'0927', d:'BONISANI'}
{c:'5241', d:'BONNIE DOONE,East London'}
{c:'5241', d:'BONNIE DOONE,Oos-Londen'}
{c:'7570', d:'BONNIEBRAE,Kraaifontein'}
{c:'6730', d:'BONNIEVALE'}
{c:'1459', d:'BONNIEVALE,Boksburg'}
{c:'7570', d:'BONNY BROOK,Kraaifontein'}
{c:'7764', d:'BONTHEUWEL'}
{c:'7763', d:'BONTHEUWEL'}
{c:'5241', d:'BONZA BAY EXT'}
{c:'5241', d:'BONZA BAY UIT'}
{c:'5241', d:'BONZABAAI,Oos-Londen'}
{c:'2807', d:'BOONS'}
{c:'0201', d:'BOORDFONTEIN'}
{c:'0201', d:'BOORDFONTEIN EAST'}
{c:'0201', d:'BOORDFONTEIN WEST'}
{c:'0201', d:'BOORDFONTEIN-OOS'}
{c:'0201', d:'BOORDFONTEIN-WES'}
{c:'4094', d:'BOOTH AANSLUITING,Durban'}
{c:'4094', d:'BOOTH JUNCTION,Durban'}
{c:'2091', d:'BOOYSENS'}
{c:'2016', d:'BOOYSENS'}
{c:'6059', d:'BOOYSENS PARK,Port Elizabeth'}
{c:'2091', d:'BOOYSENS RESERVE,Johannesburg'}
{c:'0082', d:'BOOYSENS,Pretoria'}
{c:'1913', d:'BOPHELONG'}
{c:'6529', d:'BORCHARDS,George'}
{c:'2194', d:'BORDEAUX,Randburg'}
{c:'2835', d:'BOROLELO,Swartruggens'}
{c:'7530', d:'BOSBELL,Bellville'}
{c:'1280', d:'BOSBOKRAND'}
{c:'7945', d:'BOSCHENDAL,Retreat'}
{c:'0301', d:'BOSHOEK'}
{c:'8340', d:'BOSHOF'}
{c:'2528', d:'BOSKOP'}
{c:'2154', d:'BOSKRUIN EXT,Bromhof'}
{c:'2154', d:'BOSKRUIN UIT,Bromhof'}
{c:'2154', d:'BOSKRUIN,Bromhof'}
{c:'2093', d:'BOSMONT,Johannesburg'}
{c:'7580', d:'BOSONIA,Kuils River'}
{c:'7580', d:'BOSONIA,Kuilsrivier'}
{c:'0409', d:'BOSPLAAS'}
{c:'2730', d:'BOSPOORT'}
{c:'3211', d:'BOSTON'}
{c:'7530', d:'BOSTON,Bellville'}
{c:'1055', d:'BOSVILLE,Middelburg'}
{c:'7185', d:'BOT RIVER'}
{c:'4001', d:'BOTANIC GARDENS,Durban'}
{c:'6857', d:'BOTHA'}
{c:'3660', d:'BOTHA`S HILL'}
{c:'7441', d:'BOTHASIG'}
{c:'7406', d:'BOTHASIG'}
{c:'6220', d:'BOTHASRUS,Despatch'}
{c:'9660', d:'BOTHAVILLE'}
{c:'8582', d:'BOTHITONG'}
{c:'2210', d:'BOTLENG,Delmas'}
{c:'7185', d:'BOTRIVIER'}
{c:'9781', d:'BOTSHABELO'}
{c:'9301', d:'BOTSHABELO,Bloemfontein'}
{c:'6673', d:'BOTTERKLOOF'}
{c:'3903', d:'BOTTLEBRUSH'}
{c:'3201', d:'BOUGHTON,Pietermaritzburg'}
{c:'1272', d:'BOURKE`S LUCK'}
{c:'0764', d:'BOYNE'}
{c:'0728', d:'BOYNE'}
{c:'2881', d:'BRAAKLAAGTE'}
{c:'0954', d:'BRAAMBOS MILITARY BASE'}
{c:'2017', d:'BRAAMFONTEIN'}
{c:'2001', d:'BRAAMFONTEIN'}
{c:'1454', d:'BRACKEN DOWNS'}
{c:'1448', d:'BRACKEN DOWNS EXT 1,Alberton'}
{c:'1448', d:'BRACKEN DOWNS EXT 2,Alberton'}
{c:'1448', d:'BRACKEN DOWNS EXT 3,Alberton'}
{c:'1448', d:'BRACKEN DOWNS EXT 4,Alberton'}
{c:'1448', d:'BRACKEN DOWNS EXT 5,Alberton'}
{c:'1448', d:'BRACKEN DOWNS EXT,Alberton'}
{c:'1448', d:'BRACKEN DOWNS UIT 1,Alberton'}
{c:'1448', d:'BRACKEN DOWNS UIT 2,Alberton'}
{c:'1448', d:'BRACKEN DOWNS UIT 3,Alberton'}
{c:'1448', d:'BRACKEN DOWNS UIT 4,Alberton'}
{c:'1448', d:'BRACKEN DOWNS UIT 5,Alberton'}
{c:'1448', d:'BRACKEN DOWNS UIT,Alberton'}
{c:'1448', d:'BRACKEN DOWNS,Alberton'}
{c:'1452', d:'BRACKEN GARDENS'}
{c:'1448', d:'BRACKEN GARDENS'}
{c:'7560', d:'BRACKEN HEIGHTS,Brackenfell'}
{c:'7561', d:'BRACKENFELL'}
{c:'7560', d:'BRACKENFELL'}
{c:'1448', d:'BRACKENHURST EXT 2,Alberton'}
{c:'1448', d:'BRACKENHURST EXT,Alberton'}
{c:'1448', d:'BRACKENHURST UIT 2,Alberton'}
{c:'1448', d:'BRACKENHURST UIT,Alberton'}
{c:'1448', d:'BRACKENHURST,Alberton'}
{c:'7560', d:'BRACKVILLE,Brackenfell'}
{c:'5209', d:'BRAELYN HEIGHTS,East London'}
{c:'5209', d:'BRAELYN HEIGHTS,Oos-Londen'}
{c:'5201', d:'BRAELYN,East London'}
{c:'5201', d:'BRAELYN,Oos-Londen'}
{c:'4202', d:'BRAEMAR'}
{c:'1541', d:'BRAKPAN'}
{c:'1540', d:'BRAKPAN'}
{c:'1545', d:'BRAKPAN NORTH'}
{c:'1545', d:'BRAKPAN-NOORD'}
{c:'2844', d:'BRAKUIL'}
{c:'6025', d:'BRAMHOPE,Port Elizabeth'}
{c:'2090', d:'BRAMLEY'}
{c:'2018', d:'BRAMLEY'}
{c:'2090', d:'BRAMLEY GARDENS,Johannesburg'}
{c:'2090', d:'BRAMLEY MANOR,Johannesburg'}
{c:'2090', d:'BRAMLEY NORTH,Johannesburg'}
{c:'2090', d:'BRAMLEY PARK'}
{c:'2090', d:'BRAMLEY RESERVE,Johannesburg'}
{c:'2090', d:'BRAMLEY VIEW,Johannesburg'}
{c:'2090', d:'BRAMLEY-NOORD,Johannesburg'}
{c:'9871', d:'BRAND`S POST'}
{c:'9400', d:'BRANDFORT'}
{c:'9324', d:'BRANDHOF'}
{c:'9301', d:'BRANDHOF'}
{c:'9471', d:'BRANDPAN'}
{c:'2303', d:'BRANDSPRUIT'}
{c:'8915', d:'BRANDVLEI'}
{c:'6507', d:'BRANDWAG'}
{c:'9301', d:'BRANDWAG,Bloemfontein'}
{c:'7580', d:'BRANDWAG,Kuils River'}
{c:'7580', d:'BRANDWAG,Kuilsrivier'}
{c:'7130', d:'BRANDWAG,Macassar'}
{c:'7600', d:'BRANDWAG,Stellenbosch'}
{c:'6850', d:'BRANDWAG,Worcester'}
{c:'7580', d:'BRANDWOOD,Kuils River'}
{c:'7580', d:'BRANDWOOD,Kuilsrivier'}
{c:'5418', d:'BRAUNVILLE'}
{c:'8620', d:'BRAY'}
{c:'6858', d:'BREÂ¿RIVIER'}
{c:'1724', d:'BREAUNANDA EXT 1,Roodepoort'}
{c:'1724', d:'BREAUNANDA EXT 2,Roodepoort'}
{c:'1724', d:'BREAUNANDA EXT 3,Roodepoort'}
{c:'1724', d:'BREAUNANDA UIT 1,Roodepoort'}
{c:'1724', d:'BREAUNANDA UIT 2,Roodepoort'}
{c:'1724', d:'BREAUNANDA UIT 3,Roodepoort'}
{c:'1739', d:'BREAUNANDA,Krugersdorp'}
{c:'2021', d:'BRECKNOCK,Bryanston'}
{c:'7280', d:'BREDASDORP'}
{c:'1623', d:'BREDELL'}
{c:'6858', d:'BREEDE RIVER'}
{c:'5601', d:'BREIDBACH,King William`s Town'}
{c:'1541', d:'BRENCANIA,Brakpan'}
{c:'2021', d:'BRENDAVERE,Bryanston'}
{c:'1542', d:'BRENTHURST'}
{c:'1541', d:'BRENTHURST EXT 1,Brakpan'}
{c:'1541', d:'BRENTHURST UIT 1,Brakpan'}
{c:'1541', d:'BRENTHURST,Brakpan'}
{c:'9499', d:'BRENTPARK,Kroonstad'}
{c:'1505', d:'BRENTWOOD PARK'}
{c:'7550', d:'BRENTWOOD PARK,Durbanville'}
{c:'6025', d:'BRENTWOOD PARK,Port Elizabeth'}
{c:'7441', d:'BRENTWOOD VILLAGE,Table View'}
{c:'7100', d:'BRENTWOODPARK,Eerste River'}
{c:'7100', d:'BRENTWOODPARK,Eersterivier'}
{c:'2330', d:'BREYTEN'}
{c:'4051', d:'BRIARDENE,Durban North'}
{c:'4051', d:'BRIARDENE,Durban-Noord'}
{c:'7130', d:'BRIDGEBANK,Somerset West'}
{c:'7130', d:'BRIDGEBANK,Somerset-Wes'}
{c:'6025', d:'BRIDGEMEAD,Port Elizabeth'}
{c:'7764', d:'BRIDGETOWN,Athlone'}
{c:'4068', d:'BRIDGEVALE,Phoenix'}
{c:'6621', d:'BRIDGMANVILLE'}
{c:'6623', d:'BRIDGTON'}
{c:'6620', d:'BRIDGTON'}
{c:'4052', d:'BRIGHTON BEACH,Durban'}
{c:'4009', d:'BRIGHTON BEACH,Durban'}
{c:'9745', d:'BRIGHTSIDE,Ladybrand'}
{c:'4340', d:'BRINDHAVEN,Verulam'}
{c:'0250', d:'BRITS'}
{c:'0250', d:'BRITS EXT 11,Brits'}
{c:'0250', d:'BRITS UIT 11,Brits'}
{c:'8782', d:'BRITSTOWN'}
{c:'2092', d:'BRIXTON'}
{c:'2019', d:'BRIXTON'}
{c:'7130', d:'BRIZA,Somerset West'}
{c:'7130', d:'BRIZA,Somerset-Wes'}
{c:'2020', d:'BROADWAY,Johannesburg'}
{c:'6070', d:'BROADWOOD,Port Elizabeth'}
{c:'8624', d:'BROEDERSPUT'}
{c:'0240', d:'BROEDERSTROOM'}
{c:'0906', d:'BROMBEEK'}
{c:'2154', d:'BROMHOF'}
{c:'0157', d:'BRONBERRIK,Lyttleton'}
{c:'1020', d:'BRONKHORSTSPRUIT'}
{c:'9473', d:'BRONVILLE'}
{c:'4068', d:'BROOKDALE,Phoenix'}
{c:'0011', d:'BROOKLYN'}
{c:'7405', d:'BROOKLYN,Maitland'}
{c:'0181', d:'BROOKLYN,Pretoria'}
{c:'5247', d:'BROOKMEAD,East London'}
{c:'5247', d:'BROOKMEAD,Oos-Londen'}
{c:'5201', d:'BROOKVILLE,East London'}
{c:'5201', d:'BROOKVILLE,Oos-Londen'}
{c:'2198', d:'BRUMA'}
{c:'2026', d:'BRUMA'}
{c:'0184', d:'BRUMMERIA EXT 2,Pretoria'}
{c:'0184', d:'BRUMMERIA UIT 2,Pretoria'}
{c:'0184', d:'BRUMMERIA,Pretoria'}
{c:'3300', d:'BRUNTVILLE,Mooi River'}
{c:'3300', d:'BRUNTVILLE,Mooirivier'}
{c:'3234', d:'BRUYNS HILL'}
{c:'2194', d:'BRYANBRINK,Randburg'}
{c:'2021', d:'BRYANSTON'}
{c:'2152', d:'BRYANSTON EAST,Sloane Park'}
{c:'2060', d:'BRYANSTON EXT 1,Cramerview'}
{c:'2021', d:'BRYANSTON EXT 12'}
{c:'2021', d:'BRYANSTON EXT 13'}
{c:'2060', d:'BRYANSTON EXT 18,Cramerview'}
{c:'2060', d:'BRYANSTON EXT 20,Cramerview'}
{c:'2060', d:'BRYANSTON EXT 24,Cramerview'}
{c:'2060', d:'BRYANSTON EXT 27,Cramerview'}
{c:'2060', d:'BRYANSTON EXT 28,Cramerview'}
{c:'2060', d:'BRYANSTON EXT 29,Cramerview'}
{c:'2194', d:'BRYANSTON EXT 3,Randburg'}
{c:'2060', d:'BRYANSTON EXT 31,Cramerview'}
{c:'2151', d:'BRYANSTON EXT 32,Petervale'}
{c:'2060', d:'BRYANSTON EXT 36,Cramerview'}
{c:'2060', d:'BRYANSTON EXT 37,Cramerview'}
{c:'2021', d:'BRYANSTON EXT 4'}
{c:'2060', d:'BRYANSTON EXT 43,Cramerview'}
{c:'2060', d:'BRYANSTON EXT 45,Cramerview'}
{c:'2194', d:'BRYANSTON EXT 5,Randburg'}
{c:'2021', d:'BRYANSTON EXT 7'}
{c:'2021', d:'BRYANSTON SHOPPING CENTRE'}
{c:'2060', d:'BRYANSTON UIT 1,Cramerview'}
{c:'2021', d:'BRYANSTON UIT 12'}
{c:'2021', d:'BRYANSTON UIT 13'}
{c:'2060', d:'BRYANSTON UIT 18,Cramerview'}
{c:'2060', d:'BRYANSTON UIT 20,Cramerview'}
{c:'2060', d:'BRYANSTON UIT 24,Cramerview'}
{c:'2060', d:'BRYANSTON UIT 27,Cramerview'}
{c:'2060', d:'BRYANSTON UIT 28,Cramerview'}
{c:'2060', d:'BRYANSTON UIT 29,Cramerview'}
{c:'2194', d:'BRYANSTON UIT 3,Randburg'}
{c:'2060', d:'BRYANSTON UIT 31,Cramerview'}
{c:'2151', d:'BRYANSTON UIT 32,Petervale'}
{c:'2060', d:'BRYANSTON UIT 36,Cramerview'}
{c:'2060', d:'BRYANSTON UIT 37,Cramerview'}
{c:'2021', d:'BRYANSTON UIT 4'}
{c:'2060', d:'BRYANSTON UIT 43,Cramerview'}
{c:'2060', d:'BRYANSTON UIT 45,Cramerview'}
{c:'2194', d:'BRYANSTON UIT 5,Randburg'}
{c:'2021', d:'BRYANSTON UIT 7'}
{c:'2060', d:'BRYANSTON WEST,Cramerview'}
{c:'2152', d:'BRYANSTON-OOS,Sloane Park'}
{c:'2060', d:'BRYANSTON-WES,Cramerview'}
{c:'6025', d:'BRYMORE,Port Elizabeth'}
{c:'0083', d:'BRYNTIRION,Pretoria'}
{c:'2066', d:'BUCCLEUGH'}
{c:'4126', d:'BUENA VISTA,Amanzimtoti'}
{c:'5209', d:'BUFFALO FLATS EXT,East London'}
{c:'5209', d:'BUFFALO FLATS EXT,Oos-Londen'}
{c:'5209', d:'BUFFALO FLATS UIT,East London'}
{c:'5209', d:'BUFFALO FLATS UIT,Oos-Londen'}
{c:'5209', d:'BUFFALO FLATS,East London'}
{c:'5209', d:'BUFFALO FLATS,Oos-Londen'}
{c:'5086', d:'BUFFALO NEK'}
{c:'5247', d:'BUFFALO PASS HEIGHTS,East Lond'}
{c:'5247', d:'BUFFALO PASS HEIGHTS,Oos-Londe'}
{c:'5201', d:'BUFFALO,East London'}
{c:'5201', d:'BUFFALO,Oos-Londen'}
{c:'6742', d:'BUFFELJAGS RIVER'}
{c:'6742', d:'BUFFELJAGSRIVIER'}
{c:'4093', d:'BUFFELS BOSCH,Queensburgh'}
{c:'8251', d:'BUFFELS RIVER'}
{c:'4400', d:'BUFFELSDALE,Tongaat'}
{c:'8251', d:'BUFFELSRIVIER'}
{c:'2867', d:'BUHRMANNSDRIF'}
{c:'7441', d:'BUITENZORG VILLAGE,Table View'}
{c:'0531', d:'BULGE RIVER'}
{c:'0531', d:'BULGERIVIER'}
{c:'8535', d:'BULL HILL'}
{c:'9670', d:'BULTFONTEIN'}
{c:'0120', d:'BULTFONTEIN,Pyramid'}
{c:'6971', d:'BULTHOUDERSIG'}
{c:'3244', d:'BULWER'}
{c:'5241', d:'BUNKERS HILL,East London'}
{c:'5241', d:'BUNKERS HILL,Oos-Londen'}
{c:'5115', d:'BUNTINGVILLE'}
{c:'9744', d:'BURGERSDORP'}
{c:'2092', d:'BURGERSDORP,Johannesburg'}
{c:'1150', d:'BURGERSFORT'}
{c:'1739', d:'BURGERSHOOP,Krugersdorp'}
{c:'4093', d:'BURLINGTON GARDENS,Queensburgh'}
{c:'4093', d:'BURLINGTON HEIGHTS,Durban'}
{c:'6705', d:'BURNHOLME,Robertson'}
{c:'1283', d:'BUSHBUCKRIDGE'}
{c:'1284', d:'BUSHBUCKRIDGE'}
{c:'1285', d:'BUSHBUCKRIDGE'}
{c:'1255', d:'BUSHBUCKRIDGE'}
{c:'1280', d:'BUSHBUCKRIDGE'}
{c:'1282', d:'BUSHBUCKRIDGE'}
{c:'2154', d:'BUSHHILL,Bromhof'}
{c:'1811', d:'BUSHKOPPIES,Eldoradopark'}
{c:'4052', d:'BUSHLANDS,Durban'}
{c:'6190', d:'BUSHMANS RIVER MOUTH'}
{c:'0469', d:'BUTHI'}
{c:'4960', d:'BUTTERWORTH'}
{c:'4043', d:'BUTTERWORTHS,Durban'}
{c:'1609', d:'BUURENDAL,Edenvale'}
{c:'3938', d:'BUXEDENI'}
{c:'0923', d:'BUYSDORP'}
{c:'3781', d:'BYRNE VALLEY'}
{c:'5181', d:'CABA VALE'}
{c:'2531', d:'CACHET'}
{c:'2524', d:'CACHET'}
{c:'6001', d:'CADLES,Port Elizabeth'}
{c:'7945', d:'CAFDA,Retreat'}
{c:'5455', d:'CALA'}
{c:'7230', d:'CALEDON'}
{c:'7905', d:'CALEDON SQUARE,Cape Town'}
{c:'7905', d:'CALEDONPLEIN,Kaapstad'}
{c:'6660', d:'CALITZDORP'}
{c:'8190', d:'CALVINIA'}
{c:'5247', d:'CAMBRIDGE'}
{c:'5206', d:'CAMBRIDGE'}
{c:'5247', d:'CAMBRIDGE WEST'}
{c:'5207', d:'CAMBRIDGE WEST'}
{c:'7441', d:'CAMBRIDGE,Milnerton'}
{c:'5247', d:'CAMBRIDGE-WES'}
{c:'5207', d:'CAMBRIDGE-WES'}
{c:'7580', d:'CAMELOT,Kuils River'}
{c:'7580', d:'CAMELOT,Kuilsrivier'}
{c:'8360', d:'CAMPBELL'}
{c:'2571', d:'CAMPBELLDORP,Klerksdorp'}
{c:'4300', d:'CAMPBELLSTOWN,Mount Edgecombe'}
{c:'3720', d:'CAMPERDOWN'}
{c:'8040', d:'CAMPS BAY'}
{c:'8001', d:'CAMPS BAY'}
{c:'3201', d:'CAMPSDRIFT,Pietermaritzburg'}
{c:'4341', d:'CANELANDS'}
{c:'4068', d:'CANESIDE,Phoenix'}
{c:'6186', d:'CANNON ROCKS'}
{c:'8068', d:'CAPE PROVINCIAL ADMINISTRATION'}
{c:'0183', d:'CAPE RESERVE,Pretoria West'}
{c:'0183', d:'CAPE RESERVE,Pretoria-Wes'}
{c:'7975', d:'CAPE RIVIERA,Fish Hoek'}
{c:'7975', d:'CAPE RIVIERA,Vishoek'}
{c:'1739', d:'CAPE SETTLEMENTS,Krugersdorp'}
{c:'6300', d:'CAPE ST FRANCIS,Humansdorp'}
{c:'6313', d:'CAPE ST FRANCIS,Port Elizabeth'}
{c:'8001', d:'CAPE TOWN'}
{c:'8000', d:'CAPE TOWN'}
{c:'7525', d:'CAPE TOWN INTERNATIONAL AIRPOR'}
{c:'8003', d:'CAPEMAIL'}
{c:'0084', d:'CAPITAL PARK,Pretoria'}
{c:'7975', d:'CAPRI VILLAGE,Fish Hoek'}
{c:'7975', d:'CAPRI VILLAGE,Vishoek'}
{c:'0699', d:'CAPRICORN,Pietersburg'}
{c:'7787', d:'CARAVELLE'}
{c:'1724', d:'CARENVALE,Roodepoort'}
{c:'2500', d:'CARLETONVILLE'}
{c:'2499', d:'CARLETONVILLE'}
{c:'2499', d:'CARLETONVILLE EXT 1,Carletonvi'}
{c:'2499', d:'CARLETONVILLE EXT 2,Carletonvi'}
{c:'2499', d:'CARLETONVILLE EXT 3,Carletonvi'}
{c:'2499', d:'CARLETONVILLE EXT 4,Carletonvi'}
{c:'2499', d:'CARLETONVILLE EXT 5,Carletonvi'}
{c:'2499', d:'CARLETONVILLE EXT 6,Carletonvi'}
{c:'2499', d:'CARLETONVILLE EXT 7,Carletonvi'}
{c:'2499', d:'CARLETONVILLE EXT 8,Carletonvi'}
{c:'2499', d:'CARLETONVILLE EXT 9,Carletonvi'}
{c:'2499', d:'CARLETONVILLE UIT 1,Carletonvi'}
{c:'2499', d:'CARLETONVILLE UIT 2,Carletonvi'}
{c:'2499', d:'CARLETONVILLE UIT 3,Carletonvi'}
{c:'2499', d:'CARLETONVILLE UIT 4,Carletonvi'}
{c:'2499', d:'CARLETONVILLE UIT 5,Carletonvi'}
{c:'2499', d:'CARLETONVILLE UIT 6,Carletonvi'}
{c:'2499', d:'CARLETONVILLE UIT 7,Carletonvi'}
{c:'2499', d:'CARLETONVILLE UIT 8,Carletonvi'}
{c:'2499', d:'CARLETONVILLE UIT 9,Carletonvi'}
{c:'2001', d:'CARLTON CENTRE,Johannesburg'}
{c:'8925', d:'CARNARVON'}
{c:'1185', d:'CAROLINA'}
{c:'8247', d:'CAROLUSBERG'}
{c:'7975', d:'CAROLWOOD,Fish Hoek'}
{c:'7975', d:'CAROLWOOD,Vishoek'}
{c:'4001', d:'CARRINGTON HEIGHTS,Durban'}
{c:'8301', d:'CARTERS GLEN,Kimberley'}
{c:'3202', d:'CASCADES'}
{c:'0299', d:'CASHAN,Rustenburg'}
{c:'1459', d:'CASON,Boksburg'}
{c:'8301', d:'CASSANDRA,Kimberley'}
{c:'8587', d:'CASSEL'}
{c:'1559', d:'CASSELDALE,Springs'}
{c:'2351', d:'CASSIM PARK,Ermelo'}
{c:'1370', d:'CASTEEL'}
{c:'4037', d:'CASTLE HILL,Durban'}
{c:'1401', d:'CASTLEVIEW,Germiston'}
{c:'5310', d:'CATHCART'}
{c:'3342', d:'CATHEDRAL PEAK'}
{c:'7764', d:'CATHKIN,Athlone'}
{c:'4091', d:'CATO MANOR,Durban'}
{c:'3680', d:'CATO RIDGE'}
{c:'4093', d:'CAVENDISH,Queensburgh'}
{c:'3616', d:'CAVERSHAM GLEN'}
{c:'4968', d:'CEBE'}
{c:'4720', d:'CEDARVILLE'}
{c:'8136', d:'CEDERBERG'}
{c:'5058', d:'CEFANE'}
{c:'4068', d:'CENTENARY PARK,Phoenix'}
{c:'3266', d:'CENTOCOW'}
{c:'6006', d:'CENTRAHIL'}
{c:'1809', d:'CENTRAL WESTERN JABAVU,Pimvill'}
{c:'5201', d:'CENTRAL,East London'}
{c:'5201', d:'CENTRAL,Oos-Londen'}
{c:'6001', d:'CENTRAL,Port Elizabeth'}
{c:'0157', d:'CENTURION,Pretoria'}
{c:'6835', d:'CERES'}
{c:'1491', d:'CERUTIVILLE,Nigel'}
{c:'3866', d:'CEZA'}
{c:'1739', d:'CHAMDOR,Krugersdorp'}
{c:'1739', d:'CHANCLIFF,Krugersdorp'}
{c:'0310', d:'CHANENG'}
{c:'7550', d:'CHANTECLER,Durbanville'}
{c:'4781', d:'CHARFRED'}
{c:'2301', d:'CHARL CILLIERS'}
{c:'5209', d:'CHARLES LLOYD,East London'}
{c:'5209', d:'CHARLES LLOYD,Oos-Londen'}
{c:'7646', d:'CHARLESTON HILL,Capemail'}
{c:'2473', d:'CHARLESTOWN'}
{c:'9974', d:'CHARLESVILLE,Jagersfontein'}
{c:'7490', d:'CHARLESVILLE,Matroosfontein'}
{c:'6070', d:'CHARLO EXT 5,Port Elizabeth'}
{c:'6070', d:'CHARLO UIT 5,Port Elizabeth'}
{c:'6070', d:'CHARLO,Port Elizabeth'}
{c:'1491', d:'CHARTERSTON,Nigel'}
{c:'3201', d:'CHASE VALLEY DOWNS,Pietermarit'}
{c:'3201', d:'CHASE VALLEY HEIGHTS,Pietermar'}
{c:'3201', d:'CHASE VALLEY,Pietermaritzburg'}
{c:'3201', d:'CHASEDENE,Pietermaritzburg'}
{c:'4012', d:'CHATSGLEN'}
{c:'4092', d:'CHATSWORTH'}
{c:'4030', d:'CHATSWORTH'}
{c:'6062', d:'CHATTY'}
{c:'6059', d:'CHATTY'}
{c:'0756', d:'CHEBENG'}
{c:'4400', d:'CHELMSFORD HEIGHTS,Tongaat'}
{c:'3610', d:'CHELMSFORD PARK,Pinetown'}
{c:'7100', d:'CHELSEA GREEN,Eerste River'}
{c:'7100', d:'CHELSEA GREEN,Eersterivier'}
{c:'2192', d:'CHELTONDALE,Johannesburg'}
{c:'7442', d:'CHEMPET'}
{c:'4001', d:'CHESTERVILLE,Durban'}
{c:'3630', d:'CHILTERN HILLS,Westville'}
{c:'5247', d:'CHISELHURST EXT 3,East London'}
{c:'5247', d:'CHISELHURST EXT 3,Oos-Londen'}
{c:'5247', d:'CHISELHURST EXT,East London'}
{c:'5247', d:'CHISELHURST EXT,Oos-Londen'}
{c:'5247', d:'CHISELHURST UIT 3,East London'}
{c:'5247', d:'CHISELHURST UIT 3,Oos-Londen'}
{c:'5247', d:'CHISELHURST UIT,East London'}
{c:'5247', d:'CHISELHURST UIT,Oos-Londen'}
{c:'5247', d:'CHISELHURST,East London'}
{c:'5247', d:'CHISELHURST,Oos-Londen'}
{c:'2196', d:'CHISLEHURSTON,Johannesburg'}
{c:'1624', d:'CHLOORKOP'}
{c:'7530', d:'CHRISMAR,Bellville'}
{c:'1963', d:'CHRISSIEFONTEIN'}
{c:'2332', d:'CHRISSIESMEER'}
{c:'2680', d:'CHRISTIANA'}
{c:'0183', d:'CHRISTOBURG,Pretoria'}
{c:'2091', d:'CHRISVILLE EXT 1,Johannesburg'}
{c:'2091', d:'CHRISVILLE UIT 1,Johannesburg'}
{c:'2091', d:'CHRISVILLE,Johannesburg'}
{c:'0362', d:'CHROMITE'}
{c:'0601', d:'CHROOMPARK,Potgietersrus'}
{c:'0745', d:'CHUENESPOORT'}
{c:'7500', d:'CHURCHILL,Parow'}
{c:'1463', d:'CINDA PARK'}
{c:'1459', d:'CINDA PARK'}
{c:'1459', d:'CINDERELLA,Boksburg'}
{c:'5275', d:'CINTSA EAST'}
{c:'5275', d:'CINTSA-OOS'}
{c:'3610', d:'CIRCLE GARDENS,Kloof'}
{c:'3610', d:'CIRCLE PARK,Kloof'}
{c:'7340', d:'CITRUSDAL'}
{c:'8070', d:'CITY COUNCIL,Capemail'}
{c:'0004', d:'CITY COUNCIL,Pretoria'}
{c:'2049', d:'CITY DEEP'}
{c:'2001', d:'CITY DEEP'}
{c:'3292', d:'CITY TREASURER,Pietermaritzbur'}
{c:'2092', d:'CITY WEST,Johannesburg'}
{c:'7100', d:'CLAIREWOOD,Eerste River'}
{c:'7100', d:'CLAIREWOOD,Eersterivier'}
{c:'4052', d:'CLAIRWOOD,Durban'}
{c:'7500', d:'CLAM HALL,Parow'}
{c:'1351', d:'CLANOR'}
{c:'4170', d:'CLANSTHAL,Umkomaas'}
{c:'8135', d:'CLANWILLIAM'}
{c:'4091', d:'CLARE,Durban'}
{c:'3201', d:'CLAREDON,Pietermaritzburg'}
{c:'7740', d:'CLAREINCH'}
{c:'7700', d:'CLAREINCH'}
{c:'7735', d:'CLAREMONT,Cape Town'}
{c:'7700', d:'CLAREMONT,Cape Town'}
{c:'2092', d:'CLAREMONT,Johannesburg'}
{c:'7735', d:'CLAREMONT,Kaapstad'}
{c:'7700', d:'CLAREMONT,Kaapstad'}
{c:'0082', d:'CLAREMONT,Pretoria'}
{c:'3201', d:'CLARENDON,Pietermaritzburg'}
{c:'9707', d:'CLARENS'}
{c:'1609', d:'CLARENSPARK,Edenvale'}
{c:'3215', d:'CLARIDGE'}
{c:'5024', d:'CLARKEBURY'}
{c:'7490', d:'CLARKES,Elsie`s River'}
{c:'7490', d:'CLARKES,Elsiesrivier'}
{c:'6302', d:'CLARKSON'}
{c:'0037', d:'CLAUDIUS,Laudium'}
{c:'4068', d:'CLAYFIELD,Phoenix'}
{c:'1666', d:'CLAYVILLE EAST,Olifantsfontein'}
{c:'1666', d:'CLAYVILLE EXT 13,Olifantsfonte'}
{c:'1666', d:'CLAYVILLE EXT 7,Olifantsfontei'}
{c:'1666', d:'CLAYVILLE UIT 13,Olifantsfonte'}
{c:'1666', d:'CLAYVILLE UIT 7,Olifantsfontei'}
{c:'1666', d:'CLAYVILLE,Olifantsfontein'}
{c:'1666', d:'CLAYVILLE-OOS,Olifantsfontein'}
{c:'4037', d:'CLEARHEIGHTS,Durban'}
{c:'6059', d:'CLEARY,Port Elizabeth'}
{c:'3201', d:'CLELAND,Pietermaritzburg'}
{c:'3610', d:'CLERMONT,Pinetown'}
{c:'3602', d:'CLERNAVILLE'}
{c:'2094', d:'CLEVEDEN,Johannesburg'}
{c:'2094', d:'CLEVELAND'}
{c:'2022', d:'CLEVELAND'}
{c:'1036', d:'CLEWER'}
{c:'5247', d:'CLIFTON PARK,East London'}
{c:'3610', d:'CLIFTON PARK,Gillitts'}
{c:'5247', d:'CLIFTON PARK,Oos-Londen'}
{c:'8001', d:'CLIFTON,Cape Town'}
{c:'8001', d:'CLIFTON,Kaapstad'}
{c:'4040', d:'CLOBIA,Durban'}
{c:'9735', d:'CLOCOLAN'}
{c:'7611', d:'CLOETESVILLE'}
{c:'7600', d:'CLOETESVILLE'}
{c:'7975', d:'CLOVELLY,Fish Hoek'}
{c:'7975', d:'CLOVELLY,Vishoek'}
{c:'1513', d:'CLOVERDENE,Putfontein'}
{c:'8092', d:'CLUB MUSIC DIRECT,Capemail'}
{c:'0157', d:'CLUBVIEW'}
{c:'0014', d:'CLUBVIEW'}
{c:'0157', d:'CLUBVIEW EAST,Lyttleton'}
{c:'0157', d:'CLUBVIEW WEST,Lyttleton'}
{c:'7975', d:'CLUBVIEW,Fish Hoek'}
{c:'7975', d:'CLUBVIEW,Vishoek'}
{c:'0157', d:'CLUBVIEW-OOS,Lyttleton'}
{c:'0157', d:'CLUBVIEW-WES,Lyttleton'}
{c:'1055', d:'CLUBVILLE,Middelburg'}
{c:'0002', d:'CLYDESDALE,Pretoria'}
{c:'2196', d:'CLYNTON,Johannesburg'}
{c:'1033', d:'COALVILLE'}
{c:'0772', d:'COBLANDS'}
{c:'0772', d:'COBLENTS'}
{c:'6100', d:'COEGA'}
{c:'7600', d:'COETZENBURG,Stellenbosch'}
{c:'5082', d:'COFFEE BAY'}
{c:'5380', d:'COFIMVABA'}
{c:'5054', d:'COGHLAN'}
{c:'0083', d:'COLBYN,Pretoria'}
{c:'6175', d:'COLCHESTER'}
{c:'6311', d:'COLDSTREAM'}
{c:'3360', d:'COLENSO'}
{c:'9795', d:'COLESBERG'}
{c:'6454', d:'COLESKEPLAAS'}
{c:'2725', d:'COLIGNY'}
{c:'6018', d:'COLLEEN GLEN'}
{c:'2571', d:'COLLERVILLE,Klerksdorp'}
{c:'5201', d:'COLLONDALE,East London'}
{c:'5201', d:'COLLONDALE,Oos-Londen'}
{c:'7785', d:'COLORADO PARK,Mitchells Plain'}
{c:'6620', d:'COLRIDGE UITSIG,Oudtshoorn'}
{c:'6620', d:'COLRIDGE VIEW,Oudtshoorn'}
{c:'8601', d:'COLRIDGE,Vryburg'}
{c:'8301', d:'COLVILLE,Kimberley'}
{c:'1459', d:'COMET,Boksburg'}
{c:'2385', d:'COMMONDALE'}
{c:'9308', d:'COMMUNITY'}
{c:'2064', d:'COMPTONVILLE,Naturena'}
{c:'8271', d:'CONCORDIA'}
{c:'6570', d:'CONCORDIA,Knysna'}
{c:'7100', d:'CONDOR PARK,Eerste River'}
{c:'7100', d:'CONDOR PARK,Eersterivier'}
{c:'9431', d:'CONERA'}
{c:'9430', d:'CONERA'}
{c:'4013', d:'CONGELLA'}
{c:'4001', d:'CONGELLA'}
{c:'7945', d:'CONISTON PARK,Retreat'}
{c:'4340', d:'CONISTON,Verulam'}
{c:'7490', d:'CONNAUGHT,Elsie`s River'}
{c:'7490', d:'CONNAUGHT,Elsiesrivier'}
{c:'1709', d:'CONSOLIDATED MAIN REEF,Florida'}
{c:'7945', d:'CONSORT PARK,Retreat'}
{c:'7100', d:'CONSTANTIA DALE,Eerste River'}
{c:'7100', d:'CONSTANTIA DALE,Eersterivier'}
{c:'7800', d:'CONSTANTIA HILL,Constantia'}
{c:'1709', d:'CONSTANTIA KLOOF,Florida'}
{c:'7100', d:'CONSTANTIA PARK,Eerste River'}
{c:'7100', d:'CONSTANTIA PARK,Eersterivier'}
{c:'7848', d:'CONSTANTIA,Cape Town'}
{c:'7800', d:'CONSTANTIA,Cape Town'}
{c:'5247', d:'CONSTANTIA,East London'}
{c:'7848', d:'CONSTANTIA,Kaapstad'}
{c:'7800', d:'CONSTANTIA,Kaapstad'}
{c:'9499', d:'CONSTANTIA,Kroonstad'}
{c:'5247', d:'CONSTANTIA,Oos-Londen'}
{c:'0010', d:'CONSTANTIAPARK,Glenstantia'}
{c:'7800', d:'CONSTANTIAVALE,Constantia'}
{c:'6529', d:'CONVILLE,George'}
{c:'5820', d:'COOKHOUSE'}
{c:'3201', d:'COPESVILLE,Pietermaritzburg'}
{c:'0016', d:'COR DELFOS'}
{c:'4340', d:'CORDORA GARDENS,Verulam'}
{c:'2090', d:'CORLETT GARDENS,Johannesburg'}
{c:'9850', d:'CORNELIA'}
{c:'7945', d:'CORNUTA,Retreat'}
{c:'0254', d:'CORONA'}
{c:'1739', d:'CORONATION PARK,Krugersdorp'}
{c:'3107', d:'CORONATION,Ladysmith'}
{c:'2093', d:'CORONATIONVILLE,Johannesburg'}
{c:'2195', d:'CORRIEMOOR,Johannesburg'}
{c:'6045', d:'COTSWOLD EXT 2,Port Elizabeth'}
{c:'6045', d:'COTSWOLD EXT,Port Elizabeth'}
{c:'3630', d:'COTSWOLD HILLS,Westville'}
{c:'6045', d:'COTSWOLD UIT 2,Port Elizabeth'}
{c:'6045', d:'COTSWOLD UIT,Port Elizabeth'}
{c:'6045', d:'COTSWOLD,Port Elizabeth'}
{c:'2092', d:'COTTESLOE,Johannesburg'}
{c:'1361', d:'COTTONDALE'}
{c:'2060', d:'COUNTRY LIFE PARK,Cramerview'}
{c:'7646', d:'COURTRAI,Paarl'}
{c:'9759', d:'COVILLE'}
{c:'2060', d:'COWDRAY PARK,Cramerview'}
{c:'3610', d:'COWIE`S HILL PARK,Pinetown'}
{c:'3610', d:'COWIE`S HILL,Pinetown'}
{c:'5880', d:'CRADOCK'}
{c:'6001', d:'CRADOCK PLACE,Port Elizabeth'}
{c:'2021', d:'CRAIGAVON,Bryanston'}
{c:'6001', d:'CRAIGBAIN,Port Elizabeth'}
{c:'2196', d:'CRAIGHALL'}
{c:'2024', d:'CRAIGHALL'}
{c:'2196', d:'CRAIGHALL PARK,Johannesburg'}
{c:'4170', d:'CRAIGIEBURN,Umkomaas'}
{c:'2060', d:'CRAMERVIEW'}
{c:'3220', d:'CRAMOND'}
{c:'0157', d:'CRANBROOKVALE,Lyttleton'}
{c:'7508', d:'CRAVENBY'}
{c:'7490', d:'CRAVENBY,Matroosfontein'}
{c:'7780', d:'CRAWFORD'}
{c:'7770', d:'CRAWFORD'}
{c:'0562', d:'CRECY'}
{c:'3263', d:'CREIGHTON'}
{c:'1619', d:'CRESSLAWNS,Kempton Park'}
{c:'7490', d:'CREST INDUSTRIA,Elsie`s River'}
{c:'7490', d:'CREST INDUSTRIA,Elsiesrivier'}
{c:'2118', d:'CRESTA'}
{c:'2194', d:'CRESTA EXT 2,Randburg'}
{c:'2194', d:'CRESTA UIT 2,Randburg'}
{c:'2194', d:'CRESTA,Randburg'}
{c:'1401', d:'CRESTONHILL,Primrose'}
{c:'6025', d:'CRESTVIEW,Port Elizabeth'}
{c:'1724', d:'CRESWELL PARK,Roodepoort'}
{c:'2093', d:'CROESUS,Johannesburg'}
{c:'4092', d:'CROFTDENE,Chatsworth'}
{c:'1055', d:'CROMEVILLE,Middelburg'}
{c:'2092', d:'CROSBY,Johannesburg'}
{c:'5643', d:'CROSS ROADS'}
{c:'4092', d:'CROSSMOOR,Chatsworth'}
{c:'7753', d:'CROSSROADS'}
{c:'7750', d:'CROSSROADS'}
{c:'2091', d:'CROWN GARDENS,Johannesburg'}
{c:'2092', d:'CROWN MINES'}
{c:'2025', d:'CROWN MINES'}
{c:'1619', d:'CROYDON,Kempton Park'}
{c:'1428', d:'CRUYWAGENPARK,Elsburg'}
{c:'1307', d:'CRYSBESTOS'}
{c:'2090', d:'CRYSTAL GARDENS,Johannesburg'}
{c:'1515', d:'CRYSTAL PARK'}
{c:'1515', d:'CRYSTAL PARK EXT 2,Crystal Par'}
{c:'1515', d:'CRYSTAL PARK EXT 3,Crystal Par'}
{c:'1515', d:'CRYSTAL PARK UIT 2,Crystal Par'}
{c:'1515', d:'CRYSTAL PARK UIT 3,Crystal Par'}
{c:'1724', d:'CULEMBEECK,Roodepoort'}
{c:'1759', d:'CULEMBORGPARK,Randfontein'}
{c:'5880', d:'CULLDENE,Cradock'}
{c:'1000', d:'CULLINAN'}
{c:'3235', d:'CUMBERWOOD'}
{c:'3201', d:'CUMBERWOOD'}
{c:'2198', d:'CYRILDENE,Johannesburg'}
{c:'7975', d:'DA GAMA PARK,Simon`s Town'}
{c:'7975', d:'DA GAMA PARK,Simonstad'}
{c:'6501', d:'DA GAMASKOP'}
{c:'6500', d:'DA GAMASKOP'}
{c:'6500', d:'DA NOVA,Mossel Bay'}
{c:'6500', d:'DA NOVA,Mosselbaai'}
{c:'8477', d:'DAANTJIESRUS'}
{c:'9459', d:'DAGBREEK,Welkom'}
{c:'1573', d:'DAGGAFONTEIN'}
{c:'1559', d:'DAGGAFONTEIN EXT 1,Springs'}
{c:'1559', d:'DAGGAFONTEIN UIT 1,Springs'}
{c:'1559', d:'DAGGAFONTEIN,Springs'}
{c:'1559', d:'DAL FOUCHE,Springs'}
{c:'7646', d:'DAL JOSAFAT,Paarl'}
{c:'4014', d:'DALBRIDGE'}
{c:'4001', d:'DALBRIDGE'}
{c:'2196', d:'DALECROSS,Johannesburg'}
{c:'6220', d:'DALEVIEW,Despatch'}
{c:'1543', d:'DALPARK'}
{c:'7600', d:'DALSIG,Stellenbosch'}
{c:'3236', d:'DALTON'}
{c:'1544', d:'DALVIEW'}
{c:'1541', d:'DALVIEW'}
{c:'5132', d:'DAMBENI'}
{c:'9301', d:'DAN PIENAAR,Bloemfontein'}
{c:'1739', d:'DAN PIENAARVILLE,Krugersdorp'}
{c:'6510', d:'DANA BAY'}
{c:'6510', d:'DANABAAI'}
{c:'7580', d:'DANARAND,Kuils River'}
{c:'7580', d:'DANARAND,Kuilsrivier'}
{c:'7305', d:'DANCKERTVILLE'}
{c:'7300', d:'DANCKERTVILLE'}
{c:'9310', d:'DANHOF'}
{c:'9301', d:'DANHOF'}
{c:'1401', d:'DANIA PARK,Primrose'}
{c:'2194', d:'DANIÂ¿L BRINKPARK,Randburg'}
{c:'8405', d:'DANIÂ¿LSKUIL'}
{c:'9705', d:'DANIÂ¿LSRUS'}
{c:'3080', d:'DANNHAUSER'}
{c:'0183', d:'DANVILLE'}
{c:'0018', d:'DANVILLE'}
{c:'3265', d:'DARGLE'}
{c:'7345', d:'DARLING'}
{c:'4480', d:'DARNALL'}
{c:'2194', d:'DARRENWOOD EXT 2,Randburg'}
{c:'2194', d:'DARRENWOOD UIT 2,Randburg'}
{c:'2194', d:'DARRENWOOD,Randburg'}
{c:'0082', d:'DASPOORT'}
{c:'0019', d:'DASPOORT'}
{c:'7350', d:'DASSENBERG'}
{c:'7349', d:'DASSENBERG'}
{c:'3604', d:'DASSENHOEK,Nagina'}
{c:'2531', d:'DASSIERAND,Potchefstroom'}
{c:'2571', d:'DAVANNA,Klerksdorp'}
{c:'2320', d:'DAVEL'}
{c:'1520', d:'DAVEYTON'}
{c:'1507', d:'DAVEYTON'}
{c:'1724', d:'DAVIDSONVILLE EXT 2,Roodepoort'}
{c:'1724', d:'DAVIDSONVILLE NORTH,Roodepoort'}
{c:'1724', d:'DAVIDSONVILLE UIT 2,Roodepoort'}
{c:'1724', d:'DAVIDSONVILLE,Roodepoort'}
{c:'1724', d:'DAVIDSONVILLE-NOORD,Roodepoort'}
{c:'9499', d:'DAWID MALANVILLE,Kroonstad'}
{c:'9459', d:'DAWIDSBURG,Welkom'}
{c:'2571', d:'DAWKINSVILLE,Klerksdorp'}
{c:'4340', d:'DAWN CREST,Verulam'}
{c:'3630', d:'DAWN CREST,Westville'}
{c:'1474', d:'DAWN PARK'}
{c:'1401', d:'DAWN VIEW,Primrose'}
{c:'5247', d:'DAWN,East London'}
{c:'5247', d:'DAWN,Oos-Londen'}
{c:'3630', d:'DAWNCLIFFE,Westville'}
{c:'1459', d:'DAYANGLEN,Boksburg'}
{c:'7000', d:'DE AAR'}
{c:'8301', d:'DE BEERS,Kimberley'}
{c:'0181', d:'DE BEERS,Pretoria'}
{c:'8375', d:'DE BEERSHOOGTE,Barkly West'}
{c:'8375', d:'DE BEERSHOOGTE,Barkly-Wes'}
{c:'7530', d:'DE BRON,Bellville'}
{c:'9928', d:'DE BRUG'}
{c:'2351', d:'DE BRUINPARK,Ermelo'}
{c:'2571', d:'DE CLERQVILLE,Klerksdorp'}
{c:'1884', d:'DE DEUR'}
{c:'6875', d:'DE DOORNS'}
{c:'7500', d:'DE DUIN,Parow'}
{c:'7580', d:'DE KUILEN,Kuils River'}
{c:'7580', d:'DE KUILEN,Kuilsrivier'}
{c:'6229', d:'DE MIST,Uitenhage'}
{c:'6650', d:'DE RUST'}
{c:'7500', d:'DE TIJGER,Capemail'}
{c:'1002', d:'DE WAGENSDRIFT'}
{c:'8001', d:'DE WATERKANT,Cape Town'}
{c:'8001', d:'DE WATERKANT,Kaapstad'}
{c:'6853', d:'DE WET'}
{c:'0251', d:'DE WILDT'}
{c:'7130', d:'DEACONVILLE,Macassar'}
{c:'6001', d:'DEAL PARTY,Port Elizabeth'}
{c:'9348', d:'DEALESVILLE'}
{c:'5604', d:'DEBE NEK'}
{c:'4681', d:'DEEMOUNT'}
{c:'2517', d:'DEEP SOUTH'}
{c:'3224', d:'DEEPDALE'}
{c:'1852', d:'DEEPMEADOW,Meadowlands'}
{c:'0852', d:'DEER PARK'}
{c:'0084', d:'DEERNESS,Pretoria'}
{c:'0002', d:'DEFENCE FORCE AREA,Pretoria'}
{c:'3201', d:'DEJERRING HEIGHTS,Pietermaritz'}
{c:'1609', d:'DEKLERKSHOF,Edenvale'}
{c:'1034', d:'DEL JUDOR EXT 1,Witbank'}
{c:'1044', d:'DEL JUDOR EXT 4'}
{c:'1034', d:'DEL JUDOR UIT 1,Witbank'}
{c:'1044', d:'DEL JUDOR UIT 4'}
{c:'1034', d:'DEL JUDOR,Witbank'}
{c:'7530', d:'DELAHAYE,Bellville'}
{c:'1709', d:'DELAREY,Florida'}
{c:'2770', d:'DELAREYVILLE'}
{c:'7102', d:'DELFT'}
{c:'7100', d:'DELFT'}
{c:'2312', d:'DELMAS'}
{c:'2313', d:'DELMAS'}
{c:'2311', d:'DELMAS'}
{c:'2210', d:'DELMAS'}
{c:'2310', d:'DELMAS'}
{c:'1403', d:'DELMENVILLE,Germiston'}
{c:'1401', d:'DELMENVILLE,Germiston'}
{c:'1404', d:'DELMORE,Germiston'}
{c:'1739', d:'DELPORTON,Krugersdorp'}
{c:'8377', d:'DELPORTSHOOP'}
{c:'7580', d:'DELROPARK,Kuils River'}
{c:'7580', d:'DELROPARK,Kuilsrivier'}
{c:'1401', d:'DELVILLE,Germiston'}
{c:'6529', d:'DELVILLE,Pacaltsdorp'}
{c:'4093', d:'DEMAT,Queensburgh'}
{c:'0715', d:'DENDRON'}
{c:'9412', d:'DENEYSVILLE'}
{c:'1401', d:'DENLEE,Germiston'}
{c:'0160', d:'DENNEBOOM'}
{c:'7646', d:'DENNEBURG,Paarl'}
{c:'7945', d:'DENNEDAL,Tokai'}
{c:'2196', d:'DENNEHOF,Johannesburg'}
{c:'7580', d:'DENNEMERE,Blackheath'}
{c:'6529', d:'DENNE-OORD,George'}
{c:'7601', d:'DENNESIG'}
{c:'7600', d:'DENNESIG'}
{c:'1055', d:'DENNESIG,Middelburg'}
{c:'1030', d:'DENNILTON'}
{c:'3837', d:'DENNY DALTON'}
{c:'2094', d:'DENVER'}
{c:'2027', d:'DENVER'}
{c:'8077', d:'DEPARTEMENT VAN ONDERWYS,Capem'}
{c:'8077', d:'DEPARTMENT OF EDUCATION,Capema'}
{c:'2820', d:'DERBY'}
{c:'2876', d:'DERDEPOORT'}
{c:'0035', d:'DERDEPOORTPARK'}
{c:'1569', d:'DERSLEY'}
{c:'1559', d:'DERSLEY'}
{c:'7580', d:'DES HAMPTON,Kuils River'}
{c:'7580', d:'DES HAMPTON,Kuilsrivier'}
{c:'4405', d:'DESAINAGAR'}
{c:'6220', d:'DESPATCH'}
{c:'6219', d:'DESPATCH'}
{c:'8001', d:'DEVIL`S PEAK,Cape Town'}
{c:'2260', d:'DEVON'}
{c:'7100', d:'DEVON PARK VILLAGE,Eerste Rive'}
{c:'7100', d:'DEVON PARK VILLAGE,Eersterivie'}
{c:'7100', d:'DEVON PARK,Eerste River'}
{c:'7100', d:'DEVON PARK,Eersterivier'}
{c:'7600', d:'DEVON VALLEY,Stellenbosch'}
{c:'7600', d:'DEVONVALLEI,Stellenbosch'}
{c:'1501', d:'DEWALT HATTINGHPARK,Benoni'}
{c:'9940', d:'DEWETSDORP'}
{c:'2198', d:'DEWETSHOF,Johannesburg'}
{c:'1401', d:'DEWITSRUS,Germiston'}
{c:'7490', d:'DF MALAN INDUSTRIÂ¿LE GEBIED,Ma'}
{c:'7490', d:'DF MALAN INDUSTRIAL AREA,Matro'}
{c:'8301', d:'DIAMANT PARK,Kimberley'}
{c:'9986', d:'DIAMANTHOOGTE,Koffiefontein'}
{c:'7397', d:'DIAZVILLE'}
{c:'7395', d:'DIAZVILLE'}
{c:'0457', d:'DIBASABOPHELO'}
{c:'8463', d:'DIBENG'}
{c:'0476', d:'DICHOEUNG'}
{c:'7975', d:'DIDO VALLEY,Simon`s Town'}
{c:'7975', d:'DIDOVALLEI,Simonstad'}
{c:'7600', d:'DIE BOORD,Stellenbosch'}
{c:'7140', d:'DIE BOS,Strand'}
{c:'1042', d:'DIE HEUWEL'}
{c:'0163', d:'DIE HOEWES,Pretoria'}
{c:'0126', d:'DIE TREMLOODS'}
{c:'0041', d:'DIE WILGERS'}
{c:'7130', d:'DIE WINGERD,Somerset West'}
{c:'7130', d:'DIE WINGERD,Somerset-Wes'}
{c:'7800', d:'DIEP RIVER'}
{c:'1862', d:'DIEPKLOOF'}
{c:'1864', d:'DIEPKLOOF EXT,Orlando'}
{c:'1804', d:'DIEPKLOOF EXT,Orlando'}
{c:'1804', d:'DIEPKLOOF HOSTEL,Orlando'}
{c:'1804', d:'DIEPKLOOF SONE 1 - 11,Orlando'}
{c:'1864', d:'DIEPKLOOF UIT,Orlando'}
{c:'1804', d:'DIEPKLOOF UIT,Orlando'}
{c:'1804', d:'DIEPKLOOF ZONE 1 - 11,Orlando'}
{c:'1864', d:'DIEPKLOOF,Orlando'}
{c:'1804', d:'DIEPKLOOF,Orlando'}
{c:'7800', d:'DIEPRIVIER'}
{c:'2560', d:'DIFATENG'}
{c:'2556', d:'DIJONG'}
{c:'9872', d:'DIKGAKENG'}
{c:'0721', d:'DIKGALE'}
{c:'0722', d:'DIMAMOTSA'}
{c:'5671', d:'DIMBAZA'}
{c:'8445', d:'DINGLETON'}
{c:'2868', d:'DINOKANA'}
{c:'1405', d:'DINWIDDIE,Germiston'}
{c:'1401', d:'DINWIDDIE,Germiston'}
{c:'2746', d:'DISANENG'}
{c:'1709', d:'DISCOVERY EXT 11,Florida'}
{c:'1709', d:'DISCOVERY UIT 11,Florida'}
{c:'1709', d:'DISCOVERY,Florida'}
{c:'8325', d:'DISKOBOLOS'}
{c:'1739', d:'DISTRIKDORP,Krugersdorp'}
{c:'8478', d:'DITHAKWANENG'}
{c:'1770', d:'DLALELANI'}
{c:'1818', d:'DLAMINI EXT 1,Tshiawelo'}
{c:'1818', d:'DLAMINI EXT 10,Tshiawelo'}
{c:'1818', d:'DLAMINI EXT 2,Tshiawelo'}
{c:'1818', d:'DLAMINI EXT 3,Tshiawelo'}
{c:'1818', d:'DLAMINI EXT 4,Tshiawelo'}
{c:'1818', d:'DLAMINI EXT 5,Tshiawelo'}
{c:'1818', d:'DLAMINI EXT 6,Tshiawelo'}
{c:'1818', d:'DLAMINI EXT 7,Tshiawelo'}
{c:'1818', d:'DLAMINI EXT 8,Tshiawelo'}
{c:'1818', d:'DLAMINI EXT 9,Tshiawelo'}
{c:'1818', d:'DLAMINI UIT 1,Tshiawelo'}
{c:'1818', d:'DLAMINI UIT 10,Tshiawelo'}
{c:'1818', d:'DLAMINI UIT 2,Tshiawelo'}
{c:'1818', d:'DLAMINI UIT 3,Tshiawelo'}
{c:'1818', d:'DLAMINI UIT 4,Tshiawelo'}
{c:'1818', d:'DLAMINI UIT 5,Tshiawelo'}
{c:'1818', d:'DLAMINI UIT 6,Tshiawelo'}
{c:'1818', d:'DLAMINI UIT 7,Tshiawelo'}
{c:'1818', d:'DLAMINI UIT 8,Tshiawelo'}
{c:'1818', d:'DLAMINI UIT 9,Tshiawelo'}
{c:'1818', d:'DLAMINI,Tshiawelo'}
{c:'3274', d:'DLOLWANA'}
{c:'1865', d:'DOBSONVILLE'}
{c:'1863', d:'DOBSONVILLE'}
{c:'1863', d:'DOBSONVILLE EXT 2,Dobsonville'}
{c:'1863', d:'DOBSONVILLE EXT,Dobsonville'}
{c:'1863', d:'DOBSONVILLE UIT 2,Dobsonville'}
{c:'1863', d:'DOBSONVILLE UIT,Dobsonville'}
{c:'2578', d:'DOMINIONVILLE'}
{c:'3237', d:'DONNYBROOK'}
{c:'4126', d:'DOON HEIGHTS,Amanzimtoti'}
{c:'4135', d:'DOONSIDE'}
{c:'4126', d:'DOONSIDE'}
{c:'7530', d:'DOOR-DE-KRAAL,Bellville'}
{c:'7800', d:'DOORDRIFT,Constantia'}
{c:'9459', d:'DOORN,Welkom'}
{c:'2094', d:'DOORNFONTEIN'}
{c:'2028', d:'DOORNFONTEIN'}
{c:'2094', d:'DOORNFONTEIN NORTH,Johannesbur'}
{c:'2094', d:'DOORNFONTEIN-NOORD,Johannesbur'}
{c:'7310', d:'DOORNKLOOF,Moorreesburg'}
{c:'4453', d:'DOORNKOP'}
{c:'1723', d:'DOORNKOP'}
{c:'0017', d:'DOORNPARK,Doornpoort'}
{c:'0017', d:'DOORNPOORT'}
{c:'0182', d:'DORANDIA'}
{c:'0182', d:'DORANDIA EXT 10'}
{c:'0182', d:'DORANDIA EXT 11'}
{c:'0182', d:'DORANDIA UIT 10'}
{c:'0182', d:'DORANDIA UIT 11'}
{c:'0188', d:'DORANDIA,Pretoria'}
{c:'6622', d:'DORBANK'}
{c:'5247', d:'DORCHESTER HEIGHTS,East London'}
{c:'5247', d:'DORCHESTER HEIGHTS,Oos-Londen'}
{c:'5435', d:'DORDRECHT'}
{c:'2090', d:'DORELAN,Johannesburg'}
{c:'7130', d:'DORHILL,Somerset West'}
{c:'7130', d:'DORHILL,Somerset-Wes'}
{c:'8151', d:'DORING BAY'}
{c:'8151', d:'DORINGBAAI'}
{c:'8137', d:'DORINGBOS'}
{c:'0157', d:'DORINGKLOOF,Lyttleton'}
{c:'2576', d:'DORINGKRUIN'}
{c:'2827', d:'DORINGPOORT'}
{c:'4091', d:'DORMERTON'}
{c:'4015', d:'DORMERTON'}
{c:'6705', d:'DORPSIG,Robertson'}
{c:'3206', d:'DORPSPRUIT'}
{c:'3201', d:'DORPSPRUIT'}
{c:'8730', d:'DOUGLAS'}
{c:'2055', d:'DOUGLASDALE EXT 13,Four Ways'}
{c:'2055', d:'DOUGLASDALE EXT 16,Four Ways'}
{c:'2055', d:'DOUGLASDALE EXT 24,Four Ways'}
{c:'2152', d:'DOUGLASDALE EXT 4,Sloane Park'}
{c:'2060', d:'DOUGLASDALE EXT 9,Cramerview'}
{c:'2055', d:'DOUGLASDALE UIT 13,Four Ways'}
{c:'2055', d:'DOUGLASDALE UIT 16,Four Ways'}
{c:'2055', d:'DOUGLASDALE UIT 24,Four Ways'}
{c:'2152', d:'DOUGLASDALE UIT 4,Sloane Park'}
{c:'2060', d:'DOUGLASDALE UIT 9,Cramerview'}
{c:'2021', d:'DOUGLASDALE,Bryanston'}
{c:'3610', d:'DOVEHOUSE,Gillitts'}
{c:'1609', d:'DOWERGLEN EXT 1,Germiston'}
{c:'1609', d:'DOWERGLEN EXT 2,Germiston'}
{c:'1609', d:'DOWERGLEN EXT 3,Germiston'}
{c:'1609', d:'DOWERGLEN EXT 4,Germiston'}
{c:'1609', d:'DOWERGLEN EXT 5,Germiston'}
{c:'1609', d:'DOWERGLEN UIT 1,Germiston'}
{c:'1609', d:'DOWERGLEN UIT 2,Germiston'}
{c:'1609', d:'DOWERGLEN UIT 3,Germiston'}
{c:'1609', d:'DOWERGLEN UIT 4,Germiston'}
{c:'1609', d:'DOWERGLEN UIT 5,Germiston'}
{c:'1609', d:'DOWERGLEN,Germiston'}
{c:'6059', d:'DOWERVILLE,Port Elizabeth'}
{c:'6229', d:'DR BRAUN,Uitenhage'}
{c:'1112', d:'DRAAIKRAAL'}
{c:'3331', d:'DRAGON PEAKS'}
{c:'3312', d:'DRAYCOTT'}
{c:'6741', d:'DREW'}
{c:'7945', d:'DREYERSDAL,Bergvliet'}
{c:'1935', d:'DRIE RIVIERE'}
{c:'1929', d:'DRIE RIVIERE'}
{c:'1941', d:'DRIE RIVIERE-OOS'}
{c:'8001', d:'DRIEANKERBAAI,Kaapstad'}
{c:'1459', d:'DRIEFONTEIN,Boksburg'}
{c:'2194', d:'DRIEFONTEIN,Randburg'}
{c:'1401', d:'DRIEHOEK,Germiston'}
{c:'1129', d:'DRIEKOP'}
{c:'6001', d:'DRIFTSANDS,Port Elizabeth'}
{c:'5417', d:'DRIVERSDRIFT'}
{c:'6672', d:'DROÂ¿VLAKTE'}
{c:'6822', d:'DROSTDY'}
{c:'7580', d:'DROSTDY PARK,Kuils River'}
{c:'7580', d:'DROSTDY PARK,Kuilsrivier'}
{c:'2094', d:'DROSTE PARK,Johannesburg'}
{c:'7764', d:'DRUIWEVLEI,Manenberg'}
{c:'7945', d:'DRUMBLAIR,Tokai'}
{c:'3660', d:'DRUMMOND,Botha`s Hill'}
{c:'9311', d:'DRUSANA'}
{c:'8588', d:'DRYHARTS'}
{c:'7600', d:'DU TOIT,Stellenbosch'}
{c:'1852', d:'DUBE'}
{c:'1800', d:'DUBE'}
{c:'1852', d:'DUBE VILLAGE,Meadowlands'}
{c:'1496', d:'DUDUZA'}
{c:'1494', d:'DUDUZA'}
{c:'4051', d:'DUFF`S ROAD,Durban North'}
{c:'2740', d:'DUFFIELD,Lichtenburg'}
{c:'4051', d:'DUFFWEG,Durban-Noord'}
{c:'7764', d:'DUINEFONTEIN,Manenberg'}
{c:'7140', d:'DUINENDAL,Strand'}
{c:'0835', d:'DUIWELSKLOOF'}
{c:'8001', d:'DUIWELSKOP,Kaapstad'}
{c:'9752', d:'DUKATHOLE'}
{c:'9750', d:'DUKATHOLE'}
{c:'1110', d:'DULLSTROOM'}
{c:'1939', d:'DUNCANVILLE,Vereeniging'}
{c:'3000', d:'DUNDEE'}
{c:'2336', d:'DUNDONALD'}
{c:'2192', d:'DUNHILL,Johannesburg'}
{c:'2196', d:'DUNKELD WEST,Johannesburg'}
{c:'2196', d:'DUNKELD,Johannesburg'}
{c:'1459', d:'DUNMADELEY,Boksburg'}
{c:'1590', d:'DUNNOTTAR'}
{c:'1496', d:'DUNNOTTAR'}
{c:'2090', d:'DUNSEVERN,Johannesburg'}
{c:'1508', d:'DUNSWART'}
{c:'1501', d:'DUNSWART'}
{c:'1609', d:'DUNVEGAN,Edenvale'}
{c:'3201', d:'DUNVERIA,Pietermaritzburg'}
{c:'4001', d:'DURBAN'}
{c:'4000', d:'DURBAN'}
{c:'1724', d:'DURBAN DEEP,Roodepoort'}
{c:'4029', d:'DURBAN INTERNASIONALE LUGHAWE'}
{c:'4029', d:'DURBAN INTERNATIONAL AIRPORT'}
{c:'4051', d:'DURBAN NORTH'}
{c:'4016', d:'DURBAN NORTH'}
{c:'7550', d:'DURBAN VILLAS,Durbanville'}
{c:'4051', d:'DURBAN-NOORD'}
{c:'4016', d:'DURBAN-NOORD'}
{c:'7551', d:'DURBANVILLE'}
{c:'7550', d:'DURBANVILLE'}
{c:'7550', d:'DURBANVILLE EXT 13,Durbanville'}
{c:'7550', d:'DURBANVILLE HILLS,Durbanville'}
{c:'7550', d:'DURBANVILLE UIT 13,Durbanville'}
{c:'7550', d:'DURBELL,Durbanville'}
{c:'3082', d:'DURNACOL'}
{c:'7491', d:'DURRHEIM'}
{c:'7490', d:'DURRHEIM'}
{c:'2149', d:'DUXBERRY,River Club'}
{c:'7441', d:'DUYNEFONTEIN,Melkbosstrand'}
{c:'0319', d:'DWAALBOOM'}
{c:'0812', d:'DWARS RIVER'}
{c:'0812', d:'DWARSRIVIER'}
{c:'4247', d:'DWESHULA'}
{c:'8805', d:'DYASONSKLIP'}
{c:'6628', d:'DYSSELSDORP'}
{c:'0955', d:'DZANANI'}
{c:'0975', d:'DZIMAULI'}
{c:'0833', d:'DZUMERI'}
{c:'4037', d:'EARLSFIELD,Durban'}
{c:'2090', d:'EAST BANK,Johannesburg'}
{c:'4018', d:'EAST END,Durban'}
{c:'1459', d:'EAST FIELD,Boksburg'}
{c:'5201', d:'EAST LONDON'}
{c:'5200', d:'EAST LONDON'}
{c:'0186', d:'EAST LYNNE,Pretoria'}
{c:'1754', d:'EAST PARK,Kagiso'}
{c:'4093', d:'EAST QUEENSBURGH,Queensburgh'}
{c:'1462', d:'EAST RAND'}
{c:'1459', d:'EAST RAND'}
{c:'7550', d:'EAST ROCK,Durbanville'}
{c:'2195', d:'EAST TOWN,Johannesburg'}
{c:'1459', d:'EAST VILLAGE,Boksburg'}
{c:'4068', d:'EASTBURY,Phoenix'}
{c:'7200', d:'EASTCLIFF,Hermanus'}
{c:'2190', d:'EASTCLIFF,Johannesburg'}
{c:'1055', d:'EASTDENE,Middelburg'}
{c:'6529', d:'EASTERN EXTENTION,George'}
{c:'1739', d:'EASTERN EXTENTION,Krugersdorp'}
{c:'1475', d:'EASTFIELD,Rusloo'}
{c:'2103', d:'EASTGATE'}
{c:'2148', d:'EASTGATE EXT 11,Wendywood'}
{c:'2148', d:'EASTGATE EXT 12,Wendywood'}
{c:'2148', d:'EASTGATE EXT 13,Wendywood'}
{c:'2148', d:'EASTGATE EXT 3,Wendywood'}
{c:'2148', d:'EASTGATE EXT 4,Wendywood'}
{c:'2148', d:'EASTGATE EXT 6,Wendywood'}
{c:'2148', d:'EASTGATE EXT 8,Wendywood'}
{c:'2148', d:'EASTGATE EXT 9,Wendywood'}
{c:'2148', d:'EASTGATE UIT 11,Wendywood'}
{c:'2148', d:'EASTGATE UIT 12,Wendywood'}
{c:'2148', d:'EASTGATE UIT 13,Wendywood'}
{c:'2148', d:'EASTGATE UIT 3,Wendywood'}
{c:'2148', d:'EASTGATE UIT 4,Wendywood'}
{c:'2148', d:'EASTGATE UIT 6,Wendywood'}
{c:'2148', d:'EASTGATE UIT 8,Wendywood'}
{c:'2148', d:'EASTGATE UIT 9,Wendywood'}
{c:'7945', d:'EASTLAKE ISLAND,Muizenberg'}
{c:'7945', d:'EASTLAKE VILLAGE,Muizenberg'}
{c:'7945', d:'EASTLAKE,Muizenberg'}
{c:'1609', d:'EASTLEIGH,Edenvale'}
{c:'7785', d:'EASTRIDGE,Mitchells Plain'}
{c:'1559', d:'EASTVALE,Springs'}
{c:'3241', d:'EASTWOLDS'}
{c:'3201', d:'EASTWOOD,Pietermaritzburg'}
{c:'8149', d:'EBENHAESER'}
{c:'1559', d:'EDELWEISS EXT 1,Springs'}
{c:'1559', d:'EDELWEISS EXT,Springs'}
{c:'1559', d:'EDELWEISS UIT 1,Springs'}
{c:'1559', d:'EDELWEISS UIT,Springs'}
{c:'1577', d:'EDELWEISS,Germiston'}
{c:'1559', d:'EDELWEISS,Springs'}
{c:'1613', d:'EDEN GLEN'}
{c:'1615', d:'EDEN GLEN EXT'}
{c:'1609', d:'EDEN GLEN EXT 1,Edenvale'}
{c:'1609', d:'EDEN GLEN EXT 15,Edenvale'}
{c:'1609', d:'EDEN GLEN EXT 18,Edenvale'}
{c:'1609', d:'EDEN GLEN EXT 19,Edenvale'}
{c:'1609', d:'EDEN GLEN EXT 6,Edenvale'}
{c:'1615', d:'EDEN GLEN UIT'}
{c:'1609', d:'EDEN GLEN UIT 1,Edenvale'}
{c:'1609', d:'EDEN GLEN UIT 15,Edenvale'}
{c:'1609', d:'EDEN GLEN UIT 18,Edenvale'}
{c:'1609', d:'EDEN GLEN UIT 19,Edenvale'}
{c:'1609', d:'EDEN GLEN UIT 6,Edenvale'}
{c:'1609', d:'EDEN GLEN,Edenvale'}
{c:'1458', d:'EDEN PARK'}
{c:'1455', d:'EDEN PARK'}
{c:'1458', d:'EDEN PARK EXT 1,Eden Park'}
{c:'1458', d:'EDEN PARK UIT 1,Eden Park'}
{c:'7560', d:'EDEN PARK,Brackenfell'}
{c:'9908', d:'EDENBURG'}
{c:'7700', d:'EDENBURGH,Claremont'}
{c:'1609', d:'EDENDALE,Edenvale'}
{c:'3217', d:'EDENDALE,Natal'}
{c:'1609', d:'EDENHILL,Edenvale'}
{c:'1610', d:'EDENVALE'}
{c:'1609', d:'EDENVALE'}
{c:'9535', d:'EDENVILLE'}
{c:'7441', d:'EDGEMEAD'}
{c:'7407', d:'EDGEMEAD'}
{c:'1625', d:'EDLEEN'}
{c:'1619', d:'EDLEEN'}
{c:'7785', d:'EDMARILS HILL,Mitchells Plain'}
{c:'0699', d:'EDUAN PARK,Pietersburg'}
{c:'7335', d:'EENDEKUIL'}
{c:'2266', d:'EENDRAG'}
{c:'7103', d:'EERSTE RIVER'}
{c:'7100', d:'EERSTE RIVER'}
{c:'0701', d:'EERSTEGOUD'}
{c:'9466', d:'EERSTEMYN'}
{c:'9459', d:'EERSTEMYN'}
{c:'7103', d:'EERSTERIVIER'}
{c:'7100', d:'EERSTERIVIER'}
{c:'0022', d:'EERSTERUS EXT 6,Eersterus'}
{c:'0022', d:'EERSTERUS UIT 6,Eersterus'}
{c:'0022', d:'EERSTERUS,Eersterus'}
{c:'0021', d:'EERSTERUS,Eersterus'}
{c:'4051', d:'EFFINGHAM HEIGHTS,Durban'}
{c:'3972', d:'EGAGASINI'}
{c:'9312', d:'EHRLICHPARK'}
{c:'9301', d:'EHRLICHPARK'}
{c:'7530', d:'EIKENBOSCH,Bellville'}
{c:'7570', d:'EIKENDAL,Kraaifontein'}
{c:'1872', d:'EIKENHOF'}
{c:'1759', d:'EIKEPARK,Randfontein'}
{c:'7100', d:'EINDHOVEN,Eerste River'}
{c:'7100', d:'EINDHOVEN,Eersterivier'}
{c:'1021', d:'EKANGALA'}
{c:'0186', d:'EKKLESIA,Pretoria'}
{c:'8284', d:'EKSTEENFONTEIN'}
{c:'7784', d:'EKUPHUMLENI,Khayelitsha'}
{c:'3020', d:'EKWENDENI,Pomeroy'}
{c:'2571', d:'ELANDIA,Klerksdorp'}
{c:'9499', d:'ELANDIA,Kroonstad'}
{c:'8110', d:'ELANDS BAY'}
{c:'8110', d:'ELANDSBAAI'}
{c:'1406', d:'ELANDSFONTEIN'}
{c:'1401', d:'ELANDSFONTEIN RAIL,Elandsfonte'}
{c:'1401', d:'ELANDSFONTEIN SPOOR,Elandsfont'}
{c:'2508', d:'ELANDSGOUD'}
{c:'1401', d:'ELANDSHAVEN,Germiston'}
{c:'2571', d:'ELANDSHEUWEL,Klerksdorp'}
{c:'1208', d:'ELANDSHOEK'}
{c:'3226', d:'ELANDSKOP'}
{c:'3017', d:'ELANDSKRAAL'}
{c:'2900', d:'ELANDSLAAGTE'}
{c:'2197', d:'ELANDSPARK,Johannesburg'}
{c:'0183', d:'ELANDSPOORT,Pretoria'}
{c:'0032', d:'ELANDSPOORT,Pretoria'}
{c:'0250', d:'ELANDSRAND,Brits'}
{c:'0047', d:'ELARDUSPARK'}
{c:'0181', d:'ELARDUSPARK EXT 1,Pretoria'}
{c:'0181', d:'ELARDUSPARK EXT 2,Pretoria'}
{c:'0181', d:'ELARDUSPARK EXT 3,Pretoria'}
{c:'0181', d:'ELARDUSPARK EXT 4,Pretoria'}
{c:'0181', d:'ELARDUSPARK EXT 5,Pretoria'}
{c:'0181', d:'ELARDUSPARK EXT 6,Pretoria'}
{c:'0181', d:'ELARDUSPARK UIT 1,Pretoria'}
{c:'0181', d:'ELARDUSPARK UIT 2,Pretoria'}
{c:'0181', d:'ELARDUSPARK UIT 3,Pretoria'}
{c:'0181', d:'ELARDUSPARK UIT 4,Pretoria'}
{c:'0181', d:'ELARDUSPARK UIT 5,Pretoria'}
{c:'0181', d:'ELARDUSPARK UIT 6,Pretoria'}
{c:'0181', d:'ELARDUSPARK,Pretoria'}
{c:'2094', d:'ELCEDES,Johannesburg'}
{c:'1813', d:'ELDORADOPARK'}
{c:'1811', d:'ELDORADOPARK'}
{c:'1811', d:'ELDORADOPARK EXT 1,Eldoradopar'}
{c:'1811', d:'ELDORADOPARK EXT 2,Eldoradopar'}
{c:'1811', d:'ELDORADOPARK EXT 3,Eldoradopar'}
{c:'1811', d:'ELDORADOPARK EXT 4,Eldoradopar'}
{c:'1811', d:'ELDORADOPARK EXT 5,Eldoradopar'}
{c:'1811', d:'ELDORADOPARK EXT 6,Eldoradopar'}
{c:'1811', d:'ELDORADOPARK EXT 7,Eldoradopar'}
{c:'1811', d:'ELDORADOPARK EXT 8,Eldoradopar'}
{c:'1811', d:'ELDORADOPARK EXT 9,Eldoradopar'}
{c:'1811', d:'ELDORADOPARK EXT,Eldoradopark'}
{c:'1811', d:'ELDORADOPARK UIT 1,Eldoradopar'}
{c:'1811', d:'ELDORADOPARK UIT 2,Eldoradopar'}
{c:'1811', d:'ELDORADOPARK UIT 3,Eldoradopar'}
{c:'1811', d:'ELDORADOPARK UIT 4,Eldoradopar'}
{c:'1811', d:'ELDORADOPARK UIT 5,Eldoradopar'}
{c:'1811', d:'ELDORADOPARK UIT 6,Eldoradopar'}
{c:'1811', d:'ELDORADOPARK UIT 7,Eldoradopar'}
{c:'1811', d:'ELDORADOPARK UIT 8,Eldoradopar'}
{c:'1811', d:'ELDORADOPARK UIT 9,Eldoradopar'}
{c:'1811', d:'ELDORADOPARK UIT,Eldoradopark'}
{c:'1811', d:'ELDORADOPARK,Eldoradopark'}
{c:'0157', d:'ELDORAIGNE EXT 1,Lyttleton'}
{c:'0157', d:'ELDORAIGNE EXT 11,Lyttleton'}
{c:'0157', d:'ELDORAIGNE EXT 3,Lyttleton'}
{c:'0157', d:'ELDORAIGNE EXT 6,Lyttleton'}
{c:'0157', d:'ELDORAIGNE UIT 1,Lyttleton'}
{c:'0157', d:'ELDORAIGNE UIT 11,Lyttleton'}
{c:'0157', d:'ELDORAIGNE UIT 3,Lyttleton'}
{c:'0157', d:'ELDORAIGNE UIT 6,Lyttleton'}
{c:'0157', d:'ELDORAIGNE,Lyttleton'}
{c:'8301', d:'ELECTRAPARK,Kimberley'}
{c:'7100', d:'ELECTRIC CITY,Eerste River'}
{c:'7100', d:'ELECTRIC CITY,Eersterivier'}
{c:'2197', d:'ELECTRON,Johannesburg'}
{c:'6109', d:'ELEPHANT PARK'}
{c:'7945', d:'ELFINDALE,Heathfield'}
{c:'7180', d:'ELGIN'}
{c:'7284', d:'ELIM'}
{c:'0960', d:'ELIM HOSPITAL'}
{c:'2197', d:'ELLADOONE,Johannesburg'}
{c:'2571', d:'ELLATON,Klerksdorp'}
{c:'5460', d:'ELLIOT'}
{c:'5070', d:'ELLIOTDALE'}
{c:'4051', d:'ELLIS PARK,Durban North'}
{c:'4051', d:'ELLIS PARK,Durban-Noord'}
{c:'2094', d:'ELLIS PARK,Johannesburg'}
{c:'0555', d:'ELLISRAS'}
{c:'1609', d:'ELMA PARK,Edenvale'}
{c:'0532', d:'ELMESTON'}
{c:'7490', d:'ELNOR,Matroosfontein'}
{c:'2211', d:'ELOFF'}
{c:'0084', d:'ELOFFSDAL,Pretoria'}
{c:'7791', d:'ELONWABENI'}
{c:'7646', d:'ELRICHT,Paarl'}
{c:'1428', d:'ELSBURG'}
{c:'1407', d:'ELSBURG'}
{c:'7607', d:'ELSENBURG'}
{c:'7490', d:'ELSIE`S RIVER'}
{c:'7480', d:'ELSIE`S RIVER'}
{c:'2094', d:'ELSIESHOF,Johannesburg'}
{c:'7490', d:'ELSIESRIVIER'}
{c:'7480', d:'ELSIESRIVIER'}
{c:'1428', d:'ELSPARK'}
{c:'1418', d:'ELSPARK'}
{c:'0920', d:'ELTI VILLAS,Louis Trichardt'}
{c:'2196', d:'ELTONHILL,Johannesburg'}
{c:'8301', d:'ELTORO PARK,Kimberley'}
{c:'6200', d:'ELUNDINI,Port Elizabeth'}
{c:'7780', d:'ELWYN PARK,Lansdowne'}
{c:'3610', d:'EMBERTON,Gillitts'}
{c:'1868', d:'EMDENI EXT,kwaXuma'}
{c:'1868', d:'EMDENI NORTH,kwaXuma'}
{c:'1868', d:'EMDENI SOUTH,kwaXuma'}
{c:'1868', d:'EMDENI UIT,kwaXuma'}
{c:'1868', d:'EMDENI,kwaXuma'}
{c:'1868', d:'EMDENI-NOORD,kwaXuma'}
{c:'1868', d:'EMDENI-SUID,kwaXuma'}
{c:'6011', d:'EMERALD HILL'}
{c:'2195', d:'EMMARENTIA'}
{c:'2029', d:'EMMARENTIA'}
{c:'3880', d:'EMPANGELA,Empangeni'}
{c:'3910', d:'EMPANGENI'}
{c:'3880', d:'EMPANGENI'}
{c:'1574', d:'ENDICOTT'}
{c:'5050', d:'ENGCOBO'}
{c:'3250', d:'ENHLALAKAHLE,Greytown'}
{c:'3360', d:'ENKANYEZI,Colenso'}
{c:'0556', d:'ENKELBULT'}
{c:'1830', d:'ENNERDALE'}
{c:'1826', d:'ENNERDALE'}
{c:'1830', d:'ENNERDALE EXT 1'}
{c:'1830', d:'ENNERDALE EXT 10,Odin Park'}
{c:'1830', d:'ENNERDALE EXT 11,Odin Park'}
{c:'1830', d:'ENNERDALE EXT 12,Odin Park'}
{c:'1830', d:'ENNERDALE EXT 14,Odin Park'}
{c:'1830', d:'ENNERDALE EXT 2'}
{c:'1830', d:'ENNERDALE EXT 3,Odin Park'}
{c:'1830', d:'ENNERDALE EXT 5'}
{c:'1830', d:'ENNERDALE EXT 6,Odin Park'}
{c:'1830', d:'ENNERDALE EXT 8'}
{c:'1830', d:'ENNERDALE EXT 9'}
{c:'1830', d:'ENNERDALE UIT 1'}
{c:'1830', d:'ENNERDALE UIT 10,Odin Park'}
{c:'1830', d:'ENNERDALE UIT 11,Odin Park'}
{c:'1830', d:'ENNERDALE UIT 12,Odin Park'}
{c:'1830', d:'ENNERDALE UIT 14,Odin Park'}
{c:'1830', d:'ENNERDALE UIT 2'}
{c:'1830', d:'ENNERDALE UIT 3,Odin Park'}
{c:'1830', d:'ENNERDALE UIT 5'}
{c:'1830', d:'ENNERDALE UIT 6,Odin Park'}
{c:'1830', d:'ENNERDALE UIT 8'}
{c:'1830', d:'ENNERDALE UIT 9'}
{c:'6125', d:'ENON'}
{c:'0307', d:'ENTABENI'}
{c:'4804', d:'ENVIS'}
{c:'7475', d:'EPPINDUST'}
{c:'7490', d:'EPPING FOREST,Elsie`s River'}
{c:'7490', d:'EPPING FOREST,Elsiesrivier'}
{c:'7460', d:'EPPING INDUSTRIÂ¿LE GEBIED,Eppi'}
{c:'7460', d:'EPPING INDUSTRIAL AREA,Eppindu'}
{c:'2152', d:'EPSOM DOWNS,Sloane Park'}
{c:'3201', d:'EPSWORTH,Pietermaritzburg'}
{c:'0183', d:'ERASMIA'}
{c:'0023', d:'ERASMIA'}
{c:'0048', d:'ERASMUSKLOOF'}
{c:'0153', d:'ERASMUSKLOOF EXT 3'}
{c:'0153', d:'ERASMUSKLOOF UIT 3'}
{c:'0181', d:'ERASMUSRAND,Pretoria'}
{c:'6229', d:'ERIC DODD,Uitenhage'}
{c:'2353', d:'ERMELO'}
{c:'2354', d:'ERMELO'}
{c:'2351', d:'ERMELO'}
{c:'2352', d:'ERMELO'}
{c:'2357', d:'ERMELO'}
{c:'2370', d:'ERMELO'}
{c:'2355', d:'ERMELO'}
{c:'2356', d:'ERMELO'}
{c:'2336', d:'ERMELO'}
{c:'2337', d:'ERMELO'}
{c:'2333', d:'ERMELO'}
{c:'2334', d:'ERMELO'}
{c:'2341', d:'ERMELO'}
{c:'2350', d:'ERMELO'}
{c:'2339', d:'ERMELO'}
{c:'2340', d:'ERMELO'}
{c:'8301', d:'ERNESTVILLE,Kimberley'}
{c:'4093', d:'ESCOMBE,Queensburgh'}
{c:'3815', d:'ESHOWE'}
{c:'8551', d:'ESPAGSDRIF'}
{c:'6850', d:'ESSELEN PARK,Worcester'}
{c:'1626', d:'ESSELENPARK'}
{c:'6070', d:'ESSEXVALE,Port Elizabeth'}
{c:'2007', d:'ESSEXWOLD,Bedfordview'}
{c:'6970', d:'ESSOPVILLE,Beaufort West'}
{c:'6970', d:'ESSOPVILLE,Beaufort-Wes'}
{c:'6012', d:'ESTADEAL'}
{c:'2331', d:'ESTANCIA'}
{c:'3310', d:'ESTCOURT'}
{c:'1428', d:'ESTERA,Elsburg'}
{c:'1619', d:'ESTERPARK EXT 1,Kempton Park'}
{c:'1619', d:'ESTERPARK UIT 1,Kempton Park'}
{c:'1619', d:'ESTERPARK,Kempton Park'}
{c:'3740', d:'ESTON'}
{c:'9701', d:'EUREKA,Bethlehem'}
{c:'9744', d:'EUREKA,Burgersdorp'}
{c:'7490', d:'EUREKA,Elsie`s River'}
{c:'7490', d:'EUREKA,Elsiesrivier'}
{c:'2280', d:'EVANDER'}
{c:'2091', d:'EVANS PARK,Johannesburg'}
{c:'1984', d:'EVATON,Residensia'}
{c:'1459', d:'EVELEIGH,Boksburg'}
{c:'4340', d:'EVEREST HEIGHTS,Verulam'}
{c:'2351', d:'EVERESTPARK,Ermelo'}
{c:'7550', d:'EVERGLEN,Durbanville'}
{c:'7975', d:'EVERGREEN,Fish Hoek'}
{c:'7975', d:'EVERGREEN,Vishoek'}
{c:'7550', d:'EVERSDAL HEIGHTS,Durbanville'}
{c:'7550', d:'EVERSDAL,Durbanville'}
{c:'3610', d:'EVERTON,Gillitts'}
{c:'9760', d:'EXCELSIOR'}
{c:'2023', d:'EXCOM'}
{c:'9313', d:'EXTON ROAD,Bloemfontein'}
{c:'9313', d:'EXTONWEG,Bloemfontein'}
{c:'9890', d:'EZENZELENI,Warden'}
{c:'5326', d:'EZIBELENI'}
{c:'3976', d:'EZIMPISINI'}
{c:'8301', d:'FABRICIA,Kimberley'}
{c:'1739', d:'FACTORIA,Krugersdorp'}
{c:'7405', d:'FACTRETON,Maitland'}
{c:'0043', d:'FAERIE GLEN'}
{c:'0043', d:'FAERIE GLEN EXT 2,Faerie Glen'}
{c:'0043', d:'FAERIE GLEN UIT 2,Faerie Glen'}
{c:'7975', d:'FAERIE KNOWE,Fish Hoek'}
{c:'7975', d:'FAERIE KNOWE,Vishoek'}
{c:'0191', d:'FAFUNG'}
{c:'6229', d:'FAIRBRIDGE HEIGHTS,Uitenhage'}
{c:'7405', d:'FAIRBRIDGE,Maitland'}
{c:'7100', d:'FAIRDALE,Eerste River'}
{c:'7100', d:'FAIRDALE,Eersterivier'}
{c:'7500', d:'FAIRFIELD,Parow'}
{c:'2195', d:'FAIRLAND'}
{c:'2030', d:'FAIRLAND'}
{c:'3201', d:'FAIRMEAD,Pietermaritzburg'}
{c:'2192', d:'FAIRMOUNT RIDGE,Johannesburg'}
{c:'2192', d:'FAIRMOUNT,Johannesburg'}
{c:'7550', d:'FAIRTREES,Durbanville'}
{c:'2192', d:'FAIRVALE,Johannesburg'}
{c:'9786', d:'FAIRVIEW,Barkly East'}
{c:'9786', d:'FAIRVIEW,Barkly-Oos'}
{c:'9301', d:'FAIRVIEW,Bloemfontein'}
{c:'3880', d:'FAIRVIEW,Empangeni'}
{c:'0043', d:'FAIRVIEW,Faerie Glen'}
{c:'2094', d:'FAIRVIEW,Johannesburg'}
{c:'6070', d:'FAIRVIEW,Port Elizabeth'}
{c:'2196', d:'FAIRWAYS,Johannesburg'}
{c:'7800', d:'FAIRWAYS,Wynberg'}
{c:'2192', d:'FAIRWOOD,Johannesburg'}
{c:'6850', d:'FAIRYGLEN,Worcester'}
{c:'3610', d:'FALCON PARK,New Germany'}
{c:'1929', d:'FALCONRIDGE,Vereeniging'}
{c:'4094', d:'FALLODEN PARK,Durban'}
{c:'0699', d:'FAMO PARK,Pietersburg'}
{c:'3610', d:'FARNINGHAM RIDGE,Pinetown'}
{c:'1459', d:'FARRAR PARK,Boksburg'}
{c:'1518', d:'FARRARMERE'}
{c:'1501', d:'FARRARMERE EXT 21,Benoni'}
{c:'1501', d:'FARRARMERE UIT 21,Benoni'}
{c:'1501', d:'FARRARMERE,Benoni'}
{c:'4776', d:'FARVIEW'}
{c:'4002', d:'FASTMAIL FOTO,Durban'}
{c:'9430', d:'FAUNA PARK,OFS'}
{c:'0699', d:'FAUNA PARK,Pietersburg'}
{c:'9430', d:'FAUNA PARK,Virginia'}
{c:'9301', d:'FAUNA,Bloemfontein'}
{c:'9325', d:'FAUNASIG'}
{c:'9301', d:'FAUNASIG'}
{c:'7131', d:'FAURE'}
{c:'9978', d:'FAURESMITH'}
{c:'3238', d:'FAWN LEAS'}
{c:'3875', d:'FELIXTON'}
{c:'2192', d:'FELLSIDE,Johannesburg'}
{c:'6001', d:'FERGUSON,Port Elizabeth'}
{c:'2160', d:'FERNDALE'}
{c:'2194', d:'FERNDALE EXT 3,Randburg'}
{c:'2194', d:'FERNDALE EXT 6,Randburg'}
{c:'2194', d:'FERNDALE RIDGE,Randburg'}
{c:'2194', d:'FERNDALE UIT 3,Randburg'}
{c:'2194', d:'FERNDALE UIT 6,Randburg'}
{c:'7560', d:'FERNDALE,Brackenfell'}
{c:'2194', d:'FERNDALE,Randburg'}
''';

