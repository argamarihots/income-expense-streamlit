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
    """
    Retrieve all data from the 'transactions' table in Supabase
    and convert it into a pandas DataFrame.

    Returns:
        pd.DataFrame:
            - If data exists → returns DataFrame with data
            - If empty → returns an empty DataFrame with predefined columns
    """
    response = supabase.table("transactions").select("*").execute()
    df = pd.DataFrame(response.data)

    if df.empty:
        return pd.DataFrame(columns=[
            "no","date","income_expense","category",
            "subcategory","account","amount","notes"
        ])

    return df

def insert_data(data):
    """
    Insert new data into the 'transactions' table.

    Args:
        data (dict or list of dict):
            The data to be inserted into the database.
            Must match the table schema.
    """
    supabase.table("transactions").insert(data).execute()

def delete_data(no):
    """
    Delete a record from the 'transactions' table based on the 'no' column.

    Args:
        no (int or str):
            Unique identifier used to determine which record to delete.
    """
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
    """
    Main function to run the Streamlit Income Expense Tracker app.

    This function handles:
    - Initialization of session state variables
    - Password authentication
    - Loading transaction data from the database

    Session State Variables:
        success_msg (str or None):
            Stores success message for user feedback

        show_success (bool):
            Controls visibility of success notification

        form_reset (bool):
            Triggers form reset after submission

        delete_no (str):
            Stores the 'no' value of the record to be deleted

        delete_reset (bool):
            Controls reset state for delete input

        delete_success (bool):
            Indicates if delete operation was successful

        delete_warning (bool):
            Triggers warning message before deletion

    Security:
        - Requires password input before accessing the app
        - Password is validated using Streamlit secrets

    Workflow:
        1. Initialize session state variables
        2. Prompt user for password
        3. Validate password
        4. Load transaction data
    """
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
    # TRANSFER FORM
    # =========================
    st.subheader("💸 Transfer Between Accounts")

    # Gunakan akun dari form utama
    with st.form("transfer_form", clear_on_submit=True): 
        """
        Transfer form to move balance between accounts (e.g., CASH ↔ BANK).
            Features:
                - User selects source (From) and destination (To) account
                - Inputs transfer amount and optional notes
                - Validates input before saving
                - Records double-entry transactions:
                    1. Negative amount from source account
                    2. Positive amount to destination account
        """
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
             # --- Saved Transaction Data (Before Rerun) ---
                # Load existing data to determine the next transaction number
                df_temp = load_data()
                next_no = 1
                 # If data exists, increment from the current maximum 'no'
                if not df_temp.empty:
                    next_no = int(df_temp["no"].max()) + 1
                    
               # Insert negative transaction (deduct from source account)
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
                
                # Insert positive transaction (add to destination account)
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
                
                # Set success message flag and trigger app rerun
                st.session_state.success_msg = "transfer_success"
                st.rerun()
    # =========================
    # RELOAD DATA
    # =========================
    df = load_data()

    if not df.empty:
        # Convert 'date' column to datetime format
        df["date"] = pd.to_datetime(df["date"], format="%d/%m/%Y", errors="coerce")

        # Remove rows with missing critical values
        df = df.dropna(subset=["date","amount","category","account"])

        # Convert datetime to date only (remove time component)
        df["date"] = df["date"].dt.date 

        # Sort data by date
        df = df.sort_values("date")

    # =========================
    # DATE FILTER
    # =========================
    st.subheader("Summary By Date")

    if not df.empty:
        col1, col2 = st.columns(2)

        with col1:
            # Select start date (minimum available date)
            from_date = st.date_input("Dari", min(df["date"]))

        with col2:
            # Select end date (maximum available date)
            to_date = st.date_input("Sampai", max(df["date"]))

        # Filter data based on selected date range
        df = df[
            (df["date"] >= from_date) &
            (df["date"] <= to_date)
        ]

    # =========================
    # SUMMARY
    # =========================
    if not df.empty:
        # Calculate total income and expense
        income = df[df["income_expense"]=="INCOME"]["amount"].sum()
        expense = df[df["income_expense"]=="EXPENSE"]["amount"].sum()
        
        # Display summary metrics
        col1, col2, col3 = st.columns(3)
        col1.metric("Income", f"{income:,.0f}")
        col2.metric("Expense", f"{abs(expense):,.0f}")
        col3.metric("Balance", f"{income + expense:,.0f}")

    # =========================
    # INCOME ANALYSIS
    # =========================
    st.subheader("📊 INCOME")

    # Filter only income transactions
    income_df = df[df["income_expense"]=="INCOME"]

    if not income_df.empty:
        # Multi-select filter for income categories
        selected_income = st.multiselect(
            "Income Category",
            income_categories,
            default=income_categories
        )
        
         # Apply category filter
        income_df = income_df[income_df["category"].isin(selected_income)]

        # Create pie chart data (sum by category)
        pie_income = income_df.groupby("category")["amount"].sum()

        if not pie_income.empty:
            # Plot pie chart for income distribution
            fig, ax = plt.subplots()
            pie_income.plot.pie(
                autopct="%1.1f%%",
                ax=ax,
                ylabel=""
            )
            st.pyplot(fig)

        # Create stacked bar chart (date vs category)
        bar_income = income_df.pivot_table(
            index="date",
            columns="category",
            values="amount",
            aggfunc="sum"
        ).fillna(0)

        bar_income.index = bar_income.index.astype(str)  

        # Display bar chart
        st.bar_chart(bar_income)

         # Display detailed income table
        st.dataframe(income_df.style.format({"amount": "{:,.0f}"}), hide_index=True)

    # =========================
    # EXPENSE
    # =========================
    st.subheader("📉 Expenses")

    # Filter only expense transactions
    expense_df = df[df["income_expense"]=="EXPENSE"]

     # Multi-select filter for expense categories    
    if not expense_df.empty:
        selected_exp = st.multiselect(
            "Expense Category",
            expense_categories,
            default=expense_categories
        )

        # Apply category filter
        expense_df = expense_df[expense_df["category"].isin(selected_exp)]

         # Prepare data for pie chart (absolute values for visualization)
        pie_exp = expense_df.groupby("category")["amount"].sum().abs()

        if not pie_exp.empty:
            # Plot pie chart for expense distribution
            fig, ax = plt.subplots()
            pie_exp.plot.pie(
                autopct="%1.1f%%",
                ax=ax,
                ylabel=""
            )
            st.pyplot(fig)
            
        # Create stacked bar chart (date vs category)
        bar_exp = expense_df.pivot_table(
            index="date",
            columns="category",
            values="amount",
            aggfunc="sum"
        ).fillna(0).abs()
        
        # Convert date index to string for better display
        bar_exp.index = bar_exp.index.astype(str) 

        # Display bar chart
        st.bar_chart(bar_exp)

        # Display detailed expense table
        st.dataframe(expense_df.style.format({"amount": "{:,.0f}"}), hide_index=True)

    # =========================
    # ACCOUNT
    # =========================
    st.subheader("💵 Balance Per Account")

    if not df.empty:
        # Aggregate total balance per account
        acc = df.groupby("account", as_index=False)["amount"].sum()

        # Set account as index for visualization
        acc = acc.set_index("account")
        acc.index = acc.index.astype(str)

        # Display bar chart of account balances
        st.bar_chart(acc)

    # =========================
    # TRANSACTION TABLE
    # =========================
    st.subheader("Transaction Data")

    # Display full transaction table with formatted amount
    st.dataframe(
        df.style.format({
            "amount": "{:,.0f}" # Menambahkan koma/titik sebagai pemisah ribuan
        }), 
        use_container_width=True
    )

    # =========================
    # DELETE TRANSACTION
    # =========================
    with st.form("delete_form", clear_on_submit=True):
            # Input transaction number to delete
            delete_no = st.number_input("Input no to delete", min_value=0, step=1, value=0)

            # Delete button
            delete_clicked = st.form_submit_button("Delete Now")
            
            if delete_clicked:
                 # Validate input before deleting
                if delete_no > 0:
                    delete_data(int(delete_no))

                    # Set success flag and refresh app
                    st.session_state.success_msg = "delete_success"
                    st.rerun()
                else:
                    st.warning("Please input a valid number!")
    
    # Display success message after deletion                
    if st.session_state.get("success_msg") == "delete_success":
        st.success("🗑️ Data Successfully Deleted!")
        st.session_state.success_msg = None

# =========================
# RUN
# =========================
if __name__ == "__main__":
    main()
