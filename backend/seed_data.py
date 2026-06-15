"""Seed data for CourtVision AI: leagues, teams and sample fixtures.

This intentionally uses real-world league/team names so the platform feels
authentic out of the box. Stats here are reasonable league-average baselines
used by the prediction engine; when an API-SPORTS key is configured the
fetcher will overwrite/extend these.
"""

LEAGUES = [
    {"id": "nba", "name": "NBA", "country": "USA", "tier": 1, "logo": "🏀"},
    {"id": "wnba", "name": "WNBA", "country": "USA", "tier": 2, "logo": "🏀"},
    {"id": "euroleague", "name": "EuroLeague", "country": "Europe", "tier": 1, "logo": "🇪🇺"},
    {"id": "eurocup", "name": "EuroCup", "country": "Europe", "tier": 2, "logo": "🇪🇺"},
    {"id": "ncaa", "name": "NCAA Men's Basketball", "country": "USA", "tier": 2, "logo": "🎓"},
    {"id": "nbl_aus", "name": "NBL Australia", "country": "Australia", "tier": 2, "logo": "🇦🇺"},
    {"id": "cba", "name": "CBA China", "country": "China", "tier": 2, "logo": "🇨🇳"},
    {"id": "bbl", "name": "BBL Germany", "country": "Germany", "tier": 2, "logo": "🇩🇪"},
    {"id": "lnb", "name": "France Pro A", "country": "France", "tier": 2, "logo": "🇫🇷"},
    {"id": "lba", "name": "Italy Lega Basket", "country": "Italy", "tier": 2, "logo": "🇮🇹"},
    {"id": "acb", "name": "Spain ACB", "country": "Spain", "tier": 1, "logo": "🇪🇸"},
    {"id": "bsl", "name": "Turkey BSL", "country": "Turkey", "tier": 2, "logo": "🇹🇷"},
    {"id": "gbl", "name": "Greek Basket League", "country": "Greece", "tier": 2, "logo": "🇬🇷"},
    {"id": "jbl", "name": "Japan B.League", "country": "Japan", "tier": 2, "logo": "🇯🇵"},
    {"id": "pba", "name": "Philippines PBA", "country": "Philippines", "tier": 2, "logo": "🇵🇭"},
    {"id": "fiba", "name": "FIBA International", "country": "World", "tier": 1, "logo": "🌍"},
]

