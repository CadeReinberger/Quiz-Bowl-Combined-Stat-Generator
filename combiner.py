import pandas as pd
import requests
import itertools

#NOTICE THIS DOES HAVE A BUG WITH MULTIPLE PLAYERS OF THE SAME NAME. 
#DOESN'T KEEP TRACK OF TEAM. THIS SHOULD BE FIXED, BUT WORKS W/ CASUAL USE

_TOURNEY_KEY = 6755 #hsquizbowl number identifying the tourney
_WRITE_FILE = 'res.xlsx' #excel file to output to 

def fix_header(df):
    new_header = df.iloc[0]
    df = df[1:] 
    df.columns = new_header 
    return df

def get_dfs(TOURNEY_KEY):
    #URLS
    prelim_url ='https://hsquizbowl.org/db/tournaments/' + str(TOURNEY_KEY) + '/stats/prelims/individuals/'
    playoff_url = 'https://hsquizbowl.org/db/tournaments/' + str(TOURNEY_KEY) + '/stats/playoffs/individuals/'
    #Header to pretend to be a browser
    header = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.75 Safari/537.36",
                  "X-Requested-With": "XMLHttpRequest"}
    #get the prelims df
    prelim_request = requests.get(prelim_url, headers = header)
    prelims_df = fix_header(pd.read_html(prelim_request.text)[1])
    #get the playoffs df
    playoff_request = requests.get(playoff_url, headers = header)
    playoff_df = fix_header(pd.read_html(playoff_request.text)[1])
    #return the results
    return prelims_df, playoff_df

class player:
    def __init__(self, name, powers, tossups, negs, tossups_heard):
        self.name = name
        self.powers = powers
        self.tossups = tossups
        self.negs = negs
        self.tossups_heard = tossups_heard
        
    def add(self, other):
        assert(self.name == other.name)
        return player(self.name, 
                      self.powers + other.powers, 
                      self.tossups + other.tossups, 
                      self.negs + other.negs,
                      self.tossups_heard + other.tossups_heard)
    
    def zero_player(name):
        return player(name, 0, 0, 0, 0)
    
def get_players(df):
    players = []
    for index, row in df.iterrows():
        players.append(player(row['Player'],
                              row[15],
                              row[10],
                              row[-5],
                              int(row['TUH'])))
    return players

def get_combined_players_dict(TOURNEY_KEY):
    prelim_df, playoff_df = get_dfs(TOURNEY_KEY)
    prelim_players = get_players(prelim_df)
    playoff_players = get_players(playoff_df)
    all_players = itertools.chain(prelim_players, playoff_players)
    res_dict = {}
    for p in all_players:
        if not p.name in res_dict:
            res_dict[p.name] = player.zero_player(p.name)
        res_dict[p.name] = res_dict[p.name].add(p)
    return res_dict

class final_player:
    def __init__(self, p):
        self.name = p.name
        self.powers = p.powers
        self.tossups = p.tossups
        self.negs = p.negs
        self.tossups_heard = p.tossups_heard
        self.points = 15 * self.powers + 10 * self.tossups - 5 * self.negs
        self.ppttuh = self.points * 20 / self.tossups_heard

def get_combined_final_players(TOURNEY_KEY):
    #this is not optimally efficient, but fine in practice and a good checking point
    return [final_player(p) for p in get_combined_players_dict(TOURNEY_KEY).values()]

def get_combined_df(TOURNEY_KEY):
    fps = get_combined_final_players(TOURNEY_KEY)
    cdf_data = [(fp.name, fp.powers, fp.tossups, fp.negs, fp.tossups_heard, fp.points, fp.ppttuh) for fp in fps]
    cdf = pd.DataFrame(cdf_data, columns = ['Name', '15', '10', '-5', 'TUH', 'P', 'PPG'])
    #sort by final PPG
    cdf = cdf.sort_values(by = 'PPG', ascending = False)
    return cdf

def write_result(WRITE_FILE, TOURNEY_KEY):
    get_combined_df(TOURNEY_KEY).to_excel(WRITE_FILE)
    
           
write_result(_WRITE_FILE, _TOURNEY_KEY)   