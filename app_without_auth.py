import streamlit as st
import streamlit_authenticator as stauth
import pandas as pd
import yaml
import json
import io
from datetime import datetime
from yaml.loader import SafeLoader

with open('config.yaml') as file:
    config = yaml.load(file, Loader=SafeLoader)

# Configure page
st.set_page_config(
    page_title="Adjudication Platform",
    page_icon="⚖️",
    layout="wide"
)

# Initialize session state
if 'df' not in st.session_state:
    st.session_state.df = None
if 'current_index' not in st.session_state:
    st.session_state.current_index = 0
if 'adjudicated_data' not in st.session_state:
    st.session_state.adjudicated_data = []

def reset_session():
    """Reset all session state variables"""
    st.session_state.df = None
    st.session_state.current_index = 0
    st.session_state.adjudicated_data = []

def save_adjudication(current_record, adj_emotion, adj_sentiment, adj_hate, adj_cyber, adj_reasoning, adjudicator_notes=""):
    """Save adjudication data"""
    adjudication = current_record.to_dict()
    adjudicated_data = {
        'final_emotion_label': adj_emotion,
        'final_sentiment_label': adj_sentiment,
        'final_hate_speech_label': adj_hate,
        'final_cyberbully_label': adj_cyber,
        'final_reasoning': adj_reasoning,
        'adjudicator_notes': adjudicator_notes,
        'adjudication_timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'status': 'adjudicated'
    }
    adjudication.update(adjudicated_data)
    st.session_state.adjudicated_data.append(adjudication)

def create_download_data():
    """Create downloadable DataFrame"""
    if st.session_state.adjudicated_data:
        return pd.DataFrame(st.session_state.adjudicated_data)
    return pd.DataFrame()

# Main app
st.title("⚖️ Adjudication Platform")
st.markdown("Upload CSV files for content adjudication and review")

# Sidebar for navigation and stats
with st.sidebar:
    st.header("📊 Platform Stats")
    
    if st.session_state.df is not None:
        total_records = len(st.session_state.df)
        adjudicated_count = len(st.session_state.adjudicated_data)
        remaining = total_records - adjudicated_count
        
        st.metric("Total Records", total_records)
        st.metric("Adjudicated", adjudicated_count)
        st.metric("Remaining", remaining)
        
        if total_records > 0:
            progress = adjudicated_count / total_records
            st.progress(progress)
            st.write(f"Progress: {progress:.1%}")
    
    st.markdown("---")
    
    if st.button("🔄 Reset Session", type="secondary"):
        reset_session()
        st.rerun()

st.header("📁 Upload Data")

uploaded_file = st.file_uploader(
    "Choose a JSON file",
    type="json",
    help="Upload a JSON file containing Tweet, Emotion Label, Sentiment Label, Hate Speech Label, Cyberbully, and Reasoning columns"
)

if uploaded_file is not None:
    try:
        # Load JSON data from the uploaded file
        data_new = json.load(uploaded_file)
        df = pd.DataFrame(data_new)
        
        # Validate required columns
        required_columns = ['Tweet', 'Annotator A Emotion', 'Annotator A Sentiment', 'Annotator A Hate Speech', 'Annotator A Cyberbully', 'reasoning', 'Annotator B Emotion', 'Annotator B Sentiment', 'Annotator B Hate Speech', 'Annotator B Cyberbully']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            st.error(f"Missing required columns: {', '.join(missing_columns)}")
            st.info("Required columns: Tweet, Annotator A Emotion, Annotator A Sentiment, Annotator A Hate Speech, Annotator A Cyberbully, reasoning, Annotator B Emotion, Annotator B Sentiment, Annotator B Hate Speech, Annotator B Cyberbully")
        else:
            st.session_state.df = df
            st.success(f"✅ Successfully loaded {len(df)} records")
            
            # Show data preview
            with st.expander("📋 Data Preview", expanded=False):
                st.dataframe(df.head(), use_container_width=True)
                
    except Exception as e:
        st.error(f"Error reading file: {str(e)}")

