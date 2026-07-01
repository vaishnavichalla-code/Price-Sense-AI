import streamlit as st
import pandas as pd

st.set_page_config(page_title="Price Sense AI", layout="centered")

# ------------------------------------------------------------------
# CATALOGS  --  this is what makes the product "horizontal".
# Each business type has its own products, and each product carries a
# small data profile. To support a new industry, we just add an entry
# here -- no other code changes needed.
#
#   price       = normal selling price ($)
#   cost        = what it costs us to buy/make one ($)  -> margin = price - cost
#   base_units  = units normally sold in a week at full price
#   elasticity  = how strongly demand reacts to a discount (higher = more reactive)
# ------------------------------------------------------------------
CATALOGS = {
    "Specialty Nuts Retailer": {
        "Roasted Almonds (16oz)":    {"price": 12.00, "cost": 7.50, "base_units": 420, "elasticity": 4.2},
        "Salted Pistachios (16oz)":  {"price": 14.00, "cost": 9.00, "base_units": 380, "elasticity": 5.0},
        "Mixed Nuts Variety Pack":   {"price": 18.00, "cost": 11.00, "base_units": 250, "elasticity": 3.5},
    },
    "Beverage Brand": {
        "Sparkling Water (12pk)":    {"price": 8.00, "cost": 4.50, "base_units": 900, "elasticity": 5.5},
        "Cold Brew Coffee (6pk)":    {"price": 15.00, "cost": 8.00, "base_units": 500, "elasticity": 4.0},
        "Energy Drink (4pk)":        {"price": 10.00, "cost": 5.00, "base_units": 700, "elasticity": 4.8},
    },
    "Grocery Chain": {
        "Organic Eggs (dozen)":      {"price": 6.00, "cost": 4.00, "base_units": 1500, "elasticity": 3.0},
        "Whole Milk (1gal)":         {"price": 4.50, "cost": 3.20, "base_units": 2000, "elasticity": 3.5},
        "Sourdough Bread":           {"price": 5.50, "cost": 2.50, "base_units": 1100, "elasticity": 4.0},
    },
}

# How much each timing choice amplifies demand (holiday weeks sell more).
TIMING_FACTOR = {
    "This week": 1.0,
    "Next week": 1.0,
    "Holiday week": 1.3,
    "End of month": 1.1,
}


def analyze(data, discount, timing):
    """The fake 'brain'. Takes a product's data + the proposed promo,
    returns the four numbers and a recommendation."""
    price = data["price"]
    cost = data["cost"]
    base_units = data["base_units"]
    elasticity = data["elasticity"]

    # 1) LIFT: bigger discount -> more units. Holiday timing amplifies it.
    lift_pct = elasticity * discount * TIMING_FACTOR[timing]      # e.g. 1.6 * 25 * 1.0 = 40 (%)
    promo_units = base_units * (1 + lift_pct / 100)

    # 2) CANNIBALIZATION: a share of the *extra* units aren't truly new
    #    (stolen from other products or pulled forward). Deeper discount -> more.
    cannib_rate = min(0.50, 0.08 + 0.005 * discount)             # e.g. at 25% -> 0.205
    incremental_units = promo_units - base_units
    cannibalized_units = incremental_units * cannib_rate

    # 3) PROFIT: the honest comparison.
    new_price = price * (1 - discount / 100)
    baseline_margin = price - cost                               # profit per unit, no promo
    promo_margin = new_price - cost                              # profit per unit, discounted
    baseline_profit = base_units * baseline_margin               # a normal week
    promo_profit = promo_units * promo_margin                    # promo week (discount hits ALL units)
    # cannibalized units would have sold anyway at full margin, so subtract that lost profit
    lost_to_cannibalization = cannibalized_units * baseline_margin
    incremental_profit = promo_profit - baseline_profit - lost_to_cannibalization

    # 4) RISK: deeper discounts, thin/negative margins, high cannibalization = riskier.
    risk_score = discount * 1.5 + cannib_rate * 40
    if promo_margin <= 0:
        risk_score = 100                                         # selling below cost = maximum risk
    risk_score = min(100, risk_score)
    if risk_score >= 65:
        risk_label = "High"
    elif risk_score >= 40:
        risk_label = "Medium"
    else:
        risk_label = "Low"

    # RECOMMENDATION: based on whether it actually makes more money.
    if promo_margin <= 0:
        verdict = "Don't run it"
        reason = "This discount sells the product below cost — you lose money on every unit."
    elif incremental_profit > 0.05 * baseline_profit:
        verdict = "Run it"
        reason = "The extra volume more than pays for the margin you give up."
    elif incremental_profit > 0:
        verdict = "Consider it"
        reason = "It's marginally profitable — worth it only if you also value the traffic or shelf movement."
    else:
        verdict = "Don't run it"
        reason = "The margin you give up outweighs the extra sales, largely due to cannibalization."

    return {
        "lift_pct": lift_pct,
        "promo_units": promo_units,
        "extra_units": incremental_units,
        "cannibalized_units": cannibalized_units,
        "cannib_rate": cannib_rate,
        "incremental_profit": incremental_profit,
        "baseline_profit": baseline_profit,
        "promo_profit": promo_profit,
        "risk_label": risk_label,
        "verdict": verdict,
        "reason": reason,
    }


