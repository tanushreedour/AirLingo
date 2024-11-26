import streamlit as st
from PIL import Image
import time
import os
import requests
from dotenv import load_dotenv
from azure.core.credentials import AzureKeyCredential
from azure.ai.vision.imageanalysis import ImageAnalysisClient
from azure.ai.vision.imageanalysis.models import VisualFeatures
from azure.ai.textanalytics import TextAnalyticsClient
import google.generativeai as genai
from azure.ai.translation.text import *
from azure.ai.translation.text.models import InputTextItem

# Load environment variables
load_dotenv()

# Initialize Azure and Gemini API details
ai_endpoint = os.getenv('AI_SERVICE_ENDPOINT')
ai_key = os.getenv('AI_SERVICE_KEY')
ai_region = os.getenv('REGION')
gemini_api_key = os.getenv('GEMINI_API_KEY')
exchange_key = os.getenv('EXCHANGE_RATE_API_KEY')

# Create client using endpoint and key
translation_credential = TranslatorCredential(ai_key, ai_region)
translation_client = TextTranslationClient(translation_credential)

# Create client using endpoint and key
credential = AzureKeyCredential(ai_key)
ai_client = TextAnalyticsClient(endpoint=ai_endpoint, credential=credential)

# Authenticate Azure AI Vision client
cv_client = ImageAnalysisClient(
    endpoint=ai_endpoint,
    credential=AzureKeyCredential(ai_key)
)

# Configure Generative AI API
genai.configure(api_key=gemini_api_key)
model = genai.GenerativeModel("gemini-pro")

# Sidebar Navigation
def sidebar_navigation():
    st.sidebar.title("🌍 AirLingo")
    st.sidebar.image("sidebar.jpg", use_column_width=True)  # Placeholder for logo
    st.sidebar.markdown("**Travel Smarter, Globally.**")
    st.sidebar.markdown("---")
    menu = st.sidebar.radio(
        "Navigate",
        ["Home", "Text Extraction", "Translation", "Chatbot", "Currency Conversion"],
        index=0,
        format_func=lambda x: f"📌 {x}"
    )
    st.sidebar.markdown("---")
    st.sidebar.write("🔗 **Useful Links:**")
    st.sidebar.write("- [Azure Services](https://azure.microsoft.com/)")
    st.sidebar.write("- [Gemini API](https://google.com)")
    return menu

# Header
def display_header(title):
    st.title(f"🌟 {title}")
    st.markdown(f"<p style='text-align: center; font-size: 18px;'>Elevating your travel experience with cutting-edge AI.</p>", unsafe_allow_html=True)

# Footer
def display_footer():
    st.markdown("---")
    st.markdown(
        """
        <footer style="text-align: center; color: gray; font-size: small;">
            Powered by Azure, Gemini, and your innovation. © 2024 AirLingo. All Rights Reserved.
        </footer>
        """, unsafe_allow_html=True
    )

# Home Page
def home_page():
    display_header("Welcome to AirLingo!")
    st.image("homePage.jpg", use_column_width=True)  # Placeholder for banner
    st.markdown(
        """
        **Why AirLingo?**
        - Scan menus and documents in any language and translate them instantly.
        - A personal assistant for every step of your journey.
        - Find nearby restaurants, parks, and hotels with ease.
        - Real-time currency conversion with global support.
        """
    )
    st.success("Your ultimate travel companion is just a click away. Explore the features using the sidebar.")

# Function to extract text using Azure's OCR service
def GetTextRead(image_data):
    st.info("Extracting text...")

    result = cv_client.analyze(
        image_data=image_data,
        visual_features=[VisualFeatures.READ]
    )

    extracted_text_list = []
    for block in result.read.blocks:
        for line in block.lines:
            st.markdown(f"**{line.text}**")
            extracted_text_list.append(line.text)

    return " ".join(extracted_text_list)

