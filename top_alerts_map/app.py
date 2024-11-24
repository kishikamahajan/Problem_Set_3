from shiny import App, render, ui
import pandas as pd
import altair as alt
import json
from shiny import reactive
from shinywidgets import render_altair, output_widget

# Loading the data
top_alerts_maps = pd.read_csv("/Users/kishikamahajan/Desktop/GitHub/Problem_Set_6/top_alerts_map/top_alerts_map.csv")
file_path = "/Users/kishikamahajan/Desktop/GitHub/Problem_Set_6/top_alerts_map/chicago-boundaries.geojson"
with open(file_path) as f:
    chicago_geojson = json.load(f)

geo_data = alt.Data(values = chicago_geojson["features"])

# Getting the type-subtype combinations
# This lamba function essentially extracts the value of each type and subtype from each row (x) in the top_alerts_maps df. 
# Attrition: I used chatGPT to get this lambda function. 
type_subtype_combinations = top_alerts_maps[['type', 'subtype']].apply(lambda x: f"{x['type']} - {x['subtype']}", axis=1).tolist()


app_ui = ui.page_fluid(
    ui.panel_title("Chicago Traffic Alerts"),
    
    # Use input_select with id and label
    ui.input_select(
        id = "type_subtype", 
        label = "Select Type and Subtype", 
        choices = type_subtype_combinations, 
        selected = type_subtype_combinations[0]
    ),
    output_widget("final_map_chart"))


def server(input, output, session):

    # using reactive calc as we want the output to be updated everytime the input (dropdown choices change)
    @reactive.Calc 
    def filtered_data():
        chosen_type_subtype = input.type_subtype()
        # essentially ensuring that type and subtype is allocated correctly by splitting using the "-"
        type, subtype = chosen_type_subtype.split(" - ")
        # Filter based on chosen type and subtype
        filtered_data = top_alerts_maps[(top_alerts_maps["type"] == type) & (top_alerts_maps["subtype"] == subtype)]
        # Select the top 10 based on the pre existing "count" column
        filtered = filtered_data.nlargest(10, "count")
        return filtered

    @render_altair
    def final_map_chart():
        data = filtered_data()

        # creating the scatter plot in the same way we did before
        scatter_plot = alt.Chart(data).mark_circle().encode(
            x = alt.X(
                "binned_longitude:Q",
                scale = alt.Scale(domain = [-87.79, -87.62]),  
                title = "Latitude"),
            y = alt.Y(
                "binned_latitude:Q",
                scale = alt.Scale(domain = [41.8, 41.99]), 
                title = "Longitude"
                ),
            size = alt.Size(
                "count:Q", 
                scale = alt.Scale(range = [10, 500]),  
                title = "Number of Alerts"
                )).properties(height = 400, width = 400).project(type = "equirectangular")


        # loading the chicago boundaries map the way we did before
        geo_data = alt.Data(values = chicago_geojson['features'])

        map_chart = alt.Chart(geo_data).mark_geoshape(
            fill = "lightgray",
            stroke = "black",
            opacity = 0.6
            ).project(type = "equirectangular")

        return map_chart + scatter_plot

# Create and run the app
app = App(app_ui, server)
