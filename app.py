from flask import Flask, render_template, request
import pandas as pd
import preprocessor, helper
import plotly.offline as py
import plotly.express as px
import matplotlib.pyplot as plt
import seaborn as sns
import io
import base64
import numpy as np


app = Flask(__name__)

df1 = pd.read_csv('athlete_events.csv')
df2 = pd.read_csv('athlete_events_2.csv')
df=pd.concat([df1 ,df2],ignore_index=True)
region_df = pd.read_csv('noc_regions.csv')

df = preprocessor.preprocess(df,region_df)
df.to_csv('df.csv')

def create_plotly_graph(fig):
    return py.plot(fig,output_type = "div")

def create_matplotlib_graph(fig):
    img = io.BytesIO()
    fig.savefig(img, format='png', bbox_inches='tight')
    img.seek(0)
    plot_url = base64.b64encode(img.getvalue()).decode('utf8')
    return f'<img src="data:image/png;base64,{plot_url}" style = "max-width : 80%;">'
    
@app.route('/', methods=['GET', 'POST'])
def home():
    selected_option = request.args.get('option','medal_tally')
    if selected_option == "medal_tally":
        return medal_tally()
    elif selected_option == "overall_analysis":
         return overall_analysis()
    elif selected_option == "country_analysis":
        return country_analysis()
    elif selected_option == "athlete_analysis":
         return athlete_analysis()
    else:
         return medal_tally()
@app.route('/medal_tally', methods=['GET', 'POST'])
def medal_tally():
    years, countries = helper.country_year_list(df)
    selected_year = "Overall"
    selected_country = "Overall"
    medal_table = helper.fetch_medal_tally(df, selected_year, selected_country)
    title = "Overall Tally"
    if request.method == 'POST':
        selected_year = request.form.get('year_select')
        selected_country = request.form.get('country_select')
       
        medal_table = helper.fetch_medal_tally(df, selected_year, selected_country)
        if selected_year == 'Overall' and selected_country == 'Overall':
            title = "Overall Tally"
        if selected_year != 'Overall' and selected_country == 'Overall':
            title = "Medal Tally in " + str(selected_year) + " Olympics"
        if selected_year == 'Overall' and selected_country != 'Overall':
            title = selected_country + " overall performance"
        if selected_year != 'Overall' and selected_country != 'Overall':
            title = selected_country + " performance in " + str(selected_year) + " Olympics"
    return render_template('medal_tally.html',
                           years=years,
                           countries=countries,
                           selected_year=selected_year,
                           selected_country=selected_country,
                           medal_table=medal_table,
                            title=title)

@app.route('/overall_analysis', methods = ['GET','POST'])
def overall_analysis():
    editions = df['Year'].unique().shape[0] - 1
    cities = df['City'].unique().shape[0]
    sports = df['Sport'].unique().shape[0]
    events = df['Event'].unique().shape[0]
    athletes = df['Name'].unique().shape[0]
    nations = df['region'].unique().shape[0]
    sport_list = df['Sport'].unique().tolist()
    sport_list.sort()
    sport_list.insert(0,'Overall')

    nations_over_time = helper.data_over_time(df, 'region')
    fig1 = px.line(nations_over_time, x="Edition", y="region")
    chart1 = create_plotly_graph(fig1)

    events_over_time = helper.data_over_time(df, 'Event')
    fig2 = px.line(events_over_time, x="Edition", y="Event")
    chart2 = create_plotly_graph(fig2)

    athlete_over_time = helper.data_over_time(df, 'Name')
    fig3 = px.line(athlete_over_time, x="Edition", y="Name")
    chart3 = create_plotly_graph(fig3)

    fig4, ax = plt.subplots(figsize=(20, 20))
    x = df.drop_duplicates(['Year', 'Sport', 'Event'])
    ax = sns.heatmap(x.pivot_table(index='Sport', columns='Year', values='Event', aggfunc='count').fillna(0).astype('int'),
                     annot=True)
    chart4 = create_matplotlib_graph(fig4)

    return render_template('overall_analysis.html',
                           editions=editions,
                           cities=cities,
                           sports=sports,
                           events=events,
                           athletes=athletes,
                           nations=nations,
                           chart1=chart1,
                           chart2=chart2,
                           chart3=chart3,
                           chart4=chart4,
                          )