# Text Extraction Page
def text_extraction_page():
    display_header("Text Extraction")
    st.markdown("Upload an image to extract text in multiple languages.")
    image = st.file_uploader("Upload an image (JPG, PNG)", type=["jpg", "jpeg", "png"])
    if image:
        st.image(Image.open(image), caption="Uploaded Image", use_column_width=True)
        st.info("Processing...")
        with st.spinner("Extracting text..."):
            time.sleep(2)  # Simulate processing time
            st.subheader("Extracted Text:")
            image_bytes = image.getvalue()
            extracted_text = GetTextRead(image_bytes)

            # Save extracted text to session state for use in the entity search page
            st.session_state['extracted_text'] = extracted_text
            st.success("Text extracted and saved successfully!")
        # st.write("Here's the extracted text: **[Sample Text Here]**")  # Replace with actual text from OCR function

# Translation Page
def translation_page():
    display_header("Translation")
    # Check if text has been extracted
    if 'extracted_text' in st.session_state:
        text_to_translate = st.session_state['extracted_text']
    else:
        text_to_translate = st.text_area("Enter the text to translate:")
    detectedLanguage = ai_client.detect_language(documents=[text_to_translate])[0]
    # target_language = st.selectbox("Choose target language", ["French", "Spanish", "German", "Hindi", "English", "Japanese"])
    
    ## Choose target language
    languagesResponse = translation_client.get_languages(scope="translation")
    st.write("{} languages supported.".format(len(languagesResponse.translation)))
    st.write("(See https://learn.microsoft.com/azure/ai-services/translator/language-support#translation)")
    targetLanguage = st.text_input("Enter a target language code for translation (for example, 'en'):")
    # targetLanguage = "xx"
    # supportedLanguage = False
    # while supportedLanguage == False:
    if targetLanguage not in languagesResponse.translation.keys():
        # supportedLanguage = True
        time.sleep(2)
        st.error("{0} is not a supported language.".format(targetLanguage))
    # else:
    #     st.error("{0} is not a supported language.".format(targetLanguage))
    
    if st.button("Translate"):
        with st.spinner("Translating..."):
            time.sleep(2)  # Simulate processing time
            input_text_elements = [InputTextItem(text=text_to_translate)]
            translationResponse = translation_client.translate(content=input_text_elements, to=[targetLanguage])
            translation = translationResponse[0] if translationResponse else None
            if translation:
                for translated_text in translation.translations:
                    # print(f"'{inputText}' was translated from {detectedLanguage.primary_language.name} to {translated_text.to} as '{translated_text.text}'.")
                    st.write(f"Translated text ({targetLanguage}): **{translated_text.text}**")  # Replace with actual translation
        st.success("Translation completed!")

# Chatbot Page
# def chatbot_page_original():
#     display_header("Chatbot")
#     st.markdown("Your AI travel guide is here to assist you!")
    
#     # Set a default model
#     if "gemini_model" not in st.session_state:
#         st.session_state["gemini_model"] = "gemini-pro"

#     # Initialize chat history
#     if "messages" not in st.session_state:
#         st.session_state.messages = []

#     # Display chat messages from history on app rerun
#     for message in st.session_state.messages:
#         with st.chat_message(message["role"]):
#             st.markdown(message["content"])
    
#     # if prompt := st.chat_input("Say something"):
#     #     # System message with query context
#     #     system_message = f"""You are a virtual travel companion. Assist users with their travel-related queries."""
                
#     #     # Gemini model response
#     #     response = model.generate_content(prompt)
        
#     #     # messages.chat_message("user").write(prompt)
#     #     # messages.chat_message("assistant").write(f"Assistant: {response}")
        
#     #     st.chat_message("user").write(prompt)
#     #     st.chat_message("assistant").write(f"Assistant: {response.text}")
    
#     if prompt := st.chat_input("What is up?"):
#         st.session_state.messages.append({"role": "user", "content": prompt})
#         with st.chat_message("user"):
#             st.markdown(prompt)

        
#     # Display assistant response in chat message container
#         with st.chat_message("assistant"):
#             stream = model.generate_content(
#                 # messages=[
#                 #     {"role": m["role"], "content": m["content"]}
#                 #     for m in st.session_state.messages,
#                 # stream=True,
#                 st.session_state.messages
                    
