import subprocess
subprocess.run(["pip", "install", "plotly"])
import streamlit as st
import pandas as pd
import plotly.express as px

# ---------------- CONFIG ----------------
st.set_page_config(page_title="Restaurant Dashboard", layout="wide")

# ---------------- CUSTOM CSS ----------------
st.markdown("""
<style>
.main {
    background-color: #0F172A;
}
.card {
    background-color: #1E293B;
    padding: 18px;
    border-radius: 12px;
    box-shadow: 0px 4px 12px rgba(0,0,0,0.3);
}
</style>
""", unsafe_allow_html=True)

# ---------------- LOAD DATA ----------------
df = pd.read_csv("SkyCity Auckland Restaurants & Bars.csv")
df.columns = df.columns.str.strip()

# ---------------- AI INSIGHT FUNCTION ----------------
def generate_insights(df):
    insights = []

    # Profit calculation
    profits = {
        "InStore": df["InStoreNetProfit"].sum(),
        "UberEats": df["UberEatsNetProfit"].sum(),
        "DoorDash": df["DoorDashNetProfit"].sum(),
        "SelfDelivery": df["SelfDeliveryNetProfit"].sum()
    }

    best = max(profits, key=profits.get)
    worst = min(profits, key=profits.get)

    insights.append(f"🏆 {best} is the most profitable channel.")
    insights.append(f"⚠ {worst} is the least profitable channel.")

    # Margin calculation (safe)
    def safe_margin(profit, revenue):
        return profit / revenue if revenue != 0 else 0

    margins = {
        "InStore": safe_margin(df["InStoreNetProfit"].sum(), df["InStoreRevenue"].sum()),
        "UberEats": safe_margin(df["UberEatsNetProfit"].sum(), df["UberEatsRevenue"].sum()),
        "DoorDash": safe_margin(df["DoorDashNetProfit"].sum(), df["DoorDashRevenue"].sum()),
        "SelfDelivery": safe_margin(df["SelfDeliveryNetProfit"].sum(), df["SelfDeliveryRevenue"].sum())
    }

    best_margin = max(margins, key=margins.get)
    insights.append(f"📊 {best_margin} has the highest margin efficiency.")

    # Commission impact
    commission_loss = (
        (df["UberEatsRevenue"] * df["CommissionRate"]).sum() +
        (df["DoorDashRevenue"] * df["CommissionRate"]).sum()
    )

    if commission_loss > 0:
        insights.append("💸 Aggregator commissions significantly reduce profitability.")

    # Safe delivery cost detection
    delivery_cols = ["DeliveryCostOrder", "DeliveryCostPerOrder", "SD_DeliveryTotalCost"]
    avg_delivery_cost = 0

    for col in delivery_cols:
        if col in df.columns:
            avg_delivery_cost = df[col].mean()
            break

    if avg_delivery_cost < 3:
        insights.append("🚚 Self-delivery is cost-efficient.")
    else:
        insights.append("⚠ High delivery costs may reduce self-delivery profitability.")

    return insights

# ---------------- HEADER ----------------
st.markdown("""
# 🍽️ Restaurant Profitability Dashboard  
### 📊 Multi-Channel Financial Insights
""")

st.markdown("---")

# ---------------- SIDEBAR ----------------
st.sidebar.header("🔍 Filters")

cuisine = st.sidebar.multiselect(
    "Cuisine",
    df["CuisineType"].unique(),
    default=df["CuisineType"].unique()
)

segment = st.sidebar.multiselect(
    "Segment",
    df["Segment"].unique(),
    default=df["Segment"].unique()
)

filtered_df = df[
    (df["CuisineType"].isin(cuisine)) &
    (df["Segment"].isin(segment))
]

# ---------------- KPI SECTION ----------------
st.markdown("## 📌 Key Metrics")

total_profit = (
    filtered_df["InStoreNetProfit"].sum() +
    filtered_df["UberEatsNetProfit"].sum() +
    filtered_df["DoorDashNetProfit"].sum() +
    filtered_df["SelfDeliveryNetProfit"].sum()
)

commission_loss = (
    (filtered_df["UberEatsRevenue"] * filtered_df["CommissionRate"]).sum() +
    (filtered_df["DoorDashRevenue"] * filtered_df["CommissionRate"]).sum()
)

best_channel = pd.Series({
    "InStore": filtered_df["InStoreNetProfit"].sum(),
    "UberEats": filtered_df["UberEatsNetProfit"].sum(),
    "DoorDash": filtered_df["DoorDashNetProfit"].sum(),
    "SelfDelivery": filtered_df["SelfDeliveryNetProfit"].sum()
}).idxmax()

