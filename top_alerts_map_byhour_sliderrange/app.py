from shiny import App, render, ui
from shinywidgets import output_widget, render_altair
import pandas as pd
import altair as alt
import json
from shiny import reactive

# Loading the data
top_alerts_maps_byhour_sliderrange = pd.read_csv("/Users/kishikamahajan/Desktop/GitHub/Problem_Set_6/top_alerts_map_byhour_sliderrange/top_alerts_map_byhour.csv")
file_path = "/Users/kishikamahajan/Desktop/GitHub/Problem_Set_6/top_alerts_map_byhour_sliderrange/chicago-boundaries.geojson"
with open(file_path) as f:
    chicago_geojson = json.load(f)

geo_data = alt.Data(values=chicago_geojson["features"])

type_subtype_combinations = top_alerts_maps_byhour_sliderrange[['type', 'subtype']].apply(
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

    # Switch button to toggle hour slider
    ui.input_switch(
        id="switch_button", 
        label="Toggle to show hour slider", 
        value=False
    ),

    # Conditional panel for hour slider
    ui.output_ui(id = "hour_slider_panel"),

    # Map
    output_widget("final_map_chart")
)


def server(input, output, session):
    @reactive.Calc
    def filtered_data():
        chosen_type_subtype = input.type_subtype()
        type, subtype = chosen_type_subtype.split(" - ")

        # when switch is on: choose from single hours
        if input.switch_button():
            selected_hour = f"{input.hour():02d}:00"  # Formatting hour as HH:00 to match with our dataset
            filtered_data = top_alerts_maps_byhour_sliderrange[
                (top_alerts_maps_byhour_sliderrange["type"] == type) & 
                (top_alerts_maps_byhour_sliderrange["subtype"] == subtype) &
                (top_alerts_maps_byhour_sliderrange["hour"] == selected_hour)
            ]
        # when switch is off: choose from single hours
        else:
            selected_range = input.hour_range()  
            start_hour, end_hour = selected_range
            filtered_data = top_alerts_maps_byhour_sliderrange[
                (top_alerts_maps_byhour_sliderrange["type"] == type) & 
                (top_alerts_maps_byhour_sliderrange["subtype"] == subtype) & 
                (top_alerts_maps_byhour_sliderrange["hour"].between(
                    f"{start_hour:02d}:00", f"{end_hour:02d}:00"
                ))
            ]
        
        filtered = filtered_data.nlargest(10, "count")
        return filtered

    # this part about adding the plots is the same
    @render_altair
    def final_map_chart():
        data = filtered_data()

        # creating a scatter plot
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
        ).properties(height=400, width=400).project(type="equirectangular")

        # adding the chicago neighbourhood map
        geo_data = alt.Data(values=chicago_geojson["features"])
        map_chart = alt.Chart(geo_data).mark_geoshape(
            fill="lightgray",
            stroke="black",
            opacity=0.6
        ).project(type="equirectangular")

        return map_chart + scatter_plot

    # Conditional panel for hour slider
    @output()
    @render.ui
    def hour_slider_panel():
        if input.switch_button():  
            # slider for individual hours when switch is on
            return ui.input_slider(
                id="hour", 
                label="Select Hour:", 
                min=0, 
                max=23, 
                value=11,  # Default to 11 am
                step=1, 
                ticks=True
            )
        else:
            # slider for hour range when switch is off
            return ui.input_slider(
                id="hour_range", 
                label="Select Range of Hours:", 
                min=0, 
                max=23, 
                value=(6, 9),  # Default to "06:00-09:00"
                step=1, 
                ticks=True
            )

app = App(app_ui, server)