#             )
#             response = st.write_stream(stream)
#         st.session_state.messages.append({"role": "assistant", "content": response})

# ---------------------Chatbot Page------------------
def chatbot_page():
    display_header("Chatbot")
    st.markdown("Your AI travel guide is here to assist you!")

    # Set a default Gemini model
    if "gemini_model" not in st.session_state:
        st.session_state["gemini_model"] = "gemini-pro"

    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display chat messages from history on app rerun
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Handle user input
    if prompt := st.chat_input("Ask your travel guide anything:"):
        # Add user's message to the chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Simulate assistant processing
        # with st.spinner("Your assistant is thinking..."):
            # time.sleep(2)  # Simulate processing time
            # Replace with actual call to Gemini model
            response = model.generate_content(prompt)
            # st.chat_message("assistant").write(f"Assistant: {response.text}")

        # Display assistant response
        with st.chat_message("assistant"):
            st.markdown(response.text)

        # Add assistant's response to the chat history
        st.session_state.messages.append({"role": "assistant", "content": response.text})

# Currency Conversion Page
def currency_conversion_page():
    display_header("Currency Converter")
    st.markdown("""
    Convert currencies seamlessly across the globe in real-time. 
    Powered by robust API integrations to ensure accuracy.
    """)
    # from_currency = st.selectbox("From Currency", ["USD", "EUR", "INR"])
    # to_currency = st.selectbox("To Currency", ["USD", "EUR", "INR"])
    # amount = st.number_input("Enter amount to convert", min_value=0.0, format="%.2f")
    # if st.button("Convert"):
    #     with st.spinner("Converting..."):
    #         time.sleep(2)  # Simulate processing time
    #     st.success(f"Converted Amount: **[Sample Conversion] {to_currency}**")  # Replace with actual conversion

    # Fetch currency list
    currency_list = fetch_currency_list(exchange_key)
    if not currency_list:
        st.stop()  # Stop execution if currency list fetch fails

    # Input Section
    st.subheader("💱 Conversion Details")
    from_currency = st.selectbox("From Currency", options=currency_list)
    to_currency = st.selectbox("To Currency", options=currency_list)
    amount = st.number_input("Amount to Convert", min_value=0.0, format="%.2f")

    # Extract currency codes from selection
    from_currency_code = from_currency.split(" - ")[0]
    to_currency_code = to_currency.split(" - ")[0]

    # Conversion Button
    if st.button("Convert"):
        if amount > 0:
            result = convert_currency(exchange_key, from_currency_code, to_currency_code, amount)
            if result is not None:
                st.success(f"💵 {amount} {from_currency_code} = {result:.2f} {to_currency_code}")
        else:
            st.warning("Please enter a valid amount.")
    
# Function to fetch available currencies
def fetch_currency_list(api_key):
    try:
        url = f"https://v6.exchangerate-api.com/v6/{api_key}/codes"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        return [f"{code} - {name}" for code, name in data["supported_codes"]]
    except Exception as e:
        st.error(f"Error fetching currency list: {e}")
        return []

# Function to convert currency
def convert_currency(api_key, from_currency, to_currency, amount):
    try:
        url = f"https://v6.exchangerate-api.com/v6/{api_key}/pair/{from_currency}/{to_currency}/{amount}"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        return data["conversion_result"]
    except Exception as e:
        st.error(f"Error during conversion: {e}")
        return None
    
# Main App
def main():
    menu = sidebar_navigation()
    if menu == "Home":
        home_page()
    elif menu == "Text Extraction":
        text_extraction_page()
    elif menu == "Translation":
        translation_page()
    elif menu == "Chatbot":
        chatbot_page()
    elif menu == "Currency Conversion":
        currency_conversion_page()
    display_footer()

if __name__ == "__main__":
    main()