# Adjudication section
if st.session_state.df is not None:
    st.header("⚖️ Adjudication Interface")
    
    df = st.session_state.df
    current_idx = st.session_state.current_index
    
    if current_idx < len(df):
        # Navigation
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col1:
            if st.button("⬅️ Previous", disabled=current_idx == 0):
                st.session_state.current_index = max(0, current_idx - 1)
                st.rerun()
        
        with col2:
            st.write(f"Record {current_idx + 1} of {len(df)}")
        
        with col3:
            if st.button("➡️ Next", disabled=current_idx >= len(df) - 1):
                st.session_state.current_index = min(len(df) - 1, current_idx + 1)
                st.rerun()
        
        # Current record
        current_record = df.iloc[current_idx]
        
        # Display tweet
        st.subheader("📱 Tweet Content")
        st.text_area("Tweet Text", value=current_record['Tweet'], height=100, disabled=True, key="tweet_display")
        
        # Annotator labels comparison
        st.subheader("👥 Annotator Labels Comparison")
        
        # Create comparison table
        comparison_data = {
            'Label Type': ['Emotion', 'Sentiment', 'Hate Speech', 'Cyberbully'],
            'Annotator A': [
                current_record['Annotator A Emotion'],
                current_record['Annotator A Sentiment'], 
                current_record['Annotator A Hate Speech'],
                current_record['Annotator A Cyberbully']
            ],
            'Annotator B': [
                current_record['Annotator B Emotion'],
                current_record['Annotator B Sentiment'],
                current_record['Annotator B Hate Speech'], 
                current_record['Annotator B Cyberbully']
            ]
        }
        
        comparison_df = pd.DataFrame(comparison_data)
        st.dataframe(comparison_df, use_container_width=True, hide_index=True)
        
        # Show agreement/disagreement
        agreements = []
        if current_record['Annotator A Emotion'] == current_record['Annotator B Emotion']:
            agreements.append("✅ Emotion")
        else:
            agreements.append("❌ Emotion")
            
        if current_record['Annotator A Sentiment'] == current_record['Annotator B Sentiment']:
            agreements.append("✅ Sentiment")
        else:
            agreements.append("❌ Sentiment")
            
        if str(current_record['Annotator A Hate Speech']) == str(current_record['Annotator B Hate Speech']):
            agreements.append("✅ Hate Speech")
        else:
            agreements.append("❌ Hate Speech")
            
        if str(current_record['Annotator A Cyberbully']) == str(current_record['Annotator B Cyberbully']):
            agreements.append("✅ Cyberbully")
        else:
            agreements.append("❌ Cyberbully")
        
        st.write("**Agreement Status:** " + " | ".join(agreements))

        st.subheader("📝 Reasoning")
        st.text_area("", value=current_record['reasoning'], height=120, disabled=True, key="ann_a_reasoning_display")
        
        # # Annotator reasoning sections
        # col1, col2 = st.columns(2)
        
        # with col1:
        #     st.subheader("📝 Annotator A Reasoning")
        #     st.text_area("", value=current_record['Annotator A Reasoning'], height=120, disabled=True, key="ann_a_reasoning_display")
        
        # with col2:
        #     st.subheader("📝 Annotator B Reasoning") 
        #     st.text_area("", value=current_record['Annotator B Reasoning'], height=120, disabled=True, key="ann_b_reasoning_display")
        
        # Final adjudication section
        st.subheader("⚖️ Final Adjudication")
        st.markdown("**Choose the final labels by selecting from Annotator A, Annotator B, or provide your own decision:**")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Emotion Label Selection
            emotion_options = ['Happniess', 'Neutral', 'Surprise', 'Disgust', 'Fear', 'Sadness', 'Anger']
            st.write("**Final Emotion Label:**")
            
            # Radio buttons for choosing annotator
            emotion_choice = st.radio(
                "Choose source:",
                ["Annotator A", "Annotator B", "Custom"],
                key="emotion_choice",
                horizontal=True
            )
            
            if emotion_choice == "Annotator A":
                final_emotion = current_record['Annotator A Emotion']
                st.info(f"Selected: {final_emotion}")
            elif emotion_choice == "Annotator B":
                final_emotion = current_record['Annotator B Emotion']
                st.info(f"Selected: {final_emotion}")
            else:
                final_emotion = st.selectbox(
                    "Custom Emotion Label:",
                    options=emotion_options,
                    key="custom_emotion"
                )
            
            # Sentiment Label Selection
            sentiment_options = ['Neutral', 'Negative', 'Positive']
            st.write("**Final Sentiment Label:**")
            
            sentiment_choice = st.radio(
                "Choose source:",
                ["Annotator A", "Annotator B", "Custom"],
                key="sentiment_choice", 
                horizontal=True
            )
            
            if sentiment_choice == "Annotator A":
                final_sentiment = current_record['Annotator A Sentiment']
                st.info(f"Selected: {final_sentiment}")
            elif sentiment_choice == "Annotator B":
                final_sentiment = current_record['Annotator B Sentiment']
                st.info(f"Selected: {final_sentiment}")
            else:
                final_sentiment = st.selectbox(
                    "Custom Sentiment Label:",
                    options=sentiment_options,
                    key="custom_sentiment"
                )
        
        with col2:
            # Hate Speech Label Selection
            hate_speech_options = ['True', 'False']
            st.write("**Final Hate Speech Label:**")
            
            hate_choice = st.radio(
                "Choose source:",
                ["Annotator A", "Annotator B", "Custom"],
                key="hate_choice",
                horizontal=True
            )
            
            if hate_choice == "Annotator A":
                final_hate = current_record['Annotator A Hate Speech']
                st.info(f"Selected: {final_hate}")
            elif hate_choice == "Annotator B":
                final_hate = current_record['Annotator B Hate Speech']
                st.info(f"Selected: {final_hate}")
            else:
                final_hate = st.selectbox(
                    "Custom Hate Speech Label:",
                    options=hate_speech_options,
                    key="custom_hate"
                )
            
            # Cyberbully Label Selection
            cyberbully_options = ['True', 'False']
            st.write("**Final Cyberbully Label:**")
            
            cyber_choice = st.radio(
                "Choose source:",
                ["Annotator A", "Annotator B", "Custom"],
                key="cyber_choice",
                horizontal=True
            )
            
            if cyber_choice == "Annotator A":
                final_cyber = current_record['Annotator A Cyberbully']
                st.info(f"Selected: {final_cyber}")
            elif cyber_choice == "Annotator B":
                final_cyber = current_record['Annotator B Cyberbully']
                st.info(f"Selected: {final_cyber}")
            else:
                final_cyber = st.selectbox(
                    "Custom Cyberbully Label:",
                    options=cyberbully_options,
                    key="custom_cyber"
                )
        
        # Final Reasoning Selection
        st.write("**Final Reasoning:**")
        # reasoning_choice = st.radio(
        #     "Choose reasoning source:",
        #     ["Annotator A", "Annotator B", "Custom"],
        #     key="reasoning_choice",
        #     horizontal=True
        # )
        final_reasoning = current_record['reasoning']
        st.text_area("Selected Reasoning:", value=final_reasoning, height=100, disabled=True)        
        # if reasoning_choice == "Annotator A":
        #     final_reasoning = current_record['Annotator A Reasoning']
        #     st.text_area("Selected Reasoning:", value=final_reasoning, height=100, disabled=True)
        # elif reasoning_choice == "Annotator B":
        #     final_reasoning = current_record['Annotator B Reasoning']
        #     st.text_area("Selected Reasoning:", value=final_reasoning, height=100, disabled=True)
        # else:
        #     final_reasoning = st.text_area(
        #         "Custom Reasoning:",
        #         placeholder="Provide your own reasoning for the final decision...",
        #         height=120,
        #         key="custom_reasoning"
        #     )
        
        adjudicator_notes = st.text_area(
            "Adjudicator Notes (Optional)",
            placeholder="Add any additional notes or comments about this adjudication...",
            height=80
        )
        
        # Action buttons
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("💾 Save Adjudication"):
                save_adjudication(
                    current_record=current_record,
                    adj_emotion=final_emotion,
                    adj_sentiment=final_sentiment,
                    adj_hate=final_hate,
                    adj_cyber=final_cyber,
                    adj_reasoning=final_reasoning,
                    adjudicator_notes=adjudicator_notes
                )
                st.success("✅ Adjudication saved!")
                
                # Automatically move to next record
                if st.session_state.current_index < len(st.session_state.df) - 1:
                    st.session_state.current_index += 1
                    st.rerun()

        with col2:
            if st.button("⬆️ Export All Adjudicated Data"):
                export_df = create_download_data()
                if not export_df.empty:
                    csv = export_df.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label="📥 Download CSV",
                        data=csv,
                        file_name=f"adjudicated_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv"
                    )
                else:
                    st.warning("⚠️ No adjudicated data to export yet.")
                    
        with col3:
            if st.button("🚫 Skip Record"):
                if st.session_state.current_index < len(st.session_state.df) - 1:
                    st.session_state.current_index += 1
                    st.rerun()
    
    else:
        st.success("🎉 All records have been processed!")