@app.route('/country_analysis', methods=['GET', 'POST'])
def country_analysis():
    country_list = df['region'].dropna().unique().tolist()
    country_list.sort()
    selected_country = "Afghanistan"
    yearwise_medal_count_table = None
    country_event_heatmap_table = None
    most_successful_countrywise_table = None
    
    if request.method == 'POST':
        selected_country = request.form.get('country_select')
        yearwise_medal_count_table = helper.yearwise_medal_tally(df,selected_country)
        country_event_heatmap_table = helper.country_event_heatmap(df,selected_country)
        most_successful_countrywise_table = helper.most_successful_countrywise(df,selected_country)
    
    
        if yearwise_medal_count_table is not None:
            fig1 = px.line(yearwise_medal_count_table, x="Year", y="Medal")
            chart1 = create_plotly_graph(fig1)
        else:
            chart1 = None
        
        if country_event_heatmap_table is not None:
            fig2, ax = plt.subplots(figsize=(10, 10))
            ax = sns.heatmap(country_event_heatmap_table, annot=True)
            chart2 = create_matplotlib_graph(fig2)
        else:
            chart2 = None
    else:
        yearwise_medal_count_table = helper.yearwise_medal_tally(df,selected_country)
        country_event_heatmap_table = helper.country_event_heatmap(df,selected_country)
        most_successful_countrywise_table = helper.most_successful_countrywise(df,selected_country)
    
    
        if yearwise_medal_count_table is not None:
            fig1 = px.line(yearwise_medal_count_table, x="Year", y="Medal")
            chart1 = create_plotly_graph(fig1)
        else:
            chart1 = None
        
        if country_event_heatmap_table is not None:
            fig2, ax = plt.subplots(figsize=(10, 10))
            ax = sns.heatmap(country_event_heatmap_table, annot=True)
            chart2 = create_matplotlib_graph(fig2)
        else:
            chart2 = None

    return render_template('country_analysis.html',
                            country_list = country_list,
                            selected_country = selected_country,
                           yearwise_medal_count_table = yearwise_medal_count_table,
                           country_event_heatmap_table = country_event_heatmap_table,
                           chart1=chart1,
                           chart2=chart2
                           )

@app.route('/athlete_analysis',methods = ['GET','POST'])
def athlete_analysis():
    sport_list = df['Sport'].unique().tolist()
    sport_list.sort()
    sport_list.insert(0, 'Overall')
    weight_height_df = None
    men_women_df = helper.men_vs_women(df)
    selected_sport = "Overall"
    if request.method == 'POST':
        selected_sport = request.form.get('sport_select')
        weight_height_df = helper.weight_v_height(df, selected_sport)
        if weight_height_df is not None:
           weight_height_df = weight_height_df.fillna("N/A")

        if weight_height_df is not None:
            fig1 = px.scatter(weight_height_df, x="Weight", y="Height", color = "Medal")
            chart1 = create_plotly_graph(fig1)
        else:
             chart1 = None
        
    else:
         weight_height_df = helper.weight_v_height(df, selected_sport)
         if weight_height_df is not None:
           weight_height_df = weight_height_df.fillna("N/A")

         if weight_height_df is not None:
            fig1 = px.scatter(weight_height_df, x="Weight", y="Height", color = "Medal")
            chart1 = create_plotly_graph(fig1)
         else:
            chart1 = None
            

    if men_women_df is not None:
      men_women_df.rename(columns={"Male":"Men","Female":"Women"},inplace = True)
      fig2 = px.line(men_women_df,x="Year",y=["Men","Women"])
      chart2 = create_plotly_graph(fig2)
    else:
        chart2 = None
   
    athlete_df = df.drop_duplicates(subset=['Name', 'region'])
    
    fig3, ax = plt.subplots(figsize=(10,6))
    for medal in ["Gold","Silver","Bronze"]:
        medalists = athlete_df[athlete_df["Medal"] == medal]
        sns.kdeplot(medalists["Age"], label = f"{medal} Medalist", ax = ax)
    ax.legend()
    chart3 = create_matplotlib_graph(fig3)
    
    fig4, ax = plt.subplots(figsize=(10,6))
    
    sports = df["Sport"].unique().tolist()
    for sport in sports:
        gold_medalists = athlete_df[(athlete_df['Medal'] == 'Gold') & (athlete_df["Sport"] == sport)]
        if not gold_medalists.empty:
            sns.kdeplot(gold_medalists["Age"], label = f"{sport}", ax=ax)
    ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')        
    chart4 = create_matplotlib_graph(fig4)
    


    return render_template('athlete_analysis.html',
                            sport_list = sport_list,
                            weight_height_df = weight_height_df,
                            men_women_df = men_women_df,
                           chart1 = chart1,
                           chart2 = chart2,
                           chart3 = chart3,
                            chart4 = chart4,
                           selected_sport = selected_sport
                           )


if __name__ == '__main__':
    app.run(debug=True)