# ==================================================================
# PAGE
# ==================================================================
st.title("Price Sense AI")
st.caption("Should I run this promotion? Describe it below and get a data-backed recommendation.")
st.divider()

# --- Inputs -------------------------------------------------------
left, right = st.columns(2)
business = left.selectbox("Business type", list(CATALOGS.keys()))
timing = right.selectbox("Timing", list(TIMING_FACTOR.keys()))
product = st.selectbox("Product", list(CATALOGS[business].keys()))
discount = st.slider("Discount %", min_value=5, max_value=50, value=25, step=5)

# Show the product economics so the analysis feels grounded, not a black box.
_d = CATALOGS[business][product]
st.caption(
    f"{product}: sells for \\${_d['price']:.2f}, costs \\${_d['cost']:.2f} "
    f"(margin \\${_d['price'] - _d['cost']:.2f}), ~{_d['base_units']:,} units/week at full price."
)

# --- The button: only analyze when clicked ------------------------
if st.button("Analyze promotion"):
    data = CATALOGS[business][product]
    result = analyze(data, discount, timing)

    # Recommendation banner (color depends on the verdict)
    if result["verdict"] == "Run it":
        st.success(f"Recommendation: {result['verdict']}")
    elif result["verdict"] == "Consider it":
        st.warning(f"Recommendation: {result['verdict']}")
    else:
        st.error(f"Recommendation: {result['verdict']}")
    st.write(result["reason"])

    # The four numbers, shown as metric cards
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Projected lift", f"+{result['lift_pct']:.0f}%")
    c2.metric("Cannibalization", f"{result['cannib_rate']*100:.0f}%")
    c3.metric("Incremental profit", f"${result['incremental_profit']:,.0f}")
    c4.metric("Risk", result["risk_label"])

    # --- Chart: profit at every discount level ("what's the best discount?") ---
    st.subheader("Profit at different discount levels")
    sweep = {d: analyze(data, d, timing)["incremental_profit"] for d in range(5, 51, 5)}
    chart_df = pd.DataFrame({"Incremental profit ($)": sweep})
    chart_df.index.name = "Discount %"
    st.line_chart(chart_df)

    # Find and call out the single most profitable discount.
    best_discount = max(sweep, key=sweep.get)
    best_profit = sweep[best_discount]
    if best_profit > 0:
        st.info(
            f"Best discount for {product} ({timing}): **{best_discount}% off**, "
            f"worth about **${best_profit:,.0f}** in incremental profit. "
            f"You proposed {discount}% off."
        )
    else:
        st.info(
            f"No discount level is profitable for {product} right now — "
            f"even the best option ({best_discount}% off) loses money. "
            f"This product may not be a good promo candidate."
        )

# --- Transparency panel + footer (always shown) -------------------
with st.expander("How Price Sense AI works"):
    st.write(
        "This prototype uses a transparent economic model, not real sales data:\n\n"
        "- **Lift** is estimated from each product's price sensitivity (elasticity) and the discount depth.\n"
        "- **Cannibalization** discounts the extra volume that is merely pulled from other products or future weeks.\n"
        "- **Incremental profit** compares a promo week against a normal week, accounting for the margin "
        "given up on units you would have sold anyway.\n"
        "- **Risk** rises with discount depth, thin margins, and cannibalization.\n\n"
        "In production, the elasticity and baseline numbers would come from a model trained on the "
        "retailer's real point-of-sale history. The recommendation logic stays the same."
    )

st.divider()
st.caption("Price Sense AI - prototype with simulated intelligence. For demonstration only.")
