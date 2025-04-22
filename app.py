import streamlit as st
import pandas as pd

# ---------------------------------------------------
# 1. LOAD THE DATA FROM EXCEL
# ---------------------------------------------------
@st.cache_data
def load_data(excel_file: str):
    return pd.read_excel(excel_file)

# ---------------------------------------------------
# 2. HELPER FUNCTION TO FORMAT COSTS NICELY
# ---------------------------------------------------
def format_cost(value):
    if value >= 1_000_000_000:
        return f"{value/1_000_000_000:.3f} Billion USD"
    return f"{value/1_000_000:.2f} Million USD"

# ---------------------------------------------------
# 3. REMOVE ROW CALLBACK
# ---------------------------------------------------
def remove_row(idx):
    st.session_state.energy_sources.pop(idx)

# ---------------------------------------------------
# 4. MAIN WITH CSS, SIDEBAR, SIMULATOR + REMOVE
# ---------------------------------------------------
def main():
    # --- inject CSS ---
    st.markdown("""
    <style>
      .stApp { background-color: #a8c0a0; }
      .stTitle { animation: fadeInDown 1s ease; }
      @keyframes fadeInDown {
        from { opacity: 0; transform: translateY(-20px); }
        to   { opacity: 1; transform: translateY(0); }
      }
      div.stButton > button[kind="primary"] {
        background-color: #2f4f2f!important; color:white!important;
      }
      div.stButton > button[kind="primary"]:hover {
        background-color: #1e2f1e!important;
      }
      button[data-testid^="remove_"] {
        background:red!important; color:white!important; font-weight:bold;
        font-size:20px; padding:0 10px; min-width:30px; min-height:30px;
      }
      button[data-testid^="remove_"]:hover {
        background:darkred!important;
      }
      .sidebar .css-1d391kg h2 { color:#4a6f4a; font-weight:600; }
      .sidebar-section-title { font-weight:600; font-size:1.1em; color:#4a6f4a; margin:10px 0 5px; }
      .sidebar-gap { margin:20px 0; }
      .back-button {
        border:2px solid red!important; color:red!important; background:transparent!important;
      }
      .back-button:hover {
        background:red!important; color:white!important;
      }
    </style>
    """, unsafe_allow_html=True)

    st.title("Data Center Energy Simulation")

    # --- load data + sidebar nav ---
    df = load_data("energy_data.xlsx")
    sources = df["Source"].tolist()

    if "page" not in st.session_state:
        st.session_state.page = "main"
        st.session_state.selected_source = None

    st.sidebar.markdown('<div class="sidebar-section-title">Energy Sources</div>', unsafe_allow_html=True)
    for s in sources:
        if st.sidebar.button(s):
            st.session_state.page = "source_info"
            st.session_state.selected_source = s

    st.sidebar.markdown('<div class="sidebar-gap"></div>', unsafe_allow_html=True)
    if st.sidebar.button("Back to Simulator", key="back_button"):
        st.session_state.page = "main"

    # --- source detail page ---
    if st.session_state.page == "source_info":
        s = st.session_state.selected_source
        row = df[df["Source"] == s].iloc[0]
        cp = row["Total_costs_per_twh"] + row["waste_cost"]
        st.header(f"Details: {s}")
        st.markdown(f"- Energy/plant: {row['Energy_per_plant']} TWh")
        st.markdown(f"- Cost/TWh: {format_cost(cp)}")
        st.markdown(f"- CO₂/TWh: {row['co2_per_twh']:,} tons")
        st.markdown(f"- Waste/TWh: {row['toxic_waste_tons']:,} tons")
        st.markdown(f"- Score: {row['score']}")
        st.markdown(f"- Max Plants: {row['total_plants']}")
        return

    # --- simulator page ---
    # budget range
    df["cost_per_plant"] = df["Energy_per_plant"]*(df["Total_costs_per_twh"]+df["waste_cost"])
    df["max_src_cost"]  = df["total_plants"]*df["cost_per_plant"]
    min_b = float(df["cost_per_plant"].min())
    max_b = float(df["max_src_cost"].sum())

    st.header("Budget Setup")
    st.markdown(f"Allowed: **{format_cost(min_b)}** – **{format_cost(max_b)}**")
    if "budget" not in st.session_state:
        st.session_state.budget = min_b
    st.session_state.budget = st.number_input(
        "Total Budget (USD)", min_value=min_b, max_value=max_b,
        value=st.session_state.budget, step=1_000_000.0, key="budget_input"
    )

    st.header("Select Energy Sources")
    if "energy_sources" not in st.session_state:
        st.session_state.energy_sources = []

    def add_src():
        st.session_state.energy_sources.append({"type": sources[0], "n": 0})
    st.button("Add Another Source", type="primary", on_click=add_src, key="add_btn")

    acc_cost = 0.0
    B = st.session_state.budget

    for i, ent in list(enumerate(st.session_state.energy_sources)):
        with st.container():
            st.markdown(f"### Row #{i+1}")
            rem = B - acc_cost

            # afford filter
            afford = [s for s in sources
                      if df.loc[df["Source"]==s, "cost_per_plant"].iloc[0] <= rem]
            if ent["type"] not in afford and rem>0:
                afford.append(ent["type"])
            afford = sorted(afford)

            c1,c2,c3 = st.columns([3,3,1])
            sel = c1.selectbox(f"Source #{i+1}", options=afford, key=f"type_{i}")
            r   = df[df["Source"]==sel].iloc[0]
            cpp = r["cost_per_plant"]
            mp  = int(r["total_plants"])
            max_n = min(mp, int(rem//cpp) if cpp>0 else mp)

            n = c2.number_input(
                f"Plants (max {max_n})", min_value=0, max_value=max_n,
                value=ent["n"], step=1, key=f"n_{i}"
            )
            st.session_state.energy_sources[i] = {"type":sel, "n":n}

            # <-- REMOVE button
            c3.button("Remove", key=f"remove_{i}",
                      on_click=remove_row, args=(i,),
                      type="primary"
            )

            row_c = n*cpp
            acc_cost += row_c
            st.write(f"Cost: {format_cost(row_c)}  |  Remaining: {format_cost(B-acc_cost)}")

    st.subheader("Budget Status")
    st.write(f"• Total: {format_cost(B)}")
    st.write(f"• Allocated: {format_cost(acc_cost)}")
    st.write(f"• Remaining: {format_cost(B-acc_cost)}")

    if st.button("Calculate", type="primary", key="calc_btn"):
        E = C = W = CO2 = 0.0
        sc_sum = 0; p_sum = 0
        for e in st.session_state.energy_sources:
            r = df[df["Source"]==e["type"]].iloc[0]
            TE = e["n"]*r["Energy_per_plant"]; E+=TE
            c = TE*(r["Total_costs_per_twh"]+r["waste_cost"]); C+=c
            W += TE*r["toxic_waste_tons"]; CO2+=TE*r["co2_per_twh"]
            sc_sum+=e["n"]*r["score"]; p_sum+=e["n"]
        avg = sc_sum/p_sum if p_sum>0 else 0

        st.subheader("Results")
        st.write(f"• Energy: {E:.2f} TWh")
        st.write(f"• Cost: {format_cost(C)}")
        st.write(f"• Waste: {W:,.0f} tons")
        st.write(f"• CO₂: {CO2:,.0f} tons")
        st.write(f"• Avg Score: {avg:.2f}")

if __name__ == "__main__":
    main()
