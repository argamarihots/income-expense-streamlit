import streamlit as st
import pandas as pd
from datetime import datetime
from supabase import create_client, Client
import matplotlib.pyplot as plt

# =========================
# CONFIG (CONNECTING TO DATABASE)
# =========================
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
APP_PASSWORD = st.secrets["APP_PASSWORD"]
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
    if "success_msg" not in st.session_state:
        st.session_state.success_msg = None
    st.title("💰 Income Expense Tracker")
    
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
        
    
    # 🔐 PASSWORD PROTECTION 
    password = st.text_input("Input Password", type="password")
    if password: 
        if password != st.secrets["APP_PASSWORD"]:
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

    with st.form("form", clear_on_submit=True):
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
            amount = st.number_input("Amount", min_value=0.0, step=1000.0, format="%.0f",key="amt") 
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
    # TRANSFER FORM (BARU)
    # =========================
    st.subheader("💸 Transfer Between Accounts")

    # Gunakan akun dari form utama
    with st.form("transfer_form", clear_on_submit=True): 
        t_col1, t_col2 = st.columns(2)
        with t_col1:
            transfer_from = st.selectbox("From Account", ["CASH", "BANK"])
            transfer_amount =st.number_input("Transfer Amount", min_value=0.0, step=1000.0, format="%.0f",key="transfer_amt") 
            
        with t_col2:
            transfer_to = st.selectbox("To Account", ["BANK", "CASH"]) # Default beda biar gak error
            transfer_notes = st.text_input("Notes (optional)")
        
        transfer_submit = st.form_submit_button("Confirm Transfer")

        if transfer_submit:
            if transfer_from == transfer_to:
                st.error("❌ From and To Account cannot be the same!")    
            elif transfer_amount <= 0:
                st.error("❌ Amount must be greater than 0!")    
            else:
             # --- PROSES SIMPAN DATA DI SINI (SEBELUM RERUN) ---
                df_temp = load_data()
                next_no = 1
                if not df_temp.empty:
                    next_no = int(df_temp["no"].max()) + 1
                # 1. Simpan Minus (Dari Akun Asal)
                insert_data({
                    "no": next_no,
                    "date": datetime.today().strftime("%d/%m/%Y"),
                    "income_expense": "TRANSFER",
                    "category": "Transfer",
                    "subcategory": f"To {transfer_to}",
                    "account": transfer_from,
                    "amount": -abs(transfer_amount),
                    "notes": transfer_notes
                })
                
                # 2. Simpan Plus (Ke Akun Tujuan)
                insert_data({
                    "no": next_no + 1,
                    "date": datetime.today().strftime("%d/%m/%Y"),
                    "income_expense": "TRANSFER",
                    "category": "Transfer",
                    "subcategory": f"From {transfer_from}",
                    "account": transfer_to,
                    "amount": abs(transfer_amount),
                    "notes": transfer_notes
                })
                
                # Set label sukses lalu refresh
                st.session_state.success_msg = "transfer_success"
                st.rerun()
    # =========================
    # LOAD ULANG
    # =========================
    df = load_data()

    if not df.empty:
        df["date"] = pd.to_datetime(df["date"], format="%d/%m/%Y", errors="coerce")
        df = df.dropna(subset=["date","amount","category","account"])
        df["date"] = df["date"].dt.date 
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

        # STACKED BAR
        bar_income = income_df.pivot_table(
            index="date",
            columns="category",
            values="amount",
            aggfunc="sum"
        ).fillna(0)

        bar_income.index = bar_income.index.astype(str)  

        st.bar_chart(bar_income)

        st.dataframe(income_df.style.format({"amount": "{:,.0f}"}), hide_index=True)

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
        #Stacked bar
        bar_exp = expense_df.pivot_table(
            index="date",
            columns="category",
            values="amount",
            aggfunc="sum"
        ).fillna(0).abs()

        bar_exp.index = bar_exp.index.astype(str) 

        st.bar_chart(bar_exp)

        st.dataframe(expense_df.style.format({"amount": "{:,.0f}"}), hide_index=True)

    # =========================
    # ACCOUNT
    # =========================
    st.subheader("💵 Balance Per Account")

    if not df.empty:
        acc = df.groupby("account", as_index=False)["amount"].sum()
        acc = acc.set_index("account")
        acc.index = acc.index.astype(str)
        st.bar_chart(acc)

    # =========================
    # TABLE
    # =========================
    st.subheader("Transaction Data")
    st.dataframe(
        df.style.format({
            "amount": "{:,.0f}" # Menambahkan koma/titik sebagai pemisah ribuan
        }), 
        use_container_width=True
    )

    # =========================
    # DELETE
    # =========================
    with st.form("delete_form", clear_on_submit=True):
            delete_no = st.number_input("Input no to delete", min_value=0, step=1, value=0)
            delete_clicked = st.form_submit_button("Delete Now")
            
            if delete_clicked:
                if delete_no > 0:
                    delete_data(int(delete_no))
                    st.session_state.success_msg = "delete_success"
                    st.rerun()
                else:
                    st.warning("Please input a valid number!")
                    
    if st.session_state.get("success_msg") == "delete_success":
        st.success("🗑️ Data Successfully Deleted!")
        st.session_state.success_msg = None

# =========================
# RUN
# =========================
if __name__ == "__main__":
    main()