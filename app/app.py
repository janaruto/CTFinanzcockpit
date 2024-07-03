from fuzzywuzzy import process
import json
import pandas as pd
import re
import requests
import streamlit as st



# Function to fetch data from the API
def fetch_data(url):
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an exception for HTTP errors
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching data: {e}")
        return None


def extract_numbers(input_string):
    # Use regular expression to find the first number and the percentage
    match = re.match(r"(\d+) Wins - (\d+)%", input_string)
    if match:
        first_number = int(match.group(1))
        percentage_number = int(match.group(2))
        return first_number, percentage_number
    else:
        return None, None

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
    
    api_url = "https://dev.crowdtransfer.io/api/transfers/"
    
    goal_raisable_by_fans = 100000
    club_name_crowdtransfer = 'FC Winterthur'
    player_position_idx = 0
    # Button to trigger the API call
    if st.button("Fetch Data"):
        data = fetch_data(api_url)
        data = data['results'][-1]
        
        if data:
            goal_raisable_by_fans_fetched = data['goal_raisable_by_fanbase']
            if goal_raisable_by_fans_fetched != None:
                goal_raisable_by_fans = int(goal_raisable_by_fans_fetched)
            else:
                pass
            
            club_name_crowdtransfer_fetched = data['club']['name']
            if club_name_crowdtransfer_fetched != None:
                club_name_crowdtransfer = club_name_crowdtransfer_fetched
            else:
                pass
            
            player_position_idx_fetched = data['position_type']
            if player_position_idx_fetched != None:
                if player_position_idx_fetched == 'DEFENSE':
                    player_position_idx=1
                elif player_position_idx_fetched == 'MIDFIELD':
                    player_position_ixd=2
                elif player_position_idx_fetched == 'OFFENSE':
                    player_position_idx=3
                else:
                    pass
            
            st.text(data['id'])
            st.text(goal_raisable_by_fans_fetched)
            st.text(str(club_name_crowdtransfer_fetched))
            st.text(player_position_idx_fetched)
        
    # User input features
    
    # Funding
    st.subheader('Funding')
    funding = st.number_input(
        label='Amount of funding through Crowdtransfer platform',
        min_value=0,  # minimum value allowed
        max_value=100000000,  # maximum value allowed
        value=goal_raisable_by_fans,  # default value
        step=10000  # step size
    )
    
    # Club
    st.subheader('Club')
    most_similar_club, similarity_score, index_most_similar_club = process.extractOne(club_name_crowdtransfer, df_clubs['ClubName'])
    clubname = st.selectbox('Select your Club', df_clubs['ClubName'], format_func=lambda x: x.strip(), index=index_most_similar_club)
    filtered_df = df_clubs[df_clubs.ClubName == clubname]
    filtered_df = filtered_df.reset_index(drop=True)
    mainCompetition = filtered_df.at[0, 'CompetitionID']
    clubID = filtered_df.at[0, 'ClubID']
    
    # Position
    st.subheader('Position')
    position = st.selectbox(
    "Which of these options best describes the player's position?",
    ["Goalkeeper", "Defense", "Midfield", "Attack"], index = player_position_idx
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
    
    ################################################################################
    #Premiums
    ################################################################################
    st.subheader('Premiums')
    
    # List of variables
    premium_variables = [
        'Goal in main competition', 'Assist in main competition', 'ScorerPoint in main competition', 'Appearance in main competition',
        'Goal across all competitions', 'Assist across all competitions', 'ScorerPoint across all competitions', 'Appearance across all competitions'
    ]

    # Multiselect for variables
    selected_premium_variables = st.multiselect(
        "Choose the Premiums which your club wants to offer to your fans:",
        premium_variables
    )

    # Dictionary to store input values for each selected variable
    inputs_premiums = {}

    # Display input fields for each selected variable
    for var in selected_premium_variables:
        
        inputs_premiums[var] = st.number_input(f"Payout per {var}:", value=0, step=1000)
        
        
    ################################################################################
    #Rewards
    ################################################################################
    st.subheader('Rewards')
            
    reward_variables = ['Minutes played in main competition','Minutes played across all competitions',
                        'Won games in main competition', 'Placement in main competition', 'Points in main competition'] 
    
    # Multiselect for variables
    selected_reward_variables = st.multiselect(
        "Choose the Rewards which your club wants to offer to your fans:",
        reward_variables
    )
    
    # Dictionary to store input values for each selected variable
    inputs_rewards = {}
    
    # Display input fields for each selected variable
    for var in selected_reward_variables:
        
        if var == 'Won games in main competition':
            
            bracket = ['9 Wins - 25%', '18 Wins - 50%', '36 Wins - 100%'] 
    
            # Multiselect for variables
            bracket_selected = st.selectbox(
                "Choose the percentage of payout to your fans:",
                bracket
            )
            
            col1, col2 = st.columns(2)

            # Calculate initial percentage values
            first_number, percentage_number = extract_numbers(bracket_selected)
            
            # store for expected costs table
            inputs_rewards[var] = percentage_number*funding/100
        
            
            with col1:
                st.text(
                    f"Percentage of funding: {str(percentage_number)}"
                )
            with col2:
                st.text(
                    f"Amount of games which have to be won: {str(first_number)}"
                )
                

        else:
        
            # Create columns for min and max payouts
            col1, col2 = st.columns(2)

            # Calculate initial percentage values
            min_payout = st.session_state.get(f"min_payout_{var}", 0)
            max_payout = st.session_state.get(f"max_payout_{var}", 10000)
            
            # store for expected costs table
            inputs_rewards[var] = max_payout
            
            min_percentage_of_funding = (min_payout / funding) * 100 if funding > 0 else 0
            max_percentage_of_funding = (max_payout / funding) * 100 if funding > 0 else 0
            
            with col1:
                min_percentage_of_funding = st.number_input(
                    f"Min Percentage of funding for {var}:", 
                    min_value=0.0, max_value=100.0, 
                    value=round(min_percentage_of_funding, 1), 
                    step=0.1, format="%.1f",
                    key=f"min_percent_{var}"
                )
            with col2:
                max_percentage_of_funding = st.number_input(
                    f"Max Percentage of funding for {var}:", 
                    min_value=0.0, max_value=100.0, 
                    value=round(max_percentage_of_funding, 1), 
                    step=0.1, format="%.1f",
                    key=f"max_percent_{var}"
                )
                

            # Update payouts based on percentage input
            min_payout = round((min_percentage_of_funding / 100) * funding)
            max_payout = round((max_percentage_of_funding / 100) * funding)
            
            with col1:
                min_payout = st.number_input(
                    f"Minimum payout for {var}:", 
                    value=min_payout, 
                    min_value=0, 
                    step=1000, 
                    key=f"min_payout_{var}"
                )
            with col2:
                max_payout = st.number_input(
                    f"Maximum payout for {var}:", 
                    value=max_payout, 
                    min_value=0, 
                    step=1000, 
                    key=f"max_payout_{var}"
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
        st.table(stats_table_main.style.format(precision=1))
        
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
        st.table(stats_table_all.style.format(precision=1))
        
        
        ###########################
        #Leagues
        st.subheader('League')
        
        df_league_filtered = df_league[df_league.ClubID == clubID]
        df_league_filtered = df_league_filtered[['Season', 'Placement', 'Games', 'W', 'D', 'L', 'Pts']].sort_values(by='Season', ascending=False)
        df_league_filtered.set_index('Season', inplace=True)
        st.table(df_league_filtered)
        
        ################################################################################
        #Expected costs
        ################################################################################
        st.subheader('Expected Payback')
        
        cost_dictionary = {}
        
        for var, amount in inputs_premiums.items():
            
            if 'main competition' in var:
                
                if 'Goal' in var:
                    multiplicator = stats_table_main.at['Stats', 'Goals']
                    cost = multiplicator * amount
                elif 'Assist' in var:
                    multiplicator = stats_table_main.at['Stats', 'Assists']
                    cost = multiplicator * amount
                elif 'Scorer' in var:
                    multiplicator = stats_table_main.at['Stats', 'Scorer Points']
                    cost = multiplicator * amount
                elif 'Appearance' in var:
                    multiplicator = stats_table_main.at['Stats', 'Appearances']
                    cost = multiplicator * amount
                else:
                    cost = amount
                    
                
            elif 'all competition' in var:
                
                if 'Goal' in var:
                    multiplicator = stats_table_all.at['Stats', 'Goals']
                    cost = multiplicator * amount
                elif 'Assist' in var:
                    multiplicator = stats_table_all.at['Stats', 'Assists']
                    cost = multiplicator * amount
                elif 'Scorer' in var:
                    multiplicator = stats_table_all.at['Stats', 'Scorer Points']
                    cost = multiplicator * amount
                elif 'Appearance' in var:
                    multiplicator = stats_table_all.at['Stats', 'Appearances']
                    cost = multiplicator * amount
                else:
                    cost = amount
                    
            else:
                
                cost = amount
                
            cost_dictionary[var] = cost
            
        for var, amount in inputs_rewards.items():
            
            cost_dictionary[var] = amount
            
        # Create a DataFrame from the dictionary
        df_costs = pd.DataFrame(list(cost_dictionary.items()), columns=['Variable', 'Costs'])

        # Calculate the sum of the 'Costs' column
        total_cost = df_costs['Costs'].sum()

        # Add a summary row
        summary_row = pd.DataFrame([['Sum', total_cost]], columns=['Variable', 'Costs'])
        df_costs = pd.concat([df_costs, summary_row], ignore_index=True)
        
        try:
            df_costs['Percentage of total Funding'] = (df_costs.Costs/funding*100).round(1)
        except TypeError:
            df_costs['Percentage of total Funding'] = 0
        
        # Function to format the table with the last row bold
        def make_table_bold(df):
            html = df.to_html(index=False, escape=False)
            # Split the table into rows
            rows = html.split('<tr>')
            # Bold the last row
            rows[-2] = '<tr><b>' + rows[-2] + '</b>'
            # Join the rows back together
            bolded_html = '<tr>'.join(rows)
            return bolded_html

        # Use Streamlit to display the table
        st.markdown(make_table_bold(df_costs), unsafe_allow_html=True)
        
if __name__ == '__main__':
    main()