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
    
    
# Iterate through the list with enumeration to get both index and value
def get_smallest_possible_stat_list_index(values, expected_stat):
    for index, value in enumerate(values):
        if value <= expected_stat:
            return index

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
    
    crowdtransfer_id = st.number_input("Enter transferid:", min_value=None, max_value=None, value=539, step=1)

    
    api_url = "https://dev.crowdtransfer.io/api/transfers/{}".format(crowdtransfer_id)
    
    goal_raisable_by_fans = 100000
    club_name_crowdtransfer = 'FC Winterthur'
    player_position_idx = 0

    data = fetch_data(api_url)
    

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
            player_position_idx=2
        elif player_position_idx_fetched == 'OFFENSE':
            player_position_idx=3
        else:
            pass
        
        # Assuming 'data' is the variable containing your list of dictionaries
        premiums = data['premiums']

        # Extract the required information and create a list of dictionaries
        extracted_data = [
            {
                'name': premium['name'],
                'category': premium['category'],
                'payout': premium['payout']
            }
            for premium in premiums
        ]

        # Convert the list of dictionaries into a pandas DataFrame
        df_premiums = pd.DataFrame(extracted_data)
        df_premiums = df_premiums.drop_duplicates(subset=['name', 'category'], keep='last')
        try:
            df_premiums['payout'] = df_premiums['payout'].astype(int)
        except KeyError:
            pass
        
        # Assuming 'data' is the variable containing your list of dictionaries
        rewards = data['rewards']

        # Extract the required information and create a list of dictionaries
        extracted_data = []
        for reward in rewards:
            reward_entry_min = reward['reward_entries'][0]
            if len(reward['reward_entries']) > 1:
                # Extracting the condition amounts
                reward_entries = reward['reward_entries']
                extracted_data.append({
                    'name': reward['name'],
                    'category': reward['category'],
                    'condition_amount_min': [int(entry['condition_amount']) for entry in reward_entries],
                    'condition_amount_max': [int(entry['condition_amount']) for entry in reward_entries],
                    'payout_percent_min': [int(entry['payout_percent']) for entry in reward_entries],
                    'payout_percent_max': [int(entry['payout_percent']) for entry in reward_entries],
                    'type': 'list'
                })
            else:
                reward_entry_max = reward_entry_min
            
                extracted_data.append({
                    'name': reward['name'],
                    'category': reward['category'],
                    'condition_amount_min': reward_entry_min['condition_amount'],
                    'condition_amount_max': reward_entry_max['condition_amount'],
                    'payout_percent_min': reward_entry_min['payout_percent'],
                    'payout_percent_max': reward_entry_max['payout_percent'],
                    'type': 'numbers'
                })

        # Convert the list of dictionaries into a pandas DataFrame
        df_rewards = pd.DataFrame(extracted_data)
        df_rewards = df_rewards.drop_duplicates(subset=['name', 'category'], keep='last')
        
        st.text(data['id'])
        st.text(goal_raisable_by_fans_fetched)
        st.text(str(club_name_crowdtransfer_fetched))
        st.text(player_position_idx_fetched)
        st.table(df_premiums)
        st.table(df_rewards)
        
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
    
    # Check if the input from API is empty
    if df_premiums.empty:
        pass
    else:
        recode_premiums = {'Goals scored - only in league': 'Goal in main competition', 
                            'Assists made - only in league': 'Assist in main competition', 
                            'Scorer Points - only in league': 'ScorerPoint in main competition', 
                            'Games Played - only in league': 'Appearance in main competition', 
                            'Goals scored - all competitions': 'Goal across all competitions', 
                            'Assists made - all competitions': 'Assist across all competitions', 
                            'Scorer Points - all competitions': 'ScorerPoint across all competitions', 
                            'Games Played - all competitions': 'Appearance across all competitions'}
        
        df_premiums['name'] = df_premiums['name'].replace(recode_premiums)
        
        for i, r in df_premiums.iterrows():
            selected_premium_variables.append(r['name'])
    
    # Display input fields for each selected variable
    for var in selected_premium_variables:
        if var in df_premiums['name'].values:
            sub_df = df_premiums[df_premiums['name'] == var]
            sub_df.reset_index(inplace=True,drop=True)
            inputs_premiums[var] = st.number_input(f"Payout per {var}:", value=sub_df.at[0,'payout'], step=1000)
        else:
            inputs_premiums[var] = st.number_input(f"Payout per {var}:", value=0, step=1000)
        
        
    ################################################################################
    #Rewards
    ################################################################################
    
    # rewards kann mehrere brackets haben, dassjengige nehmen welches es erfüllen würde
    st.subheader('Rewards')
            
    reward_variables = ['Minutes played in main competition','Minutes played across all competitions',
                        'Won games in main competition', 'Placement in main competition', 'Points in main competition',
                        'Finish Top 3 in League'] 
    
    # Multiselect for variables
    selected_reward_variables = st.multiselect(
        "Choose the Rewards which your club wants to offer to your fans:",
        reward_variables
    )
    
    # Dictionary to store input values for each selected variable
    inputs_rewards = {}
    
    # Check if the input from API is empty
    if df_rewards.empty:
        pass
    else:
        recode_rewards = {'Minutes played in League': 'Minutes played in main competition', 
                            'Minutes played in total': 'Minutes played across all competitions', 
                            'Scorer Points - only in league': 'Won games in main competition', 
                            'Games Played - only in league': 'Placement in main competition', 
                            'Points in the league at the end of the season': 'Points in main competition'}
        
        df_rewards['name'] = df_rewards['name'].replace(recode_rewards)
        
        for i, r in df_rewards.iterrows():
            selected_reward_variables.append(r['name'])
    
    # Display input fields for each selected variable
    for var in selected_reward_variables:
        
        if var in df_rewards['name'].values:
            sub_df = df_rewards[df_rewards['name'] == var]
            sub_df.reset_index(inplace=True,drop=True)
            
            if 'list' == sub_df['type'][0]:
                
                conditions = sub_df.condition_amount_min[0]
                percentages = sub_df.payout_percent_min[0]
                n_cols = len(conditions)

                # Use st.columns to create the columns
                columns = st.columns(n_cols)

                for i in range(n_cols):
                    condition = conditions[i]

                    key_percentage = f"percentage_{i+1}_{var}"
                    key_payout = f"payout_{i+1}_{var}"
                    
                    if key_percentage not in st.session_state:
                        st.session_state[key_percentage] = percentages[i]

                    if key_payout not in st.session_state:
                        st.session_state[key_payout] = round((percentages[i] / 100) * funding)

                    with columns[i]:
                        def update_percentage(key_payout=key_payout, key_percentage=key_percentage):
                            payout_api = st.session_state[key_payout]
                            st.session_state[key_percentage] = round((payout_api / funding) * 100, 2)

                        def update_payout(key_payout=key_payout, key_percentage=key_percentage):
                            percentage = st.session_state[key_percentage]
                            st.session_state[key_payout] = round((percentage / 100) * funding)

                        st.number_input(
                            f"Percentage of funding if {var} > {condition}:",
                            min_value=0.0, max_value=100.0,
                            value=st.session_state[key_percentage],
                            step=0.1, format="%.1f",
                            key=key_percentage,
                            on_change=update_payout
                        )

                        st.number_input(
                            f"Payout if {var} > {condition}:",
                            value=st.session_state[key_payout],
                            min_value=0,
                            step=1000,
                            key=key_payout,
                            on_change=update_percentage
                        )
                                        
                # store for expected costs table
                inputs_rewards[var] = sub_df

            else:
                pass

                
                
        else:
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
        
        #{'Scored Goals':'Goals', 'Minutes played last season':'Minutes Played'}
        
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
            
            if isinstance(amount, pd.DataFrame):
                
                st.text(var)
                conditions_cost = amount.condition_amount_min[0]
                percentages_cost = amount.payout_percent_min[0]
                
                if 'main competition' in var:
                
                    if 'Goal' in var:
                        expected_stat = stats_table_main.at['Stats', 'Goals']
                        index = get_smallest_possible_stat_list_index(conditions_cost, expected_stat)
                        cost = round((float(percentages_cost[index]) / 100) * funding)
                    elif 'Assist' in var:
                        expected_stat = stats_table_main.at['Stats', 'Assists']
                        index = get_smallest_possible_stat_list_index(conditions_cost, expected_stat)
                        cost = round((float(percentages_cost[index])/ 100) * funding)
                    elif 'Scorer' in var:
                        expected_stat = stats_table_main.at['Stats', 'Scorer Points']
                        index = get_smallest_possible_stat_list_index(conditions_cost, expected_stat)
                        cost = round((float(percentages_cost[index]) / 100) * funding)
                    elif 'Appearance' in var:
                        expected_stat = stats_table_main.at['Stats', 'Appearances']
                        index = get_smallest_possible_stat_list_index(conditions_cost, expected_stat)
                        cost = round((float(percentages_cost[index]) / 100) * funding)
                    elif 'Minutes' in var:
                        expected_stat = stats_table_main.at['Stats', 'Minutes Played']
                        index = get_smallest_possible_stat_list_index(conditions_cost, expected_stat)
                        cost = round((float(percentages_cost[index]) / 100) * funding)
                    else:
                        cost = amount
                        
                    cost_dictionary[var] = cost
                    
                elif ('all competition' in var) | ('last season' in var):
                    
                    if 'Goal' in var:
                        expected_stat = stats_table_all.at['Stats', 'Goals']
                        index = get_smallest_possible_stat_list_index(conditions_cost, expected_stat)
                        cost = round((float(percentages_cost[index]) / 100) * funding)
                    elif 'Assist' in var:
                        expected_stat = stats_table_all.at['Stats', 'Assists']
                        index = get_smallest_possible_stat_list_index(conditions_cost, expected_stat)
                        cost = round((float(percentages_cost[index])/ 100) * funding)
                    elif 'Scorer' in var:
                        expected_stat = stats_table_all.at['Stats', 'Scorer Points']
                        index = get_smallest_possible_stat_list_index(conditions_cost, expected_stat)
                        cost = round((float(percentages_cost[index]) / 100) * funding)
                    elif 'Appearance' in var:
                        expected_stat = stats_table_all.at['Stats', 'Appearances']
                        index = get_smallest_possible_stat_list_index(conditions_cost, expected_stat)
                        cost = round((float(percentages_cost[index])/ 100) * funding)
                    elif 'Minutes' in var:
                        expected_stat = stats_table_main.at['Stats', 'Minutes Played']
                        index = get_smallest_possible_stat_list_index(conditions_cost, expected_stat)
                        cost = round((float(percentages_cost[index]) / 100) * funding)
                    else:
                        cost = amount
                        
                    cost_dictionary[var] = cost
                
            else:
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