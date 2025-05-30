import streamlit as st
from assisstant import get_product_info, ProductInfo

st.title("Product Info Assistant")

user_query = st.text_input("Ask about a product:", "")

if user_query:
    try:
        info: ProductInfo = get_product_info(user_query)
        st.subheader(f"Product: {info.product_name}")
        st.write(f"Details: {info.product_details}")
        st.write(f"Price (USD): ${info.price_usd}")
    except Exception as e:
        st.error(f"Sorry, something went wrong: {e}")
