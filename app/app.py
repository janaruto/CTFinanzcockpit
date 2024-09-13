import plotly.express as px
import pandas as pd
import re
import requests
import streamlit as st

st.set_page_config(layout="wide")

# Inject custom CSS to set the width of the sidebar
st.markdown(
    """
    <style>
        section[data-testid="stSidebar"] {
            width: 800px !important; # Set the width to your desired value
        }
    </style>
    """,
    unsafe_allow_html=True,
)



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
    col_min, col_max, col_pos, col_club  = st.columns(4)
    
    with col_min:
        # Min Funding
        funding_min = st.number_input(label='Mnimal amount of funding through Crowdtransfer',min_value=0,max_value=100000000,value=0,step=100000)
    with col_max:
        # Max Funding
        funding_max = st.number_input(label='Maximum amount of funding through Crowdtransfer',min_value=0,max_value=100000000,value=0,step=100000)
    with col_pos:
        # Position
        position = st.selectbox("Which of these options best describes your funding?",["Goalkeeper", "Defense", "Midfield", "Attack", "Team"], index = 0)
    with col_club:
        clubname = st.selectbox('Select your Club', df_clubs['ClubName'], format_func=lambda x: x.strip(), index=0)
    
    filtered_df = df_clubs[df_clubs.ClubName == clubname]
    filtered_df = filtered_df.reset_index(drop=True)
    mainCompetition = filtered_df.at[0, 'CompetitionID']
    clubID = filtered_df.at[0, 'ClubID']
        
        
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
    
    # Define the column headers
    header_socialperks = ["Projected number of backers", "Funding Amount", "Internal costs"]
    
    # Initialize the session state to store the DataFrame
    if 'df_socialperks' not in st.session_state:
        # Initialize an empty DataFrame with these MultiIndex columns
        st.session_state.df_socialperks = pd.DataFrame(columns=header_socialperks)
        st.session_state.df_socialperks = st.session_state.df_socialperks.rename_axis("Label")
        
    st.subheader("Bakers & Social Perks")
    
    
    # Create two columns
    col_label_social, col_backers, col_funding, col_internalcost = st.columns(4)
    
    with col_label_social:
        label_socialperks = st.text_input("Enter label for social perk")
    with col_backers:
        n_backers = st.number_input("Number of backers", min_value=0, step=1)
    with col_funding:
        funding_amount_min = st.number_input("Min. funding Amount", min_value=0, step=1)
    with col_internalcost:
        internal_costs = st.number_input("Internal Costs", min_value=0, step=1)
    
    # Button to add the row
    if st.button("Add row Bakers & Social Perks"):
        
        # Add the new row to the DataFrame stored in session state
        new_row_socialperks = pd.DataFrame([[n_backers, funding_amount_min, internal_costs]], columns=header_socialperks, index=[label_socialperks])
        
        st.session_state.df_socialperks = pd.concat([st.session_state.df_socialperks, new_row_socialperks])
        st.session_state.df_socialperks = st.session_state.df_socialperks.rename_axis("Label")
        st.success("Row added!")
        
    # Text input and remove row functionality
    label_to_remove_social_perks = st.text_input("Enter the label of the row to remove of the Bakers & Social Perks table")

    if st.button("Remove row of the Bakers & Social Perks table"):
        if label_to_remove_social_perks in st.session_state.df_socialperks.index:
            # Remove the row from the DataFrame
            st.session_state.df_socialperks = st.session_state.df_socialperks.drop(index=label_to_remove_social_perks)
            st.success(f"Row '{label_to_remove_social_perks}' removed!")
        else:
            st.error(f"Label '{label_to_remove_social_perks}' not found in the DataFrame!")
            
    # Create three columns
    col_label_edit_socialperks, col_col_edit_socialperks, col_val_edit_socialperks = st.columns(3)
        
    # Select a row label and column for editing
    with col_label_edit_socialperks:
        label_to_edit_socialperks = st.text_input("Enter the label of the row to edit of the Bakers & Social Perks table")
    
    with col_col_edit_socialperks:
        column_to_edit_socialperks = st.selectbox("Select the column to edit of the Bakers & Social Perks table", options=header_socialperks)
        
    with col_val_edit_socialperks:
        new_value_socialperks = st.text_input(f"Enter the new value for {column_to_edit_socialperks}")


    if st.button("Edit cell of the Bakers & Social Perks table"):
        if label_to_edit_socialperks in st.session_state.df_socialperks.index:
            try:
                # Cast to numeric if necessary (except for '$ per Event' which is a string)
                if column_to_edit_socialperks != "Test":
                    new_value_socialperks = float(new_value_socialperks)
                
                # Update the value in the DataFrame
                st.session_state.df_socialperks.at[label_to_edit_socialperks, column_to_edit_socialperks] = new_value_socialperks
                st.success(f"Value updated for '{label_to_edit_socialperks}' in column '{column_to_edit_socialperks}'!")
            except ValueError:
                st.error("Invalid value entered!")
        else:
            st.error(f"Label '{label_to_edit_socialperks}' not found in the DataFrame!")
            
    #Add a reset button to clear the DataFrame
    if st.button("Reset table Bakers & Social Perks"):

        # Create a MultiIndex for the columns
        st.session_state.df_socialperks = pd.DataFrame(columns=header_socialperks)
        st.session_state.df_socialperks =  st.session_state.df_socialperks.rename_axis("Label")
        st.success("Table reset!")
            
        
    # Display the DataFrame
    st.write(st.session_state.df_socialperks)
    

        
    ###########################################################################
    # Occurence & Costs & Revenue
    ###########################################################################
    
    # Define the column headers
    header = ["$ per Event", "Occurence Min.", "Occurence Exp.", "Occurence Max.", "Costs Min.", "Costs Exp.", "Costs Max.", "Revenue Min.", "Revenue Exp.", "Revenue Max."]
    
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
        rev_min = st.number_input("Min revenue:", min_value=0.0, step=1000.0)
    with col_occ_cost2:
        occurrence_expected = st.number_input("Expected occurrence", min_value=0.0, step=1.0)
        costs_expected = st.number_input("Expected costs", min_value=0.0, step=1000.0)
        rev_expected = st.number_input("Expected revenue", min_value=0.0, step=1000.0)
    with col_occ_cost3:
        occurrence_max = st.number_input("Max occurrence", min_value=0.0, step=1.0)
        costs_max = st.number_input("Max costs", min_value=0.0, step=1000.0)
        rev_max = st.number_input("Max revenue", min_value=0.0, step=1000.0)
    
    # Button to add the row
    if st.button("Add row Occurence & Costs"):
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
                costs_min, costs_expected, costs_max, rev_min, rev_expected, rev_max,
            ]], columns=header, index=[label])

            st.session_state.df_occurence_costs = pd.concat([st.session_state.df_occurence_costs, new_row])
            st.session_state.df_occurence_costs = st.session_state.df_occurence_costs.rename_axis("Label")
            st.success("Row added!")
            
    # Text input and remove row functionality
    label_to_remove = st.text_input("Enter the label of the row to remove of the Occurence & Costs table")

    if st.button("Remove row of the Occurence & Costs table"):
        if label_to_remove in st.session_state.df_occurence_costs.index:
            # Remove the row from the DataFrame
            st.session_state.df_occurence_costs = st.session_state.df_occurence_costs.drop(index=label_to_remove)
            st.success(f"Row '{label_to_remove}' removed!")
        else:
            st.error(f"Label '{label_to_remove}' not found in the DataFrame!")
            
    # Create three columns
    col_label_edit, col_col_edit, col_val_edit = st.columns(3)
        
    # Select a row label and column for editing
    with col_label_edit:
        label_to_edit = st.text_input("Enter the label of the row to edit of the Occurence & Costs table")
    
    with col_col_edit:
        column_to_edit = st.selectbox("Select the column to edit of the Occurence & Costs table", options=header)
        
    with col_val_edit:
        new_value = st.text_input(f"Enter the new value for {column_to_edit}")


    if st.button("Edit cell of the Occurence & Costs table"):
        if label_to_edit in st.session_state.df_occurence_costs.index:
            try:
                # Cast to numeric if necessary (except for '$ per Event' which is a string)
                if column_to_edit != "$ per Event":
                    new_value = float(new_value)
                
                # Update the value in the DataFrame
                st.session_state.df_occurence_costs.at[label_to_edit, column_to_edit] = new_value
                st.success(f"Value updated for '{label_to_edit}' in column '{column_to_edit}'!")
            except ValueError:
                st.error("Invalid value entered!")
        else:
            st.error(f"Label '{label_to_edit}' not found in the DataFrame!")

    # Add a reset button to clear the DataFrame
    if st.button("Reset table Occurence & Costs"):
        # Reset the DataFrame
        st.session_state.df_occurence_costs = pd.DataFrame(columns=header)
        st.session_state.df_occurence_costs = st.session_state.df_occurence_costs.rename_axis("Label")
        st.success("Table reset!")


    # Display the DataFrame
    st.dataframe(st.session_state.df_occurence_costs)

        
    
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
                    
                    st.dataframe(df_Stats.describe().round(1).applymap(lambda x: f"{x:.1f}"))
                
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
                    st.dataframe(df_Stats.set_index(['CompetitionID', 'Season']))
                    
                    df_league_filtered = df_league[df_league.ClubID == clubID]
                    df_league_filtered = df_league_filtered[['CompetitionID','Season', 'Placement', 'Games', 'W', 'D', 'L', 'Pts']].sort_values(by='Season', ascending=False)
                    df_league_filtered = df_league_filtered.rename(columns={'CompetitionID':'League'})
                    df_league_filtered.set_index('Season', inplace=True)
                    
                    df_attendance_filtered = df_attendance[df_attendance['Home Team ID'] == clubID]
                    df_attendance_filtered['Number of Games'] = 1
                    df_attendance_filtered = df_attendance_filtered[['SeasonID','CompetitionID','Number of Games','Attendance']].groupby(by=['CompetitionID','SeasonID'],as_index=False).agg({'Number of Games': 'sum','Attendance': 'mean'})
                    df_attendance_filtered.Attendance = df_attendance_filtered.Attendance.astype(int)
                    df_attendance_filtered = df_attendance_filtered.rename(columns={'SeasonID':'Season'})
                    df_attendance_filtered.set_index('Season', inplace=True)
                    st.header("Club performance in main competition")
                    st.dataframe(df_league_filtered)
                    st.header("Average Attendance")
                    st.dataframe(df_attendance_filtered)
                    


            elif stats_table == 'League':
                df_league_filtered = df_league[df_league.ClubID == clubID]
                df_league_filtered = df_league_filtered[['CompetitionID','Season', 'Placement', 'Games', 'W', 'D', 'L', 'Pts']].sort_values(by='Season', ascending=False)
                df_league_filtered = df_league_filtered.rename(columns={'CompetitionID':'League'})
                df_league_filtered.set_index('Season', inplace=True)
                
                #df_attendance_filtered = df_attendance[df_attendance.CompetitionID == mainCompetition]
                #df_attendance_filtered = df_attendance_filtered[df_attendance_filtered['Home Team'] == clubname]
                st.header("Club performance in main competition")
                st.dataframe(df_league_filtered)
                #st.dataframe(df_attendance_filtered)
                
            else:
                pass
            
            
    ###########################################################################
    # Cost table
    ###########################################################################
    
    # Define the headers and index
    headers_cost_summary = ["Cost worst performance", "Cost expected performance", "Cost best performance"]
    index_cost_summary = ["Raised Capital", "Revenues from Performance", "Costs Social Perks", "Repayment Fans", "Total Cashflow"]
    
    # Initialize the session state to store the DataFrame
    if 'df_cost_summary' not in st.session_state:
        # Initialize an empty DataFrame with these MultiIndex columns
        st.session_state.df_cost_summary = pd.DataFrame(index=index_cost_summary, columns=headers_cost_summary)
        st.session_state.df_cost_summary = st.session_state.df_cost_summary.rename_axis("Label")
    
    raised_capital_min, raised_capital_exp, raised_capital_max = funding_max, funding_max, funding_max
    repayment_perf_min, repayment_perf_exp, repayment_perf_max = 0, 0, 0
    revenue_perf_min, revenue_perf_exp, revenue_perf_max = 0, 0, 0
    
    for i, r in st.session_state.df_occurence_costs.iterrows():
        
        if r['$ per Event'] == 'Yes':
            repayment_perf_min += r['Occurence Min.'] * r['Costs Min.']
            repayment_perf_exp += r['Occurence Exp.'] * r['Costs Exp.']
            repayment_perf_max += r['Occurence Max.'] * r['Costs Max.']
            revenue_perf_min += r['Occurence Min.'] * r['Revenue Min.']
            revenue_perf_exp += r['Occurence Exp.'] * r['Revenue Exp.']
            revenue_perf_max += r['Occurence Max.'] * r['Revenue Max.']
        else:
            repayment_perf_min += r['Costs Min.']
            repayment_perf_exp += r['Costs Exp.']
            repayment_perf_max += r['Costs Max.']
            revenue_perf_min += r['Revenue Min.']
            revenue_perf_exp += r['Revenue Exp.']
            revenue_perf_max += r['Revenue Max.']
            
    cost_social_perks = 0
            
    for i, r in st.session_state.df_socialperks.iterrows():
            
        cost_social_perks += r['Projected number of backers'] * r['Internal costs']
        
    st.session_state.df_cost_summary.at["Raised Capital", "Cost worst performance"] = raised_capital_min
    st.session_state.df_cost_summary.at["Raised Capital", "Cost expected performance"] = raised_capital_exp
    st.session_state.df_cost_summary.at["Raised Capital", "Cost best performance"] = raised_capital_max
    
    st.session_state.df_cost_summary.at["Revenues from Performance", "Cost worst performance"] = revenue_perf_min
    st.session_state.df_cost_summary.at["Revenues from Performance", "Cost expected performance"] = revenue_perf_exp
    st.session_state.df_cost_summary.at["Revenues from Performance", "Cost best performance"] = revenue_perf_max
    
    st.session_state.df_cost_summary.at["Costs Social Perks", "Cost worst performance"] = cost_social_perks
    st.session_state.df_cost_summary.at["Costs Social Perks", "Cost expected performance"] = cost_social_perks
    st.session_state.df_cost_summary.at["Costs Social Perks", "Cost best performance"] = cost_social_perks
    
    st.session_state.df_cost_summary.at["Repayment Fans", "Cost worst performance"] = repayment_perf_min
    st.session_state.df_cost_summary.at["Repayment Fans", "Cost expected performance"] = repayment_perf_exp
    st.session_state.df_cost_summary.at["Repayment Fans", "Cost best performance"] = repayment_perf_max
    
    st.session_state.df_cost_summary.at["Total Cashflow", "Cost worst performance"] = raised_capital_min + revenue_perf_min - cost_social_perks - repayment_perf_min
    st.session_state.df_cost_summary.at["Total Cashflow", "Cost expected performance"] = raised_capital_exp + revenue_perf_exp - cost_social_perks - repayment_perf_exp
    st.session_state.df_cost_summary.at["Total Cashflow", "Cost best performance"] = raised_capital_max + revenue_perf_max - cost_social_perks - repayment_perf_max
        
    st.header("Cost Summary")
    st.dataframe(st.session_state.df_cost_summary)
    
if __name__ == '__main__':
    main()