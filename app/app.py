import plotly.express as px
import pandas as pd
import re
import requests
import streamlit as st

# Define the custom CSS to make the sidebar wider
custom_css = """
    <style>
        /* Increase the sidebar width */
        .css-1d391kg {
            width: 1200px;  /* Adjust this value as needed */
        }
    </style>
"""


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
df_attendance = pd.read_csv('data/attendance_df.csv')
competitions = df_clubs['CompetitionID'].unique().tolist()
competitions = [comp for comp in competitions if comp != 'CL']
competitions = [comp for comp in competitions if comp != 'EL']
competitions = [comp for comp in competitions if comp != 'UCOL']


# Streamlit App
def main():
    
    st.title('Finanzcockpit')
        
    # User input features
    col_min_club, col_max_pos = st.columns(2)
    
    with col_min_club :
        
        # Min Funding
        funding_min = st.number_input(label='Mnimal amount of funding through Crowdtransfer',min_value=0,max_value=100000000,value=0,step=100000)
        # Club
        clubname = st.selectbox('Select your Club', df_clubs['ClubName'], format_func=lambda x: x.strip(), index=0)
    
    filtered_df = df_clubs[df_clubs.ClubName == clubname]
    filtered_df = filtered_df.reset_index(drop=True)
    mainCompetition = filtered_df.at[0, 'CompetitionID']
    clubID = filtered_df.at[0, 'ClubID']
    
    with col_max_pos :
        
        # Max Funding
        funding_max = st.number_input(label='Maximum amount of funding through Crowdtransfer',min_value=0,max_value=100000000,value=0,step=100000)
        # Position
        position = st.selectbox("Which of these options best describes your funding?",["Goalkeeper", "Defense", "Midfield", "Attack", "Team"], index = 0)
        
    ################################################################################
    #Market Value
    ################################################################################

    if position != 'Team':
        
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
        
        # Dropdown to select an option from the dictionary keys
        selected_option = st.selectbox(
            "Choose the range where your player's market value falls (defined by the 25%, 50%, 75% quartile borders of the Market Values according to the position and the league in which the selected club competes, over the last 5 seasons):",
            list(quartile_dict.keys()))
    
        
    else:
        # Dropdown to select an option from the dictionary keys
        df_StatsAll = df_playerstats[df_playerstats['Club']==clubname]
        
    ###########################################################################
    # Backers & Social Perks
    ###########################################################################
    
    # Create three columns
    col_socialperks, col_backers = st.columns(2)
    
    with col_socialperks:
    
        # Define the column headers
        header_socialperks = ["Funding Amount", "Internal costs"]
        
        # Initialize the session state to store the DataFrame
        if 'df_socialperks' not in st.session_state:
            # Initialize an empty DataFrame with these MultiIndex columns
            st.session_state.df_socialperks = pd.DataFrame(columns=header_socialperks)
            st.session_state.df_socialperks = st.session_state.df_socialperks.rename_axis("Label")
            
        st.subheader("Social Perks")
        label_socialperks = st.text_input("Enter label for social perk")
        
        # Create two columns
        col_funding, col_internalcost = st.columns(2)
        
        with col_funding:
            funding_amount_min = st.number_input("Min. funding Amount", min_value=0, step=1)
        with col_internalcost:
            internal_costs = st.number_input("Internal Costs", min_value=0, step=1)
        
        # Create two columns
        col_funding_button, col_internalcost_button = st.columns(2)
        
        with col_funding_button:
            # Button to add the row
            if st.button("Add row social perks"):
                
                # Add the new row to the DataFrame stored in session state
                new_row_socialperks = pd.DataFrame([[funding_amount_min, internal_costs]], columns=header_socialperks, index=[label_socialperks])
                
                st.session_state.df_socialperks = pd.concat([st.session_state.df_socialperks, new_row_socialperks])
                st.session_state.df_socialperks = st.session_state.df_socialperks.rename_axis("Label")
                st.success("Row added!")
        with col_internalcost_button:
            #Add a reset button to clear the DataFrame
            if st.button("Reset table social perks"):

                # Create a MultiIndex for the columns
                st.session_state.df_socialperks = pd.DataFrame(columns=header_socialperks)
                st.session_state.df_socialperks =  st.session_state.df_socialperks.rename_axis("Label")
                st.success("Table reset!")
            
        # Display the DataFrame
        st.write(st.session_state.df_socialperks)
        
    with col_backers:
        
        # Define the column headers
        header_backer = ["Who invest more than"]
        
        # Initialize the session state to store the DataFrame
        if 'df_backers' not in st.session_state:
            # Initialize an empty DataFrame with these MultiIndex columns
            st.session_state.df_backers = pd.DataFrame(columns=header_backer)
            st.session_state.df_backers = st.session_state.df_backers.rename_axis("Project number of backers")
            
        # Input fields for a new row
        st.subheader("Backers")
        
        col_backers, col_invest= st.columns(2)
        
        with col_backers:
            n_backers = st.number_input("Number of backers", min_value=0, step=1)
        with col_invest:
            invest_more = st.number_input("Invest more than", min_value=0, step=1)
        
        col_backers_button, col_invest_button = st.columns(2)
        
        with col_backers_button:
            # Button to add the row
            if st.button("Add row backers"):
                
                # Add the new row to the DataFrame stored in session state
                new_row_backer = pd.DataFrame([[invest_more]], columns=header_backer, index=[n_backers])
                
                st.session_state.df_backers = pd.concat([st.session_state.df_backers, new_row_backer])
                st.session_state.df_backers = st.session_state.df_backers.rename_axis("Project number of backers")
                st.success("Row added!")
        
        with col_invest_button:
            #Add a reset button to clear the DataFrame
            if st.button("Reset table backers"):

                # Create a MultiIndex for the columns
                st.session_state.df_backers = pd.DataFrame(columns=header_backer)
                st.session_state.df_backers = st.session_state.df_backers.rename_axis("Project number of backers")
                st.success("Table reset!")
            
        # Display the DataFrame
        st.write(st.session_state.df_backers)

        
    ###########################################################################
    # Occurence & Costs
    ###########################################################################
    
    # Define the column headers
    header = ["$ per Event", "Occurence Min.", "Occurence Exp.", "Occurence Max.", "Costs Min.", "Costs Exp.", "Costs Max."]
    
    # Initialize the session state to store the DataFrame
    if 'df_occurence_costs' not in st.session_state:
        # Initialize an empty DataFrame with these MultiIndex columns
        st.session_state.df_occurence_costs = pd.DataFrame(columns=header)
        st.session_state.df_occurence_costs = st.session_state.df_occurence_costs.rename_axis("Label")

    # Input fields for a new row
    st.subheader("Add Occurence & Costs")
    
    # Create three columns
    col_label, col_apyout_mechanism = st.columns(2)
    
    with col_label:
        label = st.text_input("Enter label for reward/premium")
    with col_apyout_mechanism:
        payout_mechanism = st.checkbox("If checked, this row will be treated as a payout per event feature")
    
    # Create three columns
    col_occ_cost1, col_occ_cost2, col_occ_cost3 = st.columns(3)

    # Place each number input in a different column
    with col_occ_cost1:
        occurrence_min = st.number_input("Min occurrence", min_value=0.0, step=1.0)
        costs_min = st.number_input("Min costs:", min_value=0.0, step=1000.0)
    with col_occ_cost2:
        occurrence_expected = st.number_input("Expected occurrence", min_value=0.0, step=1.0)
        costs_expected = st.number_input("Expected costs", min_value=0.0, step=1000.0)
    with col_occ_cost3:
        occurrence_max = st.number_input("Max occurrence", min_value=0.0, step=1.0)
        costs_max = st.number_input("Max costs", min_value=0.0, step=1000.0)
    
    # Create three columns
    col_occ_cost1_button, col_occ_cost2_button = st.columns(2)
    
    with col_occ_cost1_button:
        # Button to add the row
        if st.button("Add row occurence & costs"):
            
            if not label:
                st.error("Label cannot be empty!")
            elif label in st.session_state.df_occurence_costs.index:
                st.error(f"Label '{label}' already exists in the DataFrame!")
            else:
                # Convert the boolean to a string or a numeric value if needed
                payout_mechanism_str = "Yes" if payout_mechanism else "No"
                
                # Add the new row to the DataFrame stored in session state
                new_row = pd.DataFrame([[
                    payout_mechanism_str, 
                    occurrence_min, occurrence_expected, occurrence_max, 
                    costs_min, costs_expected, costs_max
                ]], columns=header, index=[label])
                
                st.session_state.df_occurence_costs = pd.concat([st.session_state.df_occurence_costs, new_row])
                st.session_state.df_occurence_costs = st.session_state.df_occurence_costs.rename_axis("Label")
                st.success("Row added!")

    with col_occ_cost2_button:
        #Add a reset button to clear the DataFrame
        if st.button("Reset table occurence & costs"):

            # Create a MultiIndex for the columns
            st.session_state.df_occurence_costs = pd.DataFrame(columns=header)
            st.session_state.df_occurence_costs = st.session_state.df_occurence_costs.rename_axis("Label")
            st.success("Table reset!")
        
    # Display the DataFrame
    st.write(st.session_state.df_occurence_costs)

        
    
    ###########################################################################
    # Sidebar
    ###########################################################################
    if position:
        
        with st.sidebar:
            
            stats_table = st.sidebar.selectbox('Choose a stats table:', ['All competitions', 'Main competition', 'League'])
            
            if position != 'Team':
                playerIds = quartile_dict[selected_option]['PlayerID'].unique().tolist()
            else:
                playerIds = []
            
            if (stats_table == 'All competitions') | (stats_table == 'Main competition'):
                if stats_table == 'All competitions':
                    
                    st.header("Stats all competitions")
                    
                    # Remove the string equal to mainCompetition from the list competitions
                    competitions_filter = [comp for comp in competitions if comp != mainCompetition]
                    
                    if position != 'Team':
                        # Filter the df_playerstats DataFrame
                        df_Stats = df_playerstats[df_playerstats['PlayerID'].isin(playerIds)].reset_index(drop=True)
                        df_Stats = df_Stats[~df_Stats['CompetitionID'].isin(competitions_filter)]
                    else:
                        df_Stats = df_playerstats[(df_playerstats['Club']==clubname)]
                        pass
                    
                elif stats_table == 'Main competition':
                    
                    st.header("Stats main competitions")
                    
                    if position != 'Team':
                        df_Stats = df_playerstats[(df_playerstats['PlayerID'].isin(playerIds)) & (df_playerstats['CompetitionID']==mainCompetition)].reset_index(drop=True)
                    else:
                        df_Stats = df_playerstats[(df_playerstats['Club']==clubname) & (df_playerstats['CompetitionID']==mainCompetition)]
                else:
                    pass
                
                if position != 'Team':
                    # Group by PlayerID and Season, then sum the values
                    df_Stats = df_Stats[['PlayerID', 'Season', 'Goals', 'Assists', 'ScorerPoints', 'MinutesPlayed', 'Appearances']].groupby(by=['PlayerID', 'Season'], as_index=False).sum()
                    df_Stats = df_Stats[['Goals', 'Assists', 'ScorerPoints', 'MinutesPlayed', 'Appearances']]
                else:
                    df_Stats = df_Stats[['Club', 'Season', 'CompetitionID', 'Goals','GoalsConceded', 'Assists', 'ScorerPoints', 'YellowCards','RedCards']].groupby(by=['Club', 'CompetitionID', 'Season'],as_index=False).sum()
                    df_Stats = df_Stats[['CompetitionID', 'Season','Goals','GoalsConceded', 'Assists', 'ScorerPoints', 'YellowCards','RedCards']]
                

                if position != 'Team':
                    
                    st.table(df_Stats.describe().round(1).applymap(lambda x: f"{x:.1f}"))
                
                    column = st.sidebar.selectbox('Choose a column for detailed insights:', df_Stats.columns)
                    # Check if the column selection is valid
                    if column:
                        # Compute quartiles and other statistics
                        quartiles = df_Stats[column].quantile([0.25, 0.5, 0.75]).round(2)
                        mean_val = df_Stats[column].mean().round(2)
                        min_val = df_Stats[column].min()
                        max_val = df_Stats[column].max()
                        
                        stats = {
                            'Min': min_val,
                            '25%': quartiles[0.25],
                            'Median': quartiles[0.5],
                            'Mean': mean_val,
                            '75%': quartiles[0.75],
                            'Max': max_val
                        }
                        
                        

                        # Create the Plotly histogram
                        fig = px.histogram(df_Stats, x=column, title=f'Histogram of {column}', nbins=20)
                        
                        # Add quartile boundaries to the plot
                        for q, value in stats.items():
                            fig.add_vline(
                                x=value, 
                                line_dash="dash", 
                                line_color="red", 
                            )
                            # Use add_annotation for custom positioning and rotation
                            fig.add_annotation(
                                x=value, 
                                y=0,  # Adjust the y position based on your data
                                text=q,
                                showarrow=True,
                                arrowhead=2,
                                ax=0,
                                ay=-40,  # Adjust the position of the annotation arrow
                                textangle=-45,  # Rotate text
                                font=dict(size=12, color="red")
                            )
                
                        
                        # Display the plot
                        st.plotly_chart(fig)
                        
                    else:
                        pass
                        
                else:
                    df_Stats = df_Stats.sort_values(by=['Season', 'CompetitionID'], ascending=False)
                    st.table(df_Stats.set_index(['CompetitionID', 'Season']))
                    
                    df_league_filtered = df_league[df_league.ClubID == clubID]
                    df_league_filtered = df_league_filtered[['CompetitionID','Season', 'Placement', 'Games', 'W', 'D', 'L', 'Pts']].sort_values(by='Season', ascending=False)
                    df_league_filtered = df_league_filtered.rename(columns={'CompetitionID':'League'})
                    df_league_filtered.set_index('Season', inplace=True)
                    
                    #df_attendance_filtered = df_attendance[df_attendance.CompetitionID == mainCompetition]
                    #df_attendance_filtered = df_attendance_filtered[df_attendance_filtered['Home Team'] == clubname]
                    st.header("Club performance in main competition")
                    st.table(df_league_filtered)
                    #st.table(df_attendance_filtered)
                    


            elif stats_table == 'League':
                df_league_filtered = df_league[df_league.ClubID == clubID]
                df_league_filtered = df_league_filtered[['CompetitionID','Season', 'Placement', 'Games', 'W', 'D', 'L', 'Pts']].sort_values(by='Season', ascending=False)
                df_league_filtered = df_league_filtered.rename(columns={'CompetitionID':'League'})
                df_league_filtered.set_index('Season', inplace=True)
                
                #df_attendance_filtered = df_attendance[df_attendance.CompetitionID == mainCompetition]
                #df_attendance_filtered = df_attendance_filtered[df_attendance_filtered['Home Team'] == clubname]
                st.header("Club performance in main competition")
                st.table(df_league_filtered)
                #st.table(df_attendance_filtered)
                
            else:
                pass
            
            
        
if __name__ == '__main__':
    main()