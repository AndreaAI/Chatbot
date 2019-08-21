# Chatbot

The idea of this project is to have a functional chatbot able to conduct a conversation with the user via text messages and recommend hotels based on the user inputs.
It provides more interactivity and guidance than the basil hotel finding site.

The first core part of the chatbot was implemented in [Dialogflow](https://dialogflow.com/), a Google-owned developer of human–computer interaction technologies based on natural language conversations.

All the intermediary back-end code was implemented in Python to:
1. Extend and make more complex the chatbot structure from Diagflow.
2. Query Elasticsearch and access all the information available to satisfy the user inquiry.
3. Create a front-end API with Flask for the interaction between the user and the chatbot.

Information on how to build a chatbot with Flask and Dialogflow: https://pusher.com/tutorials/chatbot-flask-dialogflow.
