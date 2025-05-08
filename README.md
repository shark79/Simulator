
# **Data Center Energy Simulator**

This interactive app helps students explore the environmental and financial impact of powering AI-driven data centers. It allows users to simulate combinations of energy sources under budget constraints and view associated emissions, waste, and sustainability scores.

## **Overview**

Developed as part of a classroom awareness project, the simulator uses real-world data from 2023 to:
- Show how different energy sources contribute to energy generation.
- Highlight the cost, CO₂ emissions, toxic waste, and climate impact of each source.
- Educate students on sustainable decision-making in the age of AI.

---

## **Features**

### 🔍 **Energy Source Explorer**
- View detailed stats for each energy source:
  - Energy per plant (TWh)
  - Total cost per TWh (including waste management)
  - CO₂ emissions per TWh
  - Toxic waste generated
  - Climate impact score
  - Maximum available plants

### 🧮 **Simulator**
- Set a **total budget** and configure energy source combinations.
- Add/remove energy sources and assign the number of plants for each.
- Automatically restricts the number of plants based on:
  - Budget limits
  - Source affordability
  - Maximum plant availability

### 📊 **Output Results**
- After simulation, view:
  - Total energy produced
  - Total cost spent
  - CO₂ emissions (tons)
  - Toxic waste (tons)
  - Average climate score

### 🧠 **Educational Use Case**
- Designed for classroom activities:
  - Teams work with unique constraints (budget, geography, resource limits).
  - Encourages critical thinking on sustainability and energy ethics.
  - Helps build awareness on the hidden costs of AI technologies.

---

## **Setup Instructions**

1. Install dependencies (requires Python + Streamlit):
   ```bash
   pip install pandas streamlit openpyxl
   ```

2. Run the app:
   ```bash
   streamlit run app.py
   ```

3. Make sure `energy_data.xlsx` is in the same directory as `app.py`.

---

## **Files**

- `app.py` – Main application code.
- `energy_data.xlsx` – Dataset containing all source parameters.
- `README.md` – Documentation and usage guide.

---

## **Acknowledgements**

This app was developed at Arizona State University as part of a principled innovation initiative to promote ethical and environmentally responsible AI use.
