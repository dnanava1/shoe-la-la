import streamlit as st
from nlp.llm_client import parse_shopping_intent
from database.queries import handle_view_details_query
from analysis.dashboard import render_analysis_dashboard

# ----- Streamlit UI -----
st.set_page_config(page_title="Nike Shoe Assistant", layout="wide")

st.title("👟 Nike Shoe Assistant")
st.write("Ask me about Nike shoes or explore market insights!")

# Sidebar for navigation
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["Chatbot", "Market Analysis"])

if page == "Chatbot":
    # Keep chat state
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display existing messages
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # User input
    if prompt := st.chat_input("Ask about Nike shoes..."):
        # Display user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Show loading spinner
        with st.chat_message("assistant"):
            with st.spinner("🔍 Searching for shoes..."):
                # Call intent classifier
                intent_json = parse_shopping_intent(prompt)

                # Handle intent
                if intent_json["intent"] == "view_details":
                    result = handle_view_details_query(intent_json)
                    if result:
                        name, color, size_label, price, original_price, discount_percent, color_url = result
                        response = f"""**{name}**

🎨 **Color**: {color}
📏 **Size**: {size_label}
💰 **Price**: ${price}
🏷️ **Original**: ${original_price}
🎯 **Discount**: {discount_percent}%

[🔗 View Product]({color_url})"""
                    else:
                        response = "❌ Sorry, I couldn't find a matching shoe. Try being more specific!"
                elif intent_json["intent"] == "search":
                    response = "🔍 I can help you search! Currently I'm optimized for detailed product lookups. Try asking about a specific shoe model with color and size."
                elif intent_json["intent"] == "recommend":
                    response = "💡 I can recommend shoes! Currently I'm optimized for detailed product lookups. Try asking about specific features you want."
                else:
                    response = "🤔 I'm not sure how to help with that. Try asking about specific Nike shoes with details like color, size, or model."

            # Display assistant response after spinner finishes
            st.markdown(response)

        # Save assistant message
        st.session_state.messages.append({"role": "assistant", "content": response})

else:  # Market Analysis page
    render_analysis_dashboard()