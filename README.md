# Price Sense AI
**Live demo:** https://price-sense-ai-xlv53egdr3mquoteo5rslz.streamlit.app/

A prototype tool that answers one question for retailers: **"Should I run this promotion?"**

You describe a proposed promotion (product, discount, timing) and it returns a clear
recommendation (Run it / Consider it / Don't run it) backed by projected lift,
cannibalization, incremental profit, and risk — plus a chart of profit at every
discount level so you can find the optimal discount.

The product is **horizontal**: it works for a specialty nuts retailer, a beverage
brand, or a grocery chain. Adding a new industry is a single entry in the `CATALOGS`
dictionary.

## Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

Then open http://localhost:8501

## Note on the "intelligence"

This is a prototype with **simulated intelligence** — no real ML or sales data. It uses
a transparent economic model (price elasticity, margin give-up, cannibalization). In
production, the elasticity and baseline numbers would come from a model trained on the
retailer's real point-of-sale history; the recommendation logic stays the same.
