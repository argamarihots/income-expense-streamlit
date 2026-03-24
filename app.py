import streamlit as st
import pandas as pd
from datetime import datetime
from supabase import create_client, Client
import matplotlib.pyplot as plt

# =========================
# CONFIG (CONNECTING TO DATABASE)
# =========================
SUPABASE_URL = "https://xwagkyijvshtswqlhhad.supabase.co".strip()
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inh3YWdreWlqdnNodHN3cWxoaGFkIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzM5MTIxOTcsImV4cCI6MjA4OTQ4ODE5N30.TzlsgET51JzMG8d2daS6SX3Lr7OFXLJHPgJiDtymJUE".strip()
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# =========================
# LOAD DATA
# =========================
def load_data():
    response = supabase.table("transactions").select("*").execute()
    df = pd.DataFrame(response.data)

    if df.empty:
        return pd.DataFrame(columns=[
            "no","date","income_expense","category",
            "subcategory","account","amount","notes"
        ])

    return df

def insert_data(data):
    supabase.table("transactions").insert(data).execute()

def delete_data(no):
    supabase.table("transactions").delete().eq("no", no).execute()

# =========================
# CATEGORY
# =========================
expense_categories = sorted([
    "🛒 Other Shopping","💳 Other Expense","🧾 Loan",
    "🍔 Food & Beverage","🧺 Laundry","🏥 Hospital",
    "🎓 Education","🚗 Vehicle ","🚌 Transportation",
    "🎉 Entertainment","🛠 Service & Maintenance","🏠 House",
    "💡 Utilities","📱 Internet & Phone","🐶 Pet",
    "👕 Outfit","💊 Medical","🧹 Cleaning"
])

income_categories = sorted([
    "💰 Salary","📝 Freelance","📈 Other Income",
    "🏦 Bank Interest","🎁 Bonus"
])

all_categories = sorted(list(set(income_categories + expense_categories)))

