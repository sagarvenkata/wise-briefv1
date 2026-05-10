-- Insert all 240 theme accounts
-- Handles stored without @ prefix

insert into theme_accounts (theme_id, twitter_handle) values

-- Theme 1: AI & Tech Disruption
(1, 'sama'), (1, 'karpathy'), (1, 'emollick'), (1, 'benedictevans'), (1, 'waitbutwhy'),
(1, 'xlr8harder'), (1, 'rowancheung'), (1, 'aibreakfast'), (1, 'MatthewBerman_'), (1, 'tsarnick'),
(1, 'GaryMarcus'), (1, 'AndrewNgAI'), (1, 'tegmark'), (1, 'fchollet'), (1, 'JeffDean'),
(1, 'hardmaru'), (1, 'AnthropicAI'), (1, 'StabilityAI'), (1, 'GoogleDeepMind'), (1, 'ylecun'),

-- Theme 2: Business Model Decoded
(2, 'TrungTPhan'), (2, 'therealzachpogrob'), (2, 'SahilBloom'), (2, 'george_mack'), (2, 'Julian'),
(2, 'BusinessMadeSimp'), (2, 'theSamParr'), (2, 'agazdecki'), (2, 'polina_marinova'), (2, 'youngmoneyblog'),
(2, 'Julian_Shapiro'), (2, 'StartupArchive_'), (2, 'AswathDamodaran'), (2, 'BenThompson'), (2, 'venturehacks'),
(2, 'jason'), (2, 'businessbarista'), (2, 'TechCrunch'), (2, 'semil'), (2, 'patrick_oshag'),

-- Theme 3: Sports
(3, 'ShamsCharania'), (3, 'wojespn'), (3, 'TheAthletic'), (3, 'BleacherReport'), (3, 'ringer'),
(3, 'NateBoyer37'), (3, 'darrenrovell'), (3, 'JeffPassan'), (3, 'MikeReiss'), (3, 'billbarnwell'),
(3, 'ESPNStatsInfo'), (3, 'FTSports'), (3, 'SportsCenter'), (3, 'ESPN'), (3, 'SkySportsNews'),
(3, 'BBCSport'), (3, 'SportingNews'), (3, 'PhilStella_FTN'), (3, 'FiveThirtyEight'), (3, 'dfishersports'),

-- Theme 4: Movies & Pop Culture
(4, 'scottmendelson'), (4, 'FilmUpdates'), (4, 'DiscussingFilm'), (4, 'culturaltutor'), (4, 'RexChapman'),
(4, 'ThePlaylist'), (4, 'deadline'), (4, 'THR'), (4, 'IndieWire'), (4, 'CinemaBlend'),
(4, 'FilmSchoolRejects'), (4, 'PopCultureDen'), (4, 'rottentomatoes'), (4, 'KassieHuang'), (4, 'PitchforkMedia'),
(4, 'Vulture'), (4, 'EW'), (4, 'Collider'), (4, 'AwardsCircuit'), (4, 'RogerEbert'),

-- Theme 5: History & Science
(5, 'historyhit'), (5, 'historyinmemes'), (5, 'StartupArchive_'), (5, 'Peter_Frankopan'), (5, 'adamjkucharski'),
(5, 'RealTimeWWII'), (5, 'Rainmaker1973'), (5, 'fermatslibrary'), (5, 'pickover'), (5, 'TodayInHistory'),
(5, 'GreatDismal'), (5, 'Amazing_Maps'), (5, 'weird_hist'), (5, 'wrathofgnon'), (5, 'weird_history'),
(5, 'historyrhymes'), (5, 'HistoryExtra'), (5, 'HistoryNeedsYou'), (5, 'todayinhistory'), (5, 'HistoryHit'),

-- Theme 6: War & Geopolitics
(6, 'ian_bremmer'), (6, 'georgefriedman'), (6, 'PeterZeihan'), (6, 'KofiBoateng_'), (6, 'RALEIGHdotWORLD'),
(6, 'RichardHaass'), (6, 'nktpnd'), (6, 'war_mapper'), (6, 'JominiW'), (6, 'MarkHertling'),
(6, 'EliotHiggins'), (6, 'McFaul'), (6, 'JulianRoepcke'), (6, 'conflictsw'), (6, 'MichaelKofman'),
(6, 'SamRamani'), (6, 'michaelh992'), (6, 'RobLee_FPRI'), (6, 'KoffiTchapgnouo'), (6, 'TrentTelenko'),