# Each team: id, league_id, name, short, city, off_rating, def_rating, pace, elo, form (last 5 W/L)
TEAMS = [
    # --- NBA ---
    ("bos", "nba", "Boston Celtics", "BOS", "Boston", 119.2, 110.5, 99.1, 1620, "WWWWL"),
    ("nyk", "nba", "New York Knicks", "NYK", "New York", 117.4, 112.3, 97.8, 1565, "WWLWW"),
    ("mil", "nba", "Milwaukee Bucks", "MIL", "Milwaukee", 118.8, 113.6, 100.2, 1555, "WLWWL"),
    ("cle", "nba", "Cleveland Cavaliers", "CLE", "Cleveland", 120.5, 109.8, 98.4, 1610, "WWWWW"),
    ("phi", "nba", "Philadelphia 76ers", "PHI", "Philadelphia", 114.8, 113.2, 98.0, 1490, "LLWLW"),
    ("mia", "nba", "Miami Heat", "MIA", "Miami", 113.6, 111.9, 96.5, 1505, "WLLWW"),
    ("orl", "nba", "Orlando Magic", "ORL", "Orlando", 110.4, 109.1, 96.8, 1495, "WWLLW"),
    ("ind", "nba", "Indiana Pacers", "IND", "Indianapolis", 119.6, 116.4, 102.3, 1530, "LWWWL"),
    ("atl", "nba", "Atlanta Hawks", "ATL", "Atlanta", 116.2, 117.0, 100.9, 1455, "LWLWL"),
    ("chi", "nba", "Chicago Bulls", "CHI", "Chicago", 113.5, 116.1, 99.4, 1430, "LLWWL"),
    ("tor", "nba", "Toronto Raptors", "TOR", "Toronto", 112.8, 116.5, 99.0, 1410, "LWLLW"),
    ("bkn", "nba", "Brooklyn Nets", "BKN", "Brooklyn", 110.3, 117.2, 98.5, 1380, "LLLWL"),
    ("det", "nba", "Detroit Pistons", "DET", "Detroit", 109.7, 119.3, 99.7, 1340, "LWLLL"),
    ("cha", "nba", "Charlotte Hornets", "CHA", "Charlotte", 108.6, 118.8, 100.1, 1335, "LLLWL"),
    ("wsh", "nba", "Washington Wizards", "WSH", "Washington", 109.2, 121.6, 100.8, 1305, "LLLLW"),
    ("okc", "nba", "Oklahoma City Thunder", "OKC", "Oklahoma City", 122.3, 108.6, 99.5, 1660, "WWWWW"),
    ("den", "nba", "Denver Nuggets", "DEN", "Denver", 119.8, 113.2, 97.6, 1595, "WWLWW"),
    ("min", "nba", "Minnesota Timberwolves", "MIN", "Minneapolis", 116.4, 110.2, 96.4, 1570, "WWWLW"),
    ("lac", "nba", "LA Clippers", "LAC", "Los Angeles", 117.2, 112.4, 97.5, 1545, "WWLWL"),
    ("dal", "nba", "Dallas Mavericks", "DAL", "Dallas", 118.6, 113.5, 98.7, 1535, "LWWWL"),
    ("phx", "nba", "Phoenix Suns", "PHX", "Phoenix", 116.9, 114.8, 99.3, 1510, "WLWWL"),
    ("lal", "nba", "Los Angeles Lakers", "LAL", "Los Angeles", 117.3, 114.6, 100.4, 1500, "WLWWL"),
    ("gsw", "nba", "Golden State Warriors", "GSW", "San Francisco", 117.8, 113.9, 100.2, 1525, "WWLWL"),
    ("sac", "nba", "Sacramento Kings", "SAC", "Sacramento", 115.3, 114.8, 100.5, 1470, "LWLWL"),
    ("mem", "nba", "Memphis Grizzlies", "MEM", "Memphis", 114.6, 115.2, 101.1, 1450, "WLLWL"),
    ("hou", "nba", "Houston Rockets", "HOU", "Houston", 113.9, 110.5, 99.6, 1480, "WWLWW"),
    ("nop", "nba", "New Orleans Pelicans", "NOP", "New Orleans", 113.1, 114.6, 99.8, 1440, "LWLWL"),
    ("sas", "nba", "San Antonio Spurs", "SAS", "San Antonio", 112.4, 116.2, 100.3, 1390, "LWLLW"),
    ("por", "nba", "Portland Trail Blazers", "POR", "Portland", 109.5, 116.8, 98.2, 1370, "LLWLL"),
    ("uta", "nba", "Utah Jazz", "UTA", "Salt Lake City", 110.8, 118.5, 100.6, 1355, "LLWLL"),
    # --- WNBA ---
    ("nyl", "wnba", "New York Liberty", "NYL", "New York", 108.5, 96.8, 80.2, 1610, "WWWLW"),
    ("lva", "wnba", "Las Vegas Aces", "LVA", "Las Vegas", 110.2, 98.4, 81.5, 1600, "WWWWL"),
    ("min_wn", "wnba", "Minnesota Lynx", "MIN", "Minneapolis", 105.6, 94.8, 79.6, 1580, "WLWWW"),
    ("con", "wnba", "Connecticut Sun", "CON", "Uncasville", 104.2, 97.3, 79.1, 1530, "WLLWW"),
    ("sea", "wnba", "Seattle Storm", "SEA", "Seattle", 103.6, 99.5, 80.8, 1490, "LWLWW"),
    ("ind_wn", "wnba", "Indiana Fever", "IND", "Indianapolis", 102.4, 102.6, 82.1, 1450, "WLWLL"),
    ("phx_wn", "wnba", "Phoenix Mercury", "PHX", "Phoenix", 101.8, 103.2, 81.4, 1430, "LWLLW"),
    ("chi_wn", "wnba", "Chicago Sky", "CHI", "Chicago", 99.4, 105.1, 81.0, 1380, "LLWLL"),
    # --- EuroLeague ---
    ("rma", "euroleague", "Real Madrid", "RMA", "Madrid", 112.4, 102.6, 73.5, 1645, "WWWLW"),
    ("pan", "euroleague", "Panathinaikos", "PAN", "Athens", 110.6, 103.8, 74.2, 1620, "WWLWW"),
    ("oly", "euroleague", "Olympiacos", "OLY", "Piraeus", 108.9, 100.5, 72.8, 1595, "WLWWW"),
    ("fbb", "euroleague", "Fenerbahce", "FBB", "Istanbul", 110.2, 102.9, 73.6, 1590, "WWWLL"),
    ("efs", "euroleague", "Anadolu Efes", "EFS", "Istanbul", 107.5, 105.1, 74.5, 1530, "LWWLW"),
    ("bar", "euroleague", "FC Barcelona", "BAR", "Barcelona", 109.4, 104.6, 73.9, 1560, "WLWLW"),
    ("mac", "euroleague", "Maccabi Tel Aviv", "MAC", "Tel Aviv", 106.8, 106.2, 75.1, 1500, "LWLWW"),
    ("zal", "euroleague", "Zalgiris Kaunas", "ZAL", "Kaunas", 105.3, 103.6, 73.2, 1485, "LWLWL"),
    ("vir", "euroleague", "Virtus Bologna", "VIR", "Bologna", 104.9, 105.4, 73.8, 1455, "LLWLW"),
    ("mil_el", "euroleague", "EA7 Milano", "MIL", "Milan", 103.6, 106.8, 74.6, 1440, "LLWLL"),
    # --- Spain ACB ---
    ("rma_acb", "acb", "Real Madrid", "RMA", "Madrid", 115.4, 103.2, 76.5, 1620, "WWLWW"),
    ("bar_acb", "acb", "FC Barcelona", "BAR", "Barcelona", 113.8, 104.5, 75.8, 1590, "WLWWL"),
    ("uni", "acb", "Unicaja Malaga", "UNI", "Malaga", 109.2, 102.4, 75.1, 1530, "WWLWW"),
    ("bas", "acb", "Baskonia", "BAS", "Vitoria", 108.6, 106.8, 76.3, 1490, "LWLWL"),
    # --- Italy LBA ---
    ("vir_lba", "lba", "Virtus Bologna", "VIR", "Bologna", 108.4, 103.6, 74.5, 1565, "WWLWW"),
    ("mil_lba", "lba", "EA7 Milano", "MIL", "Milan", 107.8, 104.9, 74.8, 1550, "WLWWL"),
    ("ven", "lba", "Reyer Venezia", "VEN", "Venice", 103.2, 106.5, 74.2, 1430, "LLWLW"),
    # --- BBL Germany ---
    ("alb", "bbl", "ALBA Berlin", "ALB", "Berlin", 110.6, 104.8, 78.4, 1545, "WWWLW"),
    ("bay", "bbl", "FC Bayern Munich", "BAY", "Munich", 109.8, 103.2, 77.6, 1555, "WLWWW"),
    ("ulm", "bbl", "Ratiopharm Ulm", "ULM", "Ulm", 105.3, 106.8, 78.9, 1450, "LWLWW"),
    # --- France Pro A ---
    ("mon", "lnb", "AS Monaco", "MON", "Monaco", 111.4, 102.5, 75.6, 1580, "WWWWL"),
    ("par", "lnb", "Paris Basketball", "PAR", "Paris", 108.6, 103.9, 76.2, 1520, "WLWWW"),
    ("asv", "lnb", "ASVEL", "ASV", "Villeurbanne", 106.8, 104.6, 75.4, 1500, "LWWLW"),
    # --- Turkey BSL ---
    ("fbb_bsl", "bsl", "Fenerbahce", "FBB", "Istanbul", 110.8, 102.3, 75.8, 1595, "WWLWW"),
    ("efs_bsl", "bsl", "Anadolu Efes", "EFS", "Istanbul", 109.5, 104.1, 76.2, 1560, "WLWWL"),
    # --- Greek Basket League ---
    ("pan_gbl", "gbl", "Panathinaikos", "PAN", "Athens", 111.6, 100.9, 74.8, 1620, "WWLWW"),
    ("oly_gbl", "gbl", "Olympiacos", "OLY", "Piraeus", 110.4, 101.6, 74.5, 1605, "WWWLW"),
    # --- NBL Australia ---
    ("syd", "nbl_aus", "Sydney Kings", "SYD", "Sydney", 109.8, 105.3, 92.4, 1540, "WWLWW"),
    ("mel", "nbl_aus", "Melbourne United", "MEL", "Melbourne", 108.6, 104.5, 91.8, 1525, "WLWWL"),
    ("per", "nbl_aus", "Perth Wildcats", "PER", "Perth", 107.4, 103.9, 91.2, 1545, "WWLWW"),
    # --- Japan B.League ---
    ("alv", "jbl", "Alvark Tokyo", "ALV", "Tokyo", 106.8, 102.4, 79.5, 1540, "WWLWW"),
    ("bre", "jbl", "Chiba Jets", "BRE", "Chiba", 105.4, 103.6, 80.1, 1525, "WLWWL"),
    # --- CBA China ---
    ("lia", "cba", "Liaoning Flying Leopards", "LIA", "Shenyang", 112.4, 105.6, 91.2, 1560, "WWWLW"),
    ("zhe", "cba", "Zhejiang Lions", "ZHE", "Hangzhou", 110.6, 106.8, 90.8, 1530, "WWLWW"),
    # --- Philippines PBA ---
    ("brm", "pba", "Barangay Ginebra", "BRM", "Manila", 104.6, 102.8, 88.5, 1520, "WLWWL"),
    ("trp", "pba", "TNT Tropang", "TRP", "Manila", 105.8, 103.4, 89.2, 1535, "WWLWW"),
    # --- NCAA ---
    ("duke", "ncaa", "Duke Blue Devils", "DUKE", "Durham", 116.4, 92.5, 67.8, 1640, "WWWWL"),
    ("kan", "ncaa", "Kansas Jayhawks", "KAN", "Lawrence", 114.8, 94.3, 68.4, 1615, "WWLWW"),
    ("unc", "ncaa", "UNC Tar Heels", "UNC", "Chapel Hill", 113.6, 95.1, 68.9, 1580, "WLWWW"),
    ("uk", "ncaa", "Kentucky Wildcats", "UK", "Lexington", 115.3, 93.8, 68.2, 1610, "WWWWW"),
    # --- EuroCup ---
    ("hap", "eurocup", "Hapoel Tel Aviv", "HAP", "Tel Aviv", 107.4, 102.6, 74.5, 1480, "WWLWW"),
    ("bou", "eurocup", "JL Bourg", "BOU", "Bourg-en-Bresse", 105.8, 104.3, 75.2, 1450, "WLWWW"),
    # --- FIBA International ---
    ("usa", "fiba", "USA National Team", "USA", "USA", 122.5, 95.4, 78.5, 1750, "WWWWW"),
    ("esp", "fiba", "Spain National Team", "ESP", "Spain", 110.8, 98.5, 76.8, 1620, "WWLWW"),
    ("fra", "fiba", "France National Team", "FRA", "France", 109.6, 99.2, 76.5, 1610, "WWWLW"),
    ("ser", "fiba", "Serbia National Team", "SER", "Serbia", 112.4, 100.6, 77.2, 1640, "WWLWW"),
]
