<!-- Add a disclaimer -->
I first found this code on X (https://x.com/jason_j_lee/status/1828188888888888888) which Akshay shared[https://x.com/akshay_pachaar], give him a a follow.

Original code is here: https://github.com/patchy631/ai-engineering-hub/blob/main/rag-with-dockling/README.md

## Steps i did to run this code on my Mac Local machine

1. First install all the dependencies
`pip install -q --progress-bar off --no-warn-conflicts llama-index-core llama-index-readers-docling llama-index-node-parser-docling llama-index-embeddings-huggingface llama-index-llms-huggingface-api llama-index-readers-file python-dotenv llama-index-llms-ollama`

2. Then download Ollama from here: https://ollama.ai/ and run it on my local machine 
`ollama run llama3.2`

3. Then run the streamlit app
`streamlit run main.py`

4. Then you can chat with the excel file