-- Theme 7: Human Psychology & Behaviour
(7, 'naval'), (7, 'jamesclear'), (7, 'hubermanlab'), (7, 'AdamMGrant'), (7, 'jonhaidt'),
(7, 'DanielPink'), (7, 'profbrianlittle'), (7, 'Dannykifer'), (7, 'AliAbdaal'), (7, 'RyanHoliday'),
(7, 'shankarvedantam'), (7, 'joerogan'), (7, 'BehaviourWorks'), (7, 'BehavioralScientist'), (7, 'PsychToday'),
(7, 'NeuroNeurotic'), (7, 'ProfSteveP'), (7, 'DrBrianNosek'), (7, 'ProfDavidClark'), (7, 'PaulBloom'),

-- Theme 8: Stock Market & Wealth (cleaned backslashes)
(8, 'morganhousel'), (8, 'patrick_oshag'), (8, 'ChrisBloomstran'), (8, 'TheStalwart'), (8, 'BrianFeroldi'),
(8, 'ReformedBroker'), (8, 'LizAnnSonders'), (8, 'charliebilello'), (8, 'visualizevalue'), (8, '10kdiver'),
(8, 'MikeZaccardi'), (8, 'PeterLBrandt'), (8, 'EddyElfenbein'), (8, 'awealthofcs'), (8, 'MebFaber'),
(8, 'jessefelder'), (8, 'OptionsHawk'), (8, 'MicroCapClub'), (8, 'Valuewalk'), (8, 'BarbarianCap'),

-- Theme 9: Climate & Energy
(9, 'hausfath'), (9, 'BillMcKibben'), (9, 'KetanJ_'), (9, 'jsborenstein'), (9, 'vatsal_manot'),
(9, 'EricHolthaus'), (9, 'DrShepherd2013'), (9, 'ProfLesley'), (9, 'ClimateAdam'), (9, 'GlobalEcoGuy'),
(9, 'JesseJenkins'), (9, 'Carbon_Brief'), (9, 'CleanTechnica'), (9, 'GlobalWindOrg'), (9, 'Solar_Quotes'),
(9, 'IEA'), (9, 'BloombergNEF'), (9, 'RMIorg'), (9, 'WoodMackenzie'), (9, 'wclimate'),

-- Theme 10: Consumer & Corporate
(10, 'matthewstoller'), (10, 'linaronchi'), (10, 'ProMarket_org'), (10, 'davidfaber'), (10, 'alexkantrowitz'),
(10, 'GlennKesslerWP'), (10, 'lisaabramowicz1'), (10, 'ritholtz'), (10, 'jasonzweigwsj'), (10, 'felix_salmon'),
(10, 'KaraSwisher'), (10, 'HarvardBiz'), (10, 'corpgov'), (10, 'OpenSecrets'), (10, 'propublica'),
(10, 'SecondMeasure'), (10, 'CorpGovResearch'), (10, 'TheMarkup'), (10, 'FoodPolitics'), (10, 'BenThompson'),

-- Theme 11: Cities & Infrastructure
(11, 'marketurbanism'), (11, 'StrongTowns'), (11, 'UrbanistOrg'), (11, 'AbtBoulder'), (11, 'SolomonNBCNews'),
(11, 'urbanize_la'), (11, 'brent_toderian'), (11, 'AlexisSabadell'), (11, 'PublicCityPlan'), (11, 'transportist'),
(11, 'neilturok'), (11, 'NextCity_org'), (11, 'citylab'), (11, 'citymonitor'), (11, 'CityBeautiful'),
(11, 'UrbanLandInst'), (11, 'SSCITweets'), (11, 'PedRochet'), (11, 'planetizen'), (11, 'urbanTLP'),

-- Theme 12: Food & Health
(12, 'PeterAttiaMD'), (12, 'foundmyfitness'), (12, 'MaxLugavere'), (12, 'Marion_Nestle'), (12, 'ChrisKresser'),
(12, 'davidludwigmd'), (12, 'DrRheauxman'), (12, 'DrMarkHyman'), (12, 'NutritionMadeS'), (12, 'michaelpollan'),
(12, 'UlrichKelber'), (12, 'chrispalmermd'), (12, 'ProfTimSpector'), (12, 'ZoeFoodPerson'), (12, 'GutMicrobiotaNews'),
(12, 'DrJoshAxe'), (12, 'NutritionFacts_org'), (12, 'Examine_com'), (12, 'RupaSubramanya'), (12, 'GidMK');
