import streamlit as st
import math
import pandas as pd
import matplotlib.pyplot as plt


def widmark_bac(weight_grams: float, alcohol_grams: float, windmark_factor: float):
    bac = alcohol_grams / (weight_grams * windmark_factor) * 100
    return bac


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
    metabolism_rate_per_min = (0.015 / 60)
    return metabolism_rate_per_min * minutes


def main():
    st.title("BAC and Time Analysis")

    weight = st.number_input("Enter your body weight (lbs):", value=145)
    height = st.number_input("Enter your height (cm):", value=177.8)
    is_male = st.checkbox("Male", True)

    drinking_threshold = st.number_input("Enter your BAC threshold:", value=0.05)

    absorption_minutes = st.number_input("Enter the time (in minutes) to absorb a drink:", value=15)

    session_length = st.number_input("How long, in minutes, do you want to drink for?", value=60)

    wfactor = calculate_windmark_factor(weight, height, is_male)

    drink_time_option = st.number_input("Select drink time (minutes after start):", 0)
    drink_amount = st.number_input("Enter drink amount:", value=1)

    add_drink = st.button("Add Drink")

    if add_drink:
        existing_drinks = drinks.get(drink_time_option, 0)
        drinks[drink_time_option] = existing_drinks + drink_amount

    alcohol_buffer = 0
    bac_timesteps = []
    absorption_rate = 14 / absorption_minutes

    counter = 0
    zero_counter = 0
    last_entered_drink_timestep = 0

    while True:
        value = bac_timesteps[counter - 1] if counter > 0 else 0
        drinks_at_time = drinks.get(counter, 0)

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
            drinks[counter + 1] = 1
            last_entered_drink_timestep = max(drinks.keys())

        counter += 1

    bac_df = pd.DataFrame({'timestep': range(len(bac_timesteps)), 'BAC': bac_timesteps})

    col1, col2, col3 = st.columns(3)
    with col1:
        st.dataframe(bac_df)
    with col2:
        drinks_df = pd.DataFrame.from_dict(drinks, orient='index', columns=['Amount'])
        drinks_df.index.name = 'Drink Time'
        st.dataframe(drinks_df)

    fig, ax = plt.subplots()
    ax.plot(bac_df['timestep'], bac_df['BAC'])
    ax.set_xlabel('Timestep (minutes)')
    ax.set_ylabel('BAC')
    for drink_time in drinks.keys():
        ax.axvline(x=drink_time, color='red', linestyle='--')
    ax.set_title('Time vs BAC')
    st.pyplot(fig)


if __name__ == '__main__':
    drinks = {}
    main()