# =========================
# MAIN
# =========================
def main():
    # INITIALIZE
    if "show_success" not in st.session_state:
        st.session_state.show_success = False
        
    if "form_reset" not in st.session_state:
        st.session_state.form_reset = False

    if "delete_no" not in st.session_state:
        st.session_state.delete_no = ""
        
    if "delete_reset" not in st.session_state:
        st.session_state.delete_reset = False
    
    if "delete_success" not in st.session_state:
        st.session_state.delete_success = False
        
    if "delete_warning" not in st.session_state:
        st.session_state.delete_warning = False
        
    st.title("💰 Income Expense Tracker")
    
    # 🔐 PASSWORD PROTECTION 
    password = st.text_input("Input Password", type="password")
    if password: 
        if password != "Juntak389":
            st.warning("Wrong Password!")
            st.stop()
    else:
        st.info('Input Password')
        st.stop()


    df = load_data()

    # =========================
    # INPUT
    # =========================
    st.subheader("Add Transaction")
    
    # reset form
    if st.session_state.get("form_reset", False): 
        st.session_state.ie = ""
        st.session_state.cat = ""
        st.session_state.subcat = ""
        st.session_state.acc = "CASH"
        st.session_state.amt = 0.0
        st.session_state.notes = ""
    
        st.session_state.form_reset = False

    with st.form("form"):
        col1, col2 = st.columns(2)

        with col1:
            date_input = st.date_input("Date")

            income_expense = st.selectbox(
                "Income/Expense",
                ["","INCOME","EXPENSE"],
                key="ie"
            )

            category = st.selectbox("Category",[""] + all_categories, key="cat")
            subcategory = st.text_input("Subcategory", key="subcat")

        with col2:
            account = st.selectbox("Account", ["CASH", "BANK"], key="acc")
            amount = st.number_input("Amount", min_value=0.0, step=1000.0, key="amt")
            notes = st.text_area("Notes", key="notes")

        submit = st.form_submit_button("Submit")

        if submit:
            next_no = 1
            if not df.empty:
                next_no = int(df["no"].max()) + 1

            if income_expense == "EXPENSE":
                amount = -abs(amount)
            else:
                amount = abs(amount)

            insert_data({
                "no": next_no,
                "date": date_input.strftime("%d/%m/%Y"),
                "income_expense": income_expense,
                "category": category,
                "subcategory": subcategory,
                "account": account,
                "amount": amount,
                "notes": notes
            })
            st.session_state.show_success = True
            st.session_state.form_reset = True
            st.rerun()
            
    if st.session_state.get("show_success", False):
        st.success("Data successfully saved!")
        st.session_state.show_success = False

    st.markdown("---") 
    

    # =========================
    # LOAD ULANG
    # =========================
    df = load_data()

    if not df.empty:
        df["date"] = pd.to_datetime(df["date"], format="%d/%m/%Y", errors="coerce")
        df = df.dropna(subset=["date","amount","category","account"])
        df["date"] = df["date"].dt.date  # ✅ FIX HILANGIN JAM
        df = df.sort_values("date")

    # =========================
    # FILTER TANGGAL
    # =========================
    st.subheader("Summary By Date")

    if not df.empty:
        col1, col2 = st.columns(2)

        with col1:
            from_date = st.date_input("Dari", min(df["date"]))

        with col2:
            to_date = st.date_input("Sampai", max(df["date"]))

        df = df[
            (df["date"] >= from_date) &
            (df["date"] <= to_date)
        ]

    # =========================
    # SUMMARY
    # =========================
    if not df.empty:
        income = df[df["income_expense"]=="INCOME"]["amount"].sum()
        expense = df[df["income_expense"]=="EXPENSE"]["amount"].sum()

        col1, col2, col3 = st.columns(3)
        col1.metric("Income", f"{income:,.0f}")
        col2.metric("Expense", f"{abs(expense):,.0f}")
        col3.metric("Balance", f"{income + expense:,.0f}")

    # =========================
    # INCOME
    # =========================
    st.subheader("📊 INCOME")

    income_df = df[df["income_expense"]=="INCOME"]

    if not income_df.empty:
        selected_income = st.multiselect(
            "Income Category",
            income_categories,
            default=income_categories
        )

        income_df = income_df[income_df["category"].isin(selected_income)]

        pie_income = income_df.groupby("category")["amount"].sum()

        if not pie_income.empty:
            fig, ax = plt.subplots()
            pie_income.plot.pie(
                autopct="%1.1f%%",
                ax=ax,
                ylabel=""
            )
            st.pyplot(fig)

        # ✅ STACKED BAR FIX
        bar_income = income_df.pivot_table(
            index="date",
            columns="category",
            values="amount",
            aggfunc="sum"
        ).fillna(0)

        bar_income.index = bar_income.index.astype(str)  # ✅ FIX BUG STREAMLIT

        st.bar_chart(bar_income)

        st.dataframe(income_df)

    # =========================
    # EXPENSE
    # =========================
    st.subheader("📉 Expenses")

    expense_df = df[df["income_expense"]=="EXPENSE"]

    if not expense_df.empty:
        selected_exp = st.multiselect(
            "Expense Category",
            expense_categories,
            default=expense_categories
        )

        expense_df = expense_df[expense_df["category"].isin(selected_exp)]

        pie_exp = expense_df.groupby("category")["amount"].sum().abs()

        if not pie_exp.empty:
            fig, ax = plt.subplots()
            pie_exp.plot.pie(
                autopct="%1.1f%%",
                ax=ax,
                ylabel=""
            )
            st.pyplot(fig)

        # ✅ STACKED BAR FIX
        bar_exp = expense_df.pivot_table(
            index="date",
            columns="category",
            values="amount",
            aggfunc="sum"
        ).fillna(0).abs()

        bar_exp.index = bar_exp.index.astype(str)  # ✅ FIX BUG STREAMLIT

        st.bar_chart(bar_exp)

        st.dataframe(expense_df)

    # =========================
    # ACCOUNT
    # =========================
    st.subheader("💵 Balance Per Account")

    if not df.empty:
        acc = df.groupby("account", as_index=False)["amount"].sum()
        acc = acc.set_index("account")
        acc.index = acc.index.astype(str)  # ✅ FIX BUG

        st.bar_chart(acc)

    # =========================
    # TABLE
    # =========================
    st.subheader("Transaction Data")
    st.dataframe(df, use_container_width=True)

    # =========================
    # DELETE
    # =========================
    st.subheader("Delete Data")
    
    #Reset Input
    if st.session_state.get("delete_reset", False):
        st.session_state.delete_no = ""
        st.session_state.delete_reset = False
    # input
    delete_no = st.text_input("Input no", key="delete_no")
    
    delete_clicked = st.button("Delete")
    # logic Click
    if delete_clicked:
        if delete_no:
            delete_data(int(delete_no))

        st.session_state.delete_success = True
        st.session_state.delete_reset = True
        st.rerun()
    
    
    if st.session_state.get("delete_warning", False):
        st.warning("Please Input Number!")
        st.session_state.delete_warning = False

    if st.session_state.get("delete_success", False):
        st.success("Data Successfully Deleted!")
        st.session_state.delete_success = False

# =========================
# RUN
# =========================
if __name__ == "__main__":
    main()