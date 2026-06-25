"""
Inspired by the Rag tutorial on the milvus website https://milvus.io/docs/build-rag-with-milvus.md

The original tutorial was done with OpenAi API. This script is modified to work with Ollama LLMs.
"""

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# Imports

import json
import numpy as np
import os
import ollama
import pymilvus

from src.scrap_repo import scrapper

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# Settings

# Repo variables
path_repo = "../Variational-Autoencoder-for-EEG-analysis/"
file_extension_filter = ['.md', '.py', '.txt', '.sh']
file_extension_filter = ['.md',]

paths_to_ignore = ["../DL_for_AD_detection/.git", "../DL_for_AD_detection/.venv/", "../DL_for_AD_detection/wandb"]
paths_to_ignore = [".git", ".venv/", ".wandb"]

# Milvus variable
milvus_uri = "./tutorial/db/milvus_demo.db"
collection_name = "milvus_rag_tutorial_collection"

# Ollama variable
EMBEDDING_MODEL = 'hf.co/CompendiumLabs/bge-base-en-v1.5-gguf'
LANGUAGE_MODEL = 'hf.co/bartowski/Llama-3.2-1B-Instruct-GGUF'

# RAG variables
question = "What is hvEEGNet?"
n_chunk_to_retrieve = 3

SYSTEM_PROMPT = "Human: You are an AI assistant. You are able to find answers to the questions from the contextual passage snippets provided."
# USER_PROMPT is defined in get_user_prompt

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

def get_user_prompt(context : str, question : str) -> str :
    user_prompt = f"Use the following pieces of information enclosed in <context> tags to provide an answer to the question enclosed in <question> tags.\n"
    user_prompt += f"<context>\n{context}\n</context>\n"
    user_prompt += f"<question>\n{question}\n</question>\n"
    # user_prompt += f"Provide your answer removing any tags from the text. You can access your knowledge if you feel it is necessary\n"

    return user_prompt

def split_markdown(text_to_split) :
    """
    Function to split markdown files into chunks.
    The function splits the text at each header (lines starting with #).
    """
    
    # Split text in lines
    text_split_in_lines = text_to_split.split('\n')

    # Variable to store the chunks
    tmp_chunks = []

    # Chunk currently constructed
    current_chunk = ""

    # Iterate over line
    for line in text_split_in_lines :
        if len(line) > 0 : # Check that the line is not empty
            if line[0] == '#' : # If new line start with # then create a new chunk
                # Save current chunk in the list
                tmp_chunks.append(current_chunk)

                # Create new chunk
                current_chunk = line
            else : # If new line NOT start with # then save the line in the current chunk
                current_chunk += line + "\n"
    
    # Clean chunks
    chunks = [chunk for chunk in tmp_chunks if len(chunk.strip()) > 0]

    return chunks

def embed_text(text : str, model : str) :
    """
    Embed the text using ollama model specified by the model argument
    """

    return ollama.embed(model = model, input = text)['embeddings'][0]

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# Scrapping and test embedding

# Scrape the repository and create chunks
repo_scrapper = scrapper(path_repo, file_extension_filter, paths_to_ignore, chunking_function = split_markdown)

# Check if the n. of chunk to retrieve is higher than the total number of chunk
if n_chunk_to_retrieve > len(repo_scrapper.chunks) : n_chunk_to_retrieve = len(repo_scrapper.chunks)

# Test embedding
random_chunk = str(np.random.choice(repo_scrapper.chunks))
embedding_random_chunk = embed_text(random_chunk, model = EMBEDDING_MODEL)
print("\n%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%")
print("Check embedding of random chunk")
print("-------------------------------")
print(f"Text :\n{random_chunk}")
print("-------------------------------")
print(f"Embedding :\n{embedding_random_chunk}")

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# Milvus setup

# Create the Milvus client
os.makedirs(os.path.dirname(milvus_uri), exist_ok=True)
milvus_client = pymilvus.MilvusClient(uri = milvus_uri)

# Note from the tutorial page about Milvus client
# Setting the uri as a local file, e.g../milvus.db, is the most convenient method, as it automatically utilizes Milvus Lite to store all data in this file.
# If you have large scale of data, you can set up a more performant Milvus server on docker or kubernetes. In this setup, please use the server uri, e.g.http://localhost:19530, as your uri.
# If you want to use Zilliz Cloud, the fully managed cloud service for Milvus, adjust the uri and token, which correspond to the Public Endpoint and Api key in Zilliz Cloud.

# Check if the collection (db) already exist (has_collection method).
# If already exist delete it (drop_collection method).
if milvus_client.has_collection(collection_name):
    milvus_client.drop_collection(collection_name)


# Create new collection
# More info here : https://milvus.io/api-reference/pymilvus/v2.6.x/MilvusClient/Collections/create_collection.md
milvus_client.create_collection(
    collection_name = collection_name,
    dimension = len(embedding_random_chunk),
    metric_type = "IP",  # The value defaults to COSINE. Possible values are L2, IP (Inner product distance), and COSINE.
    consistency_level="Bounded",  # Supported values are (`"Strong"`, `"Session"`, `"Bounded"`, `"Eventually"`). See https://milvus.io/docs/consistency.md#Consistency-Level for more details.
)

# Convert chunks in embedding
data = []
for i in range(len(repo_scrapper.chunks)) :
    current_chunk = repo_scrapper.chunks[i]
    embedding_current_chunk = embed_text(current_chunk, model = EMBEDDING_MODEL)
    data.append({"id" : i, "vector" : embedding_current_chunk, "text": current_chunk})

# Save embedding inside Milvus
# More info here : https://milvus.io/docs/insert-update-delete.md#Insert-Entities-into-a-Collection
# Personal notes :
# The collection must be a list of dictionary. If you not specified a Schema each dictionary must have the field id and vector
# Additionally, this Collection has the dynamic field enabled, so the Entities in the example code include a field called text that is not defined in the Schema.
milvus_client.insert(collection_name = collection_name, data = data)


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# RAG operation

embedding_question = embed_text(question, model = EMBEDDING_MODEL)

# Search inside Milvus the most relevant chunks
# More info here : https://milvus.io/api-reference/pymilvus/v2.6.x/MilvusClient/Vector/search.md
search_res = milvus_client.search(
    collection_name = collection_name,
    data = [embedding_question],  # Use the `embed_text` function to convert the question to an embedding vector
    limit = n_chunk_to_retrieve,  # Return top n results
    search_params = {"metric_type": "IP"},  # Inner product distance
    output_fields = ["text"],  # Return the text field. This must be one of the field you use to create the collection (in our case id, vector and text)
)

# Print results
retrieved_lines_with_distances = [(res["entity"]["text"], res["distance"]) for res in search_res[0]]
print("\n%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%")
print(f"Question : {question}\n")
print("Chunks with the highest similarity score :\n")
print(json.dumps(retrieved_lines_with_distances, indent = 4))

# Merge chunks with the highest similarity score
context = "\n".join([line_with_distance[0] for line_with_distance in retrieved_lines_with_distances])

# Get the user prompt
USER_PROMPT = get_user_prompt(context, question)

# Create response
stream = ollama.chat(
    model = LANGUAGE_MODEL,
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": USER_PROMPT},
    ],
    stream = True,
)

# print the response from the chatbot in real-time
print("\n%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%")
print(f"Question : {question}\n")
print('Chatbot response:')
for chunk in stream:
    print(chunk['message']['content'], end='', flush=True)
