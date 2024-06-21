import streamlit as st
import pandas as pd

# Or, if the image is stored locally
st.image('data/cd_logo.png')

# Load the data
df_playerstats = pd.read_csv('data/playerStats.csv')
df_league = pd.read_csv('data/leagueTables.csv')
df_clubs = pd.read_csv('data/df_clubs.csv')
competitions = df_clubs['CompetitionID'].unique().tolist()
competitions = [comp for comp in competitions if comp != 'CL']
competitions = [comp for comp in competitions if comp != 'EL']
competitions = [comp for comp in competitions if comp != 'UCOL']


# Streamlit App
def main():
    st.title('Finanzcockpit')
    
    # User input features
    
    # Club
    st.subheader('Club')
    clubname = st.selectbox('Select your Club', df_clubs['ClubName'], format_func=lambda x: x.strip())
    filtered_df = df_clubs[df_clubs.ClubName == clubname]
    filtered_df = filtered_df.reset_index(drop=True)
    mainCompetition = filtered_df.at[0, 'CompetitionID']
    clubID = filtered_df.at[0, 'ClubID']
    
    # Position
    st.subheader('Position')
    position = st.selectbox(
    "Which of these options best describes the player's position?",
    ["Goalkeeper", "Defense", "Midfield", "Attack"]
    )
    
    ################################################################################
    #Market Value
    ################################################################################

    # Grouping by PlayerID and Season
    df_StatsAll = df_playerstats[(df_playerstats.CompetitionID == mainCompetition) & (df_playerstats.Position==position)]

    # Calculate the quartile values
    quartiles = df_StatsAll['MarketValue'].quantile([0.25, 0.5, 0.75]).round(0)

    # Create labels for the quartiles
    labels = [f"{int(df_StatsAll['MarketValue'].min()):.0f} - {int(quartiles[0.25]):.0f}",
                f"{int(quartiles[0.25]):.0f} - {int(quartiles[0.5]):.0f}",
                f"{int(quartiles[0.5]):.0f} - {int(quartiles[0.75]):.0f}",
                f"{int(quartiles[0.75]):.0f} - {int(df_StatsAll['MarketValue'].max()):.0f}"]

    # Create a new column to store the quartile categories
    df_StatsAll['Quartile'] = pd.qcut(df_StatsAll['MarketValue'], q=4, labels=labels)

    # Create the dictionary
    quartile_dict = {label: df_StatsAll[df_StatsAll['Quartile'] == label] for label in labels}

    st.subheader('Market Value')
    # Dropdown to select an option from the dictionary keys
    selected_option = st.selectbox(
        "Choose the range where your player's market value falls (defined by the 25%, 50%, 75% quartile borders of the Market Values according to the position and the league in which the selected club competes, over the last 5 seasons):",
        list(quartile_dict.keys())
    )

    ###########################################################################
    # MainStats Function to process the selected option and display the table
    ###########################################################################
    def display_player_stats_main_competitions(selected_option, quartile_dict, df_playerstats):
        # Get the player IDs from the selected option
        playerIds = quartile_dict[selected_option]['PlayerID'].unique().tolist()
        
        # Filter the df_playerstats DataFrame
        df_StatsMain = df_playerstats[(df_playerstats['PlayerID'].isin(playerIds)) & (df_playerstats['CompetitionID']==mainCompetition)].reset_index(drop=True)
        
        # Group by PlayerID and Season, then sum the values
        df_StatsMain = df_StatsMain[['PlayerID', 'Season', 'Goals', 'Assists', 'ScorerPoints', 'MinutesPlayed', 'Appearances']].groupby(by=['PlayerID', 'Season']).sum()
        
        # Calculate the mean and round the results
        df_meanMain = df_StatsMain.mean().round(1)
        
        return df_meanMain
    
    ###########################################################################
    # ALLStats Function to process the selected option and display the table
    ###########################################################################
    def display_player_stats_all_competitions(selected_option, quartile_dict, df_playerstats, competitions):
        
        # Remove the string equal to mainCompetition from the list competitions
        competitions_filter = [comp for comp in competitions if comp != mainCompetition]

        # Get the player IDs from the selected option
        playerIds = quartile_dict[selected_option]['PlayerID'].unique().tolist()
        
        # Filter the df_playerstats DataFrame
        df_StatsAll = df_playerstats[df_playerstats['PlayerID'].isin(playerIds)].reset_index(drop=True)
        df_StatsAll = df_StatsAll[~df_StatsAll['CompetitionID'].isin(competitions_filter)]
        
        # Group by PlayerID and Season, then sum the values
        df_StatsAll = df_StatsAll[['PlayerID', 'Season', 'Goals', 'Assists', 'ScorerPoints', 'MinutesPlayed', 'Appearances']].groupby(by=['PlayerID', 'Season']).sum()
        
        # Calculate the mean and round the results
        df_meanAll = df_StatsAll.mean().round(1)
        
        return df_meanAll
    

    # Display the table if an option is selected
    if selected_option:
        
        st.subheader('Stats')
        
        ###########################
        #Main
        st.subheader('Main Competition')
        st.write("Statistics per Season for selected market value range across **main competitions**:")
        stats_table_main = display_player_stats_main_competitions(selected_option,quartile_dict, df_playerstats)
        
        # Rename the index for display
        stats_table_main = stats_table_main.to_frame().T
        stats_table_main.index = ['Stats']
        
        # Customize the column names
        stats_table_main.columns = ['Goals', 'Assists', 'Scorer Points', 'Minutes Played', 'Appearances']
        
        # Format the DataFrame
        stats_table_main = stats_table_main.style.format(precision=1)
        
        st.table(stats_table_main)
        
        ###########################
        #All
        st.subheader('All Competitions')
        st.write("Statistics per Season for selected market value range across **all club competitions** (national league, cups, european cups, no data from national competitions):")
        stats_table_all = display_player_stats_all_competitions(selected_option,quartile_dict, df_playerstats, competitions)
        
        # Rename the index for display
        stats_table_all = stats_table_all.to_frame().T
        stats_table_all.index = ['Stats']
        
        # Customize the column names
        stats_table_all.columns = ['Goals', 'Assists', 'Scorer Points', 'Minutes Played', 'Appearances']
        
        # Format the DataFrame
        stats_table_all = stats_table_all.style.format(precision=1)
        
        st.table(stats_table_all)
        
        
        ###########################
        #Leagues
        st.subheader('League')
        
        df_league_filtered = df_league[df_league.ClubID == clubID]
        df_league_filtered = df_league_filtered[['Season', 'Placement', 'Games', 'W', 'D', 'L', 'Pts']].sort_values(by='Season', ascending=False)
        df_league_filtered.set_index('Season', inplace=True)
        st.table(df_league_filtered)
        
        
if __name__ == '__main__':
    main()