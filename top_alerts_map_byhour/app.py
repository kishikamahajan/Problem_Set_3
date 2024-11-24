from shiny import App, render, ui
import pandas as pd
import altair as alt
import json
from shiny import reactive
from shinywidgets import render_altair, output_widget

# Loading the data
top_alerts_maps_byhour = pd.read_csv("/Users/kishikamahajan/Desktop/GitHub/Problem_Set_6/top_alerts_map_byhour/top_alerts_map_byhour.csv")
file_path = "/Users/kishikamahajan/Desktop/GitHub/Problem_Set_6/top_alerts_map_byhour/chicago-boundaries.geojson"
with open(file_path) as f:
    chicago_geojson = json.load(f)

geo_data = alt.Data(values = chicago_geojson["features"])

type_subtype_combinations = top_alerts_maps_byhour[['type', 'subtype']].apply(
    lambda x: f"{x['type']} - {x['subtype']}", axis=1
).tolist()


app_ui = ui.page_fluid(
    ui.panel_title("Chicago Traffic Alerts"),

    # Dropdown menu for type and subtype
    ui.input_select(
        id="type_subtype", 
        label="Select Type and Subtype:", 
        choices=type_subtype_combinations, 
        selected=type_subtype_combinations[0]
    ),

    # Slider for hour selection
    ui.input_slider(
        id="hour", 
        label="Select Hour:", 
        min=0, 
        max=23, 
        value=12, 
        step=1, 
        ticks=True
    ),

    # Map
    output_widget("final_map_chart")
)


def server(input, output, session):
    # Reactive calculation for filtered data
    @reactive.Calc
    def filtered_data():
        # Get selected type-subtype
        chosen_type_subtype = input.type_subtype()
        type, subtype = chosen_type_subtype.split(" - ")

        # Get selected hour
        selected_hour = f"{input.hour():02d}:00"  # Format hour as HH:00

        # Filter data based on type, subtype, and hour
        filtered_data = top_alerts_maps_byhour[
            (top_alerts_maps_byhour["type"] == type) & 
            (top_alerts_maps_byhour["subtype"] == subtype) &
            (top_alerts_maps_byhour["hour"] == selected_hour)
        ]

        # Select top 10 by count
        filtered = filtered_data.nlargest(10, "count")
        return filtered

    # Render Altair chart
    @render_altair
    def final_map_chart():
        data = filtered_data()

        # making the scatter plot the same way as before
        scatter_plot = alt.Chart(data).mark_circle().encode(
            x=alt.X(
                "binned_longitude:Q",
                scale=alt.Scale(domain=[-87.79, -87.62]),  
                title="Longitude"
            ),
            y=alt.Y(
                "binned_latitude:Q",
                scale=alt.Scale(domain=[41.8, 41.99]), 
                title="Latitude"
            ),
            size=alt.Size(
                "count:Q", 
                scale=alt.Scale(range=[10, 500]),  
                title="Number of Alerts"
            )
        ).properties(height = 400, width = 400).project(type="equirectangular")

        # making the map the same way as before
        geo_data = alt.Data(values=chicago_geojson["features"])
        map_chart = alt.Chart(geo_data).mark_geoshape(
            fill="lightgray",
            stroke="black",
            opacity=0.6
        ).project(type="equirectangular")

        return map_chart + scatter_plot

app = App(app_ui, server)