import streamlit as st
import pandas as pd
import math  # for floor division

# ---------------------------------------------------
# 1. LOAD THE DATA FROM EXCEL
# ---------------------------------------------------
@st.cache_data
def load_data(excel_file: str):
    """
    Loads the energy data from the specified Excel file.
    The file should contain the following columns:
    [Source, Total_costs_per_twh, Energy_per_plant, total_plants,
     rec_cost, waste_cost, toxic_waste_tons, co2_per_twh, score]
    """
    df = pd.read_excel(excel_file)
    return df

# ---------------------------------------------------
# 2. HELPER FUNCTION TO FORMAT COSTS NICELY
# ---------------------------------------------------
def format_cost(value):
    """
    Format a cost value as Million or Billion USD.
    """
    if value >= 1_000_000_000:
        return f"{value/1_000_000_000:.3f} Billion USD"
    else:
        return f"{value/1_000_000:.2f} Million USD"

# ---------------------------------------------------
# 3. REMOVE ROW CALLBACK
# ---------------------------------------------------
def remove_row(index):
    """
    Remove a row from st.session_state.energy_sources at the given index.
    Because st.button supports an on_click callback (as shown in the docs),
    removing the row here will update session state and the app will re-run.
    """
    st.session_state.energy_sources.pop(index)

# ---------------------------------------------------
# 4. MAIN FUNCTION WITH THE STREAMLIT APP
# ---------------------------------------------------
def main():
    # Inject custom CSS for background color, button styles, and sidebar layout
    st.markdown(
        """
        <style>
        /* Background color */
        .stApp {
            background-color: #a8c0a0; /* sage green */
            color: #333333;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }
        /* Header animation */
        .stTitle {
            animation: fadeInDown 1s ease-in-out;
        }
        /* Fade in animation */
        @keyframes fadeInDown {
            0% {
                opacity: 0;
                transform: translateY(-20px);
            }
            100% {
                opacity: 1;
                transform: translateY(0);
            }
        }
        /* Dark green buttons with white text - normal and hover */
        div.stButton > button[kind="primary"] {
            background-color: #2f4f2f !important;
            color: white !important;
        }
        div.stButton > button[kind="primary"]:hover {
            background-color: #1e2f1e !important;
            color: white !important;
        }
        /* Sidebar header style */
        .css-1d391kg h2 {
            color: #4a6f4a;
            font-weight: 600;
        }
        /* Sidebar button group title */
        .sidebar-section-title {
            font-weight: 600;
            font-size: 1.1em;
            margin-top: 10px;
            margin-bottom: 5px;
            color: #4a6f4a;
        }
        /* Gap between energy source buttons and back button */
        .sidebar-gap {
            margin-top: 20px;
            margin-bottom: 20px;
        }
        /* Red outline for Back to Simulator button */
        .back-button {
            border: 2px solid red !important;
            color: red !important;
            background-color: transparent !important;
        }
        .back-button:hover {
            background-color: red !important;
            color: white !important;
        }
        /* Remove buttons styled as red with white text */
        button[data-testid^="remove_"] {
            background-color: red !important;
            color: white !important;
            font-weight: normal !important;
            font-size: 14px !important;
            padding: 6px 12px !important;
            min-width: auto !important;
            min-height: auto !important;
        }
        button[data-testid^="remove_"]:hover {
            background-color: darkred !important;
            color: white !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.title("Data Center Energy Simulation")

    # Initialize session state variables for page and selected source
    if "page" not in st.session_state:
        st.session_state.page = "main"
    if "selected_source" not in st.session_state:
        st.session_state.selected_source = None

    # ------------------------------
    # A) Load Data and Extract Info
    # ------------------------------
    df = load_data("energy_data.xlsx")
    valid_sources = df["Source"].unique().tolist()

    # Sidebar with titles and buttons
    st.sidebar.markdown('<div class="sidebar-section-title">Information for Energy Sources</div>', unsafe_allow_html=True)
    # Show first 6 energy source buttons with title
    for src in valid_sources[:6]:
        if st.sidebar.button(src):
            st.session_state.page = "source_info"
            st.session_state.selected_source = src
    # Show remaining energy source buttons without title
    for src in valid_sources[6:]:
        if st.sidebar.button(src):
            st.session_state.page = "source_info"
            st.session_state.selected_source = src

    # Gap between energy source buttons and back button
    st.sidebar.markdown('<div class="sidebar-gap"></div>', unsafe_allow_html=True)

    # Back to Simulator button with red outline
    back_button_clicked = st.sidebar.button("Back to Simulator", key="back_button")
    if back_button_clicked:
        st.session_state.page = "main"
        st.session_state.selected_source = None

    # Page routing
    if st.session_state.page == "main":
        # ------------------------------------------------------
        # B) Remove Preliminary Data Display (per user request)
        # ------------------------------------------------------
        # (No preliminary data display here)

        # -------------------------------------------------------------------
        # C) Set Up Budget Input (with dynamic range based on the data)
        # -------------------------------------------------------------------
        # Compute cost per plant for each source:
        # cost_per_plant = Energy_per_plant * (Total_costs_per_twh + waste_cost)
        df["min_cost_per_plant"] = df["Energy_per_plant"] * (df["Total_costs_per_twh"] + df["waste_cost"])
        # Maximum cost if all plants are built for each source
        df["max_cost_per_source"] = df["total_plants"] * df["min_cost_per_plant"]

        min_budget = float(df["min_cost_per_plant"].min())
        max_budget = float(df["max_cost_per_source"].sum())

        st.header("Budget Setup")
        st.markdown(
            f"Enter your available budget (in USD). The allowed range is from **{format_cost(min_budget)}** to **{format_cost(max_budget)}**."
        )
        if "budget" not in st.session_state:
            st.session_state.budget = min_budget
        budget = st.number_input(
            "Total Budget (USD)",
            min_value=min_budget,
            max_value=max_budget,
            value=st.session_state.budget,
            step=1_000_000.0,
            key="budget_input"
        )
        st.session_state.budget = budget

        # -----------------------------------------------------------
        # D) Dynamic Input Section for Energy Source & Quantity
        # -----------------------------------------------------------
        st.header("Select Energy Sources")
        st.markdown(
            """
            **Instructions:**
            1. Choose an energy source from the dropdown below. Only those with at least one affordable plant (given your remaining budget) are shown.
            2. Enter the number of plants—this number is capped by both the maximum allowed and by your remaining budget.
            3. The cost for that row and your remaining budget are displayed below each selection.
            4. Click **Add Another Source** to add an additional energy source selection.
            5. Use the **Remove** button beside a row to remove it if needed.
            """
        )

        if "energy_sources" not in st.session_state:
            st.session_state.energy_sources = []

        def add_source():
            # Add a new row with the first valid source and 0 plants.
            st.session_state.energy_sources.append({"type": valid_sources[0], "n": 0})

        st.button("Add Another Source",type="primary", on_click=add_source, key="add_source_button")

        # Initialize an accumulated cost tracker (to enforce overall budget constraints)
        accumulated_cost = 0.0

        # Iterate over each energy source entry
        for i, source_entry in list(enumerate(st.session_state.energy_sources)):
            with st.container():
                st.markdown(f"### Energy Source Input #{i+1}")
                # Calculate remaining budget before this row
                remaining_budget_this = budget - accumulated_cost

                # Filter available sources based on whether at least one plant is affordable
                affordable_sources = []
                for src in valid_sources:
                    row_tmp = df.loc[df["Source"] == src].iloc[0]
                    cost_per_plant_tmp = row_tmp["Energy_per_plant"] * (row_tmp["Total_costs_per_twh"] + row_tmp["waste_cost"])
                    if cost_per_plant_tmp <= remaining_budget_this:
                        affordable_sources.append(src)
                # Make sure current selection is included if already selected
                if source_entry["type"] not in affordable_sources and remaining_budget_this > 0:
                    affordable_sources.append(source_entry["type"])
                affordable_sources = sorted(affordable_sources)

                # Create three columns: source selection, plant number, and remove button.
                col1, col2, col3 = st.columns([3, 3, 1])
                chosen_type = col1.selectbox(
                    f"Energy Source #{i+1}",
                    options=affordable_sources,
                    key=f"type_select_{i}",
                    index=affordable_sources.index(source_entry["type"]) if source_entry["type"] in affordable_sources else 0
                )

                # Retrieve row data for the chosen energy source
                row_data = df.loc[df["Source"] == chosen_type].iloc[0]
                # Cost per plant for this source:
                cost_per_plant = row_data["Energy_per_plant"] * (row_data["Total_costs_per_twh"] + row_data["waste_cost"])
                max_plants_data = int(row_data["total_plants"])
                # Determine how many plants can be afforded given the remaining budget:
                allowed_by_budget = int(remaining_budget_this // cost_per_plant) if cost_per_plant > 0 else max_plants_data
                allowed_max = min(max_plants_data, allowed_by_budget)

                chosen_n = col2.number_input(
                    f"Number of plants for {chosen_type} (Max: {allowed_max})",
                    min_value=0,
                    max_value=allowed_max,
                    value=source_entry["n"],
                    step=1,
                    key=f"n_input_{i}"
                )

                # Update session state for this row
                st.session_state.energy_sources[i]["type"] = chosen_type
                st.session_state.energy_sources[i]["n"] = chosen_n

                # Create the Remove button with an on_click callback;
                # this will call remove_row(i) when clicked.
                col3.button("Remove", key=f"remove_{i}",type="primary", on_click=remove_row, args=(i,))

                # Update accumulated cost with the cost for this row.
                row_cost = chosen_n * cost_per_plant
                accumulated_cost += row_cost

                st.write(f"Cost for this row: {format_cost(row_cost)}")
                st.write(f"Remaining Budget after this row: {format_cost(budget - accumulated_cost)}")

                if chosen_n > allowed_max:
                    st.error("Selected number of plants exceeds remaining budget constraints!")

        st.subheader("Final Budget Status")
        st.write(f"Total Budget: {format_cost(budget)}")
        st.write(f"Total Allocated Cost: {format_cost(accumulated_cost)}")
        st.write(f"Remaining Budget: {format_cost(budget - accumulated_cost)}")

        st.button("Calculate",type="primary", key="calculate_button")

    elif st.session_state.page == "source_info":
        # Show detailed information for the selected energy source
        src = st.session_state.selected_source
        st.header(f"Details for {src}")

        row = df.loc[df["Source"] == src].iloc[0]
        cost_per_twh = row["Total_costs_per_twh"] + row["waste_cost"]

        st.markdown(f"**Energy per plant:** {row['Energy_per_plant']} TWh")
        st.markdown(f"**Total Cost per TWh:** {format_cost(cost_per_twh)}")
        st.markdown(f"**CO₂ Emissions per TWh:** {row['co2_per_twh']:,} Tons")
        st.markdown(f"**Toxic Waste per TWh:** {row['toxic_waste_tons']:,} Tons")
        st.markdown(f"**Climate Score:** {row['score']}")
        st.markdown(f"**Maximum Plants Available:** {row['total_plants']}")

# -------------------
# RUN THE STREAMLIT APP
# -------------------
if __name__ == "__main__":
    main()
