import pandas as pd
import plotly.express as px
import streamlit as st


def widmark_bac(weight_grams: float, alcohol_grams: float, windmark_factor: float):
    return alcohol_grams / (weight_grams * windmark_factor) * 100


def pounds_to_grams(pounds):
    return pounds * 453.592


def drinks_to_grams(drinks):
    return drinks * 14


def calculate_bmi(weight, height):
    height_m = height / 100
    return weight / (height_m * height_m)


def windmark_factor(bmi: float, male: bool = True):
    if male:
        return 1.0181 - 0.01213 * bmi
    else:
        return 0.9367 - 0.01240 * bmi


def grams_to_kg(grams):
    return grams / 1000


def calculate_windmark_factor(weight: float, height: float, male: bool):
    weight = pounds_to_grams(weight)
    weight_kg = grams_to_kg(weight)
    bmi = calculate_bmi(weight_kg, height)
    return windmark_factor(bmi, male)


def calculate_metabolise(minutes):
    return (0.015 / 60) * minutes


def main():
    st.set_page_config(page_title="BAC and Time Analysis")

    with st.sidebar:
        st.title("BAC and Time Analysis")
        st.write("Calculate your BAC via this handy calculator.")

        if st.button("Reset All"):
            st.session_state.clear()

    if 'drinks' not in st.session_state:
        st.session_state.drinks = {}

    tab1, tab2, tab3 = st.tabs(["Profile", "Party", "Drinks"])

    with tab1:
        weight = st.number_input("Enter your body weight (lbs):", value=145)
        height = st.number_input("Enter your height (cm):", value=177.8)
        absorption_minutes = st.number_input("Enter the time (in minutes) that it takes you to absorb a drink:",
                                             value=15)

        sex = st.selectbox("Sex",("Male","Female"))

        if sex == "Male":
            is_male = True
        else:
            is_male = False


    with tab2:
        drinking_threshold = st.number_input("Enter your minimum BAC threshold:", value=0.05)
        session_length = st.number_input("How long, in minutes, do you want to drink for?", value=60)

    with tab3:
        drink_time_option = st.number_input("Enter drink time (minutes after start):", 0)
        drink_amount = st.number_input("Enter drink amount:", value=0)
        add_drink = st.button("Add Drink")

        if add_drink:
            existing_drinks = st.session_state.drinks.get(drink_time_option, 0)
            st.session_state.drinks[drink_time_option] = existing_drinks + drink_amount

    wfactor = calculate_windmark_factor(weight, height, is_male)

    alcohol_buffer = 0
    bac_timesteps = []
    absorption_rate = 14 / absorption_minutes

    counter = 0
    zero_counter = 0
    last_entered_drink_timestep = 0

    while True:
        value = bac_timesteps[counter - 1] if counter > 0 else 0
        drinks_at_time = st.session_state.drinks.get(counter, 0)

        alcohol_buffer += drinks_to_grams(drinks_at_time)
        grams_absorbed = min(alcohol_buffer, absorption_rate)
        alcohol_buffer -= grams_absorbed

        value += widmark_bac(pounds_to_grams(weight), grams_absorbed, wfactor)
        value -= calculate_metabolise(1)

        value = max(0, value)
        if value == 0:
            zero_counter += 1
        else:
            zero_counter = 0

        bac_timesteps.append(value)

        if zero_counter > 180 and counter > last_entered_drink_timestep and alcohol_buffer <= 0:
            break
        if (session_length > counter > last_entered_drink_timestep or counter < (
                last_entered_drink_timestep - absorption_minutes)) and value <= drinking_threshold and alcohol_buffer <= 0:
            st.session_state.drinks[counter + 1] = st.session_state.drinks.get(counter + 1,
                                                                               0) + 1  # Increment the drink amount
            last_entered_drink_timestep = max(st.session_state.drinks.keys())

        counter += 1

    bac_df = pd.DataFrame({'timestep': range(len(bac_timesteps)), 'BAC': bac_timesteps})

    st.title("Results")


    drinks_df = pd.DataFrame.from_dict(st.session_state.drinks, orient='index', columns=['Amount'])
    drinks_df.index.name = 'Drink Time'
    st.dataframe(drinks_df)

    # Create an interactive plot using Plotly
    st.title("Time vs BAC")
    fig = px.line(bac_df, x='timestep', y='BAC', title='Time vs BAC')
    for drink_time in st.session_state.drinks.keys():
        fig.add_shape(
            type="line",
            x0=drink_time, y0=0,
            x1=drink_time, y1=max(bac_df['BAC']),
            line=dict(color='red', dash='dash')
        )

    # Display the Plotly chart
    st.plotly_chart(fig, use_container_width=True)


if __name__ == '__main__':
    main()