# Download section
if st.session_state.adjudicated_data:
    st.header("📥 Download Adjudicated Data")
    
    download_df = create_download_data()
    
    # Show preview of adjudicated data
    with st.expander("📋 Adjudicated Data Preview", expanded=False):
        st.dataframe(download_df, use_container_width=True)
    
    # Download format selection
    download_format = st.radio(
        "Select download format:",
        ["JSON", "CSV"],
        horizontal=True,
        key="download_format"
    )
    
    if download_format == "JSON":
        # JSON download
        import json
        json_data = json.dumps(st.session_state.adjudicated_data, indent=2, ensure_ascii=False)
        
        st.download_button(
            label="📥 Download Adjudicated Data (JSON)",
            data=json_data,
            file_name=f"adjudicated_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json",
            type="primary"
        )
    else:
        # CSV download
        csv_buffer = io.StringIO()
        download_df.to_csv(csv_buffer, index=False)
        csv_data = csv_buffer.getvalue()
        
        st.download_button(
            label="📥 Download Adjudicated Data (CSV)",
            data=csv_data,
            file_name=f"adjudicated_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            type="primary"
        )
    
    st.info(f"💡 {len(st.session_state.adjudicated_data)} records ready for download")

# Instructions
with st.expander("📖 How to Use", expanded=False):
    st.markdown("""
    ### Instructions:
    
    1. **Upload CSV File**: Upload a CSV file with the required columns:
    - Tweet
    - Annotator A Emotion, Annotator A Sentiment, Annotator A Hate Speech, Annotator A Cyberbully, reasoning
    - Annotator B Emotion, Annotator B Sentiment, Annotator B Hate Speech, Annotator B Cyberbully, reasoning
    
    2. **Review Annotations**: 
    - Compare Annotator A and Annotator B labels side-by-side
    - See agreement/disagreement status for each label type
    - Review both annotators' reasoning
    
    3. **Make Final Decision**:
    - Choose between Annotator A, Annotator B, or provide custom labels
    - Select reasoning from either annotator or write your own
    - Add adjudicator notes for additional context
    
    4. **Navigate & Track**:
    - Use Previous/Next buttons to navigate records
    - Monitor progress in the sidebar
    - Skip records if needed
    
    5. **Download Results**:
    - Export includes all annotator data plus final decisions
    - Timestamped for audit trails
    - Comprehensive adjudication record
    
    ### Features:
    - ✅ Dual annotator comparison view
    - ✅ Agreement status indicators  
    - ✅ Flexible selection (A, B, or Custom)
    - ✅ Progress tracking
    - ✅ Complete audit trail export
    """)