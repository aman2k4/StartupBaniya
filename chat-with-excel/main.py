import os

import gc
import tempfile
import uuid
import pandas as pd

from llama_index.core import Settings
from llama_index.llms.ollama import Ollama
from llama_index.core import PromptTemplate
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader
from llama_index.readers.docling import DoclingReader
from llama_index.core.node_parser import MarkdownNodeParser

import streamlit as st

if "id" not in st.session_state:
    st.session_state.id = uuid.uuid4()
    st.session_state.file_cache = {}

session_id = st.session_state.id
client = None

@st.cache_resource
def load_llm():
    llm = Ollama(model="llama3.2", request_timeout=120.0)
    return llm

def reset_chat():
    st.session_state.messages = []
    st.session_state.context = None
    gc.collect()


def display_excel(file):
    st.markdown("### File Preview")
    # Read the file based on its type
    if file.name.endswith(('.xlsx', '.xls')):
        df = pd.read_excel(file)
    else:  # CSV file
        df = pd.read_csv(file)
    # Display the dataframe
    st.dataframe(df)

def validate_csv(file):
    try:
        # Try to read the first few lines to detect the delimiter
        sample = file.read(1024).decode('utf-8')
        file.seek(0)  # Reset file pointer
        
        if not sample.strip():
            return False, "File is empty"
            
        # Detect delimiter
        if ',' in sample:
            delimiter = ','
        elif ';' in sample:
            delimiter = ';'
        elif '\t' in sample:
            delimiter = '\t'
        else:
            return False, "Could not detect valid CSV delimiter (comma, semicolon, or tab)"
            
        # Try reading with detected delimiter
        df = pd.read_csv(file, delimiter=delimiter)
        
        if df.empty:
            return False, "File contains no data"
        if len(df.columns) < 1:
            return False, "No columns found in the file"
            
        return True, None
    except UnicodeDecodeError:
        return False, "File encoding issue. Please save the file with UTF-8 encoding"
    except pd.errors.EmptyDataError:
        return False, "The file is empty"
    except Exception as e:
        return False, f"Error reading CSV: {str(e)}"

def process_file(file_path):
    """Process file based on its extension"""
    if file_path.endswith('.csv'):
        try:
            # Try different delimiters
            delimiters = [',', ';', '\t']
            df = None
            
            for delimiter in delimiters:
                try:
                    df = pd.read_csv(file_path, delimiter=delimiter)
                    if not df.empty and len(df.columns) > 1:
                        break
                except:
                    continue
                    
            if df is None or df.empty:
                raise Exception("Could not read CSV file with any standard delimiter")
                
            # Convert DataFrame to markdown for DoclingReader
            markdown_content = df.to_markdown()
            with open(file_path + '.md', 'w', encoding='utf-8') as f:
                f.write(markdown_content)
            return file_path + '.md'
        except Exception as e:
            raise Exception(f"Error processing CSV file: {str(e)}")
    return file_path

with st.sidebar:
    st.header(f"Add your documents!")
    
    uploaded_file = st.file_uploader("Choose your `.xlsx` or `.csv` file", type=["xlsx", "xls", "csv"])

    if uploaded_file:
        try:
            # Validate CSV files before processing
            if uploaded_file.name.endswith('.csv'):
                is_valid, error_message = validate_csv(uploaded_file)
                if not is_valid:
                    st.error(f"Invalid CSV file: {error_message}")
                    st.stop()

            with tempfile.TemporaryDirectory() as temp_dir:
                file_path = os.path.join(temp_dir, uploaded_file.name)
                
                with open(file_path, "wb") as f:
                    f.write(uploaded_file.getvalue())
                
                file_key = f"{session_id}-{uploaded_file.name}"
                st.write("Indexing your document...")

                if file_key not in st.session_state.get('file_cache', {}):
                    if os.path.exists(temp_dir):
                        try:
                            # Process the file if needed
                            processed_file_path = process_file(file_path)
                            
                            reader = DoclingReader()
                            loader = SimpleDirectoryReader(
                                input_dir=temp_dir,
                                file_extractor={
                                    ".xlsx": reader,
                                    ".xls": reader,
                                    ".csv": reader,
                                    ".md": reader  # Add support for processed markdown files
                                },
                            )
                            docs = loader.load_data()
                            
                            if not docs:
                                raise Exception("No documents were loaded. The file might be empty or in an unsupported format.")
                            
                        except Exception as e:
                            st.error(f"Error processing document: {str(e)}")
                            st.error("Please make sure your file is properly formatted and not empty.")
                            st.stop()
                    else:    
                        st.error('Could not find the file you uploaded, please check again...')
                        st.stop()
                    
                    # setup llm & embedding model
                    llm=load_llm()
                    embed_model = HuggingFaceEmbedding( model_name="BAAI/bge-large-en-v1.5", trust_remote_code=True)
                    # Creating an index over loaded data
                    Settings.embed_model = embed_model
                    node_parser = MarkdownNodeParser()
                    index = VectorStoreIndex.from_documents(documents=docs, transformations=[node_parser], show_progress=True)

                    # Create the query engine, where we use a cohere reranker on the fetched nodes
                    Settings.llm = llm
                    query_engine = index.as_query_engine(streaming=True)

                    # ====== Customise prompt template ======
                    qa_prompt_tmpl_str = (
                    "Context information is below.\n"
                    "---------------------\n"
                    "{context_str}\n"
                    "---------------------\n"
                    "Given the context information above I want you to think step by step to answer the query in a highly precise and crisp manner focused on the final answer, incase case you don't know the answer say 'I don't know!'.\n"
                    "Query: {query_str}\n"
                    "Answer: "
                    )
                    qa_prompt_tmpl = PromptTemplate(qa_prompt_tmpl_str)

                    query_engine.update_prompts(
                        {"response_synthesizer:text_qa_template": qa_prompt_tmpl}
                    )
                    
                    st.session_state.file_cache[file_key] = query_engine
                else:
                    query_engine = st.session_state.file_cache[file_key]

                # Inform the user that the file is processed and Display the PDF uploaded
                st.success("Ready to Chat!")
                display_excel(uploaded_file)
        except Exception as e:
            st.error(f"An error occurred: {str(e)}")
            if "Input document" in str(e):
                st.error("The CSV file format is not supported. Please make sure it's a valid CSV file.")
            st.error("If the problem persists, try the following:")
            st.error("1. Check if the CSV file is not empty")
            st.error("2. Ensure the CSV file is properly formatted")
            st.error("3. Try saving the CSV file with UTF-8 encoding")
            st.stop()     

col1, col2 = st.columns([6, 1])

with col1:
    st.header(f"RAG over Excel using Dockling 🐥 &  Llama-3.2")

with col2:
    st.button("Clear ↺", on_click=reset_chat)

# Initialize chat history
if "messages" not in st.session_state:
    reset_chat()


# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])


# Accept user input
if prompt := st.chat_input("What's up?"):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    # Display user message in chat message container
    with st.chat_message("user"):
        st.markdown(prompt)

    # Display assistant response in chat message container
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        
        # Simulate stream of response with milliseconds delay
        streaming_response = query_engine.query(prompt)
        
        for chunk in streaming_response.response_gen:
            full_response += chunk
            message_placeholder.markdown(full_response + "▌")

        # full_response = query_engine.query(prompt)

        message_placeholder.markdown(full_response)
        # st.session_state.context = ctx

    # Add assistant response to chat history
    st.session_state.messages.append({"role": "assistant", "content": full_response})