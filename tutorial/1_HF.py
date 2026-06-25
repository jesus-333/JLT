"""
Code copied from huggingface (https://huggingface.co/blog/ngxson/make-your-own-rag) (28/08/2025)

There are some extra notes and change in formatting but the code is mostly the same.
"""

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

import ollama

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

EMBEDDING_MODEL = 'hf.co/CompendiumLabs/bge-base-en-v1.5-gguf'
LANGUAGE_MODEL = 'hf.co/bartowski/Llama-3.2-1B-Instruct-GGUF'

# Each element in the VECTOR_DB will be a tuple (chunk, embedding)
# The embedding is a list of floats, for example: [0.1, 0.04, -0.34, 0.21, ...]
VECTOR_DB = []

def add_chunk_to_database(chunk) :
    embedding = ollama.embed(model = EMBEDDING_MODEL, input = chunk)['embeddings'][0]
    VECTOR_DB.append((chunk, embedding))

def cosine_similarity(a, b) :
    dot_product = sum([x * y for x, y in zip(a, b)])
    norm_a = sum([x ** 2 for x in a]) ** 0.5
    norm_b = sum([x ** 2 for x in b]) ** 0.5
    return dot_product / (norm_a * norm_b)

def retrieve(query, top_n = 3) :
    query_embedding = ollama.embed(model = EMBEDDING_MODEL, input = query)['embeddings'][0]
    # temporary list to store (chunk, similarity) pairs
    similarities = []
    for chunk, embedding in VECTOR_DB:
        similarity = cosine_similarity(query_embedding, embedding)
        similarities.append((chunk, similarity))

    # sort by similarity in descending order, because higher similarity means more relevant chunks
    similarities.sort(key = lambda x : x[1], reverse = True)

    # finally, return the top N most relevant chunks
    return similarities[:top_n]

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# Generate response

input_query = input('Ask me a question: ')
retrieved_knowledge = retrieve(input_query)

print('Retrieved knowledge:')
for chunk, similarity in retrieved_knowledge:
    print(f' - (similarity: {similarity:.2f}) {chunk}')

instruction_prompt = f'''
    You are a helpful chatbot.
    Use only the following pieces of context to answer the question. Don't make up any new information:
    {'\n'.join([f' - {chunk}' for chunk, similarity in retrieved_knowledge])}
    '''


stream = ollama.chat(
    model = LANGUAGE_MODEL,
    messages = [
        {"role": "system", "content": instruction_prompt},
        {"role": "user", "content": input_query},
    ],
    stream = True,
)

# Note for the chat method (from https://ollama.readthedocs.io/en/api/#generate-a-chat-completion)
"""
Parameters

    model: (required) the model name
    messages: the messages of the chat, this can be used to keep a chat memory
    tools: tools for the model to use if supported. Requires stream to be set to false

The message object has the following fields:
    role: the role of the message, either system, user, assistant, or tool
    content: the content of the message
    images (optional): a list of images to include in the message (for multimodal models such as llava)
    tool_calls (optional): a list of tools the model wants to use

Advanced parameters (optional):
    format: the format to return a response in. Currently the only accepted value is json
    options: additional model parameters listed in the documentation for the Modelfile such as temperature
    stream: if false the response will be returned as a single response object, rather than a stream of objects
    keep_alive: controls how long the model will stay loaded into memory following the request (default: 5m)
"""

# print the response from the chatbot in real-time
print('Chatbot response:')
for chunk in stream:
    print(chunk['message']['content'], end='', flush=True)