avg_margin = total_profit / filtered_df["InStoreRevenue"].sum() if filtered_df["InStoreRevenue"].sum() != 0 else 0

col1, col2, col3, col4 = st.columns(4)

def card(title, value):
    return f"""
    <div class='card'>
        <h4 style='color:#94A3B8'>{title}</h4>
        <h2>{value}</h2>
    </div>
    """

col1.markdown(card("💰 Total Profit", f"${total_profit:,.0f}"), unsafe_allow_html=True)
col2.markdown(card("📊 Avg Margin", f"{avg_margin:.2%}"), unsafe_allow_html=True)
col3.markdown(card("💸 Commission Loss", f"${commission_loss:,.0f}"), unsafe_allow_html=True)
col4.markdown(card("🏆 Best Channel", best_channel), unsafe_allow_html=True)

# ---------------- CHARTS ----------------
st.markdown("## 📈 Channel Performance")

col5, col6 = st.columns(2)

profit_df = pd.DataFrame({
    "Channel": ["InStore","UberEats","DoorDash","SelfDelivery"],
    "Profit": [
        filtered_df["InStoreNetProfit"].sum(),
        filtered_df["UberEatsNetProfit"].sum(),
        filtered_df["DoorDashNetProfit"].sum(),
        filtered_df["SelfDeliveryNetProfit"].sum()
    ]
})

fig1 = px.bar(profit_df, x="Channel", y="Profit", color="Channel", template="plotly_dark")
col5.plotly_chart(fig1, use_container_width=True)

revenue_df = pd.DataFrame({
    "Channel": ["InStore","UberEats","DoorDash","SelfDelivery"],
    "Revenue": [
        filtered_df["InStoreRevenue"].sum(),
        filtered_df["UberEatsRevenue"].sum(),
        filtered_df["DoorDashRevenue"].sum(),
        filtered_df["SelfDeliveryRevenue"].sum()
    ]
})

fig2 = px.pie(revenue_df, names="Channel", values="Revenue", template="plotly_dark")
col6.plotly_chart(fig2, use_container_width=True)

# ---------------- MARGIN ----------------
st.markdown("## 📊 Margin Analysis")

margin_df = pd.DataFrame({
    "Channel": ["InStore","UberEats","DoorDash","SelfDelivery"],
    "Margin": [
        filtered_df["InStoreNetProfit"].sum() / filtered_df["InStoreRevenue"].sum(),
        filtered_df["UberEatsNetProfit"].sum() / filtered_df["UberEatsRevenue"].sum(),
        filtered_df["DoorDashNetProfit"].sum() / filtered_df["DoorDashRevenue"].sum(),
        filtered_df["SelfDeliveryNetProfit"].sum() / filtered_df["SelfDeliveryRevenue"].sum()
    ]
})

fig3 = px.bar(margin_df, x="Channel", y="Margin", color="Channel", template="plotly_dark")
st.plotly_chart(fig3, use_container_width=True)

# ---------------- WHAT-IF ----------------
st.markdown("## 🔮 Scenario Analysis")

commission_input = st.slider("Commission Rate (%)", 0, 50, 20)
delivery_cost_input = st.slider("Delivery Cost per Order ($)", 0.0, 10.0, 3.0)

orders_col = "SelfDeliveryOrdersCount"
if orders_col not in filtered_df.columns:
    orders_col = "SelfDeliveryOrders"

filtered_df["AdjustedUberProfit"] = filtered_df["UberEatsRevenue"] * (1 - commission_input/100)

filtered_df["AdjustedSDProfit"] = (
    filtered_df["SelfDeliveryRevenue"] -
    (delivery_cost_input * filtered_df[orders_col])
)

adj_df = pd.DataFrame({
    "Channel": ["UberEats","SelfDelivery"],
    "Profit": [
        filtered_df["AdjustedUberProfit"].sum(),
        filtered_df["AdjustedSDProfit"].sum()
    ]
})

fig4 = px.bar(adj_df, x="Channel", y="Profit", color="Channel", template="plotly_dark")
st.plotly_chart(fig4, use_container_width=True)

# ---------------- AI INSIGHTS ----------------
st.markdown("## 🤖 AI-Generated Insights")

insights = generate_insights(filtered_df)

for insight in insights:
    st.markdown(f"- {insight}")

# ---------------- FOOTER ----------------
st.markdown("---")
st.markdown("🚀 Developed using Streamlit | Consulting Dashboard")
