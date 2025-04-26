from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import shutil
import data_processor
import chatbot
from dotenv import load_dotenv, set_key
import re

app = Flask(__name__)
CORS(app)

DATA_DIR = "../Data"
PROCESSED_DATA_DIR = "../processed_data"

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(PROCESSED_DATA_DIR, exist_ok=True)

# Cleanup data and processed_data directories on server startup
print(f"Clearing processed data directory: {PROCESSED_DATA_DIR}")
if os.path.exists(PROCESSED_DATA_DIR):
    try:
        for item in os.listdir(PROCESSED_DATA_DIR):
            item_path = os.path.join(PROCESSED_DATA_DIR, item)
            if os.path.isfile(item_path):
                os.remove(item_path)
            elif os.path.isdir(item_path):
                shutil.rmtree(item_path)
        print("Processed data directory cleared.")
    except Exception as e:
        print(f"Error clearing processed data directory: {e}")

print(f"Clearing raw data directory: {DATA_DIR}")
if os.path.exists(DATA_DIR):
    try:
        for item in os.listdir(DATA_DIR):
            item_path = os.path.join(DATA_DIR, item)
            if os.path.isfile(item_path):
                os.remove(item_path)
            elif os.path.isdir(item_path):
                shutil.rmtree(item_path)
        print("Raw data directory cleared.")
    except Exception as e:
        print(f"Error clearing raw data directory: {e}")

load_dotenv(dotenv_path='../.env')

# Dictionary to hold active chat sessions (in-memory)
active_chats = {}

@app.route('/api/test')
def test():
    return {'message': 'Hello from the backend!'}

@app.route('/api/upload', methods=['POST'])
def upload_files():
    if 'files' not in request.files:
        return jsonify({'error': 'No file part in the request'}), 400

    files = request.files.getlist('files')
    if not files:
        return jsonify({'error': 'No selected file'}), 400

    uploaded_count = 0
    skipped_files = []

    for file in files:
        if file.filename == '':
            continue

        if not file.filename.lower().endswith('.zip'):
            print(f"Skipping non-zip file: {file.filename}")
            skipped_files.append(file.filename)
            continue

        filename = file.filename
        filepath = os.path.join(DATA_DIR, filename)
        try:
            file.save(filepath)
            uploaded_count += 1
            print(f"Uploaded file: {filename}")
        except Exception as e:
            print(f"Error saving file {filename}: {e}")

    response_message = f'Successfully uploaded {uploaded_count} zip files.'
    if skipped_files:
        response_message += f' Skipped {len(skipped_files)} non-zip files: {", ".join(skipped_files)}.'

    return jsonify({'message': response_message, 'skipped_files': skipped_files}), 200

@app.route('/api/delete_file', methods=['POST'])
def delete_file():
    data = request.get_json()
    if not data or 'filename' not in data:
        return jsonify({'error': 'Invalid request data. Requires filename.'}), 400

    filename = data.get('filename')
    filepath = os.path.join(DATA_DIR, filename)

    if not os.path.exists(filepath):
        return jsonify({'error': f'File not found: {filename}'}), 404

    try:
        os.remove(filepath)
        print(f"Deleted file: {filename}")
        return jsonify({'message': f'File deleted successfully: {filename}'}), 200
    except Exception as e:
        print(f"Error deleting file {filename}: {e}")
        return jsonify({'error': f'Error deleting file: {e}'}), 500

@app.route('/api/clear_uploaded_files', methods=['POST'])
def clear_uploaded_files():
    print("Clearing uploaded files...")
    try:
        print(f"Clearing raw data directory: {DATA_DIR}")
        if os.path.exists(DATA_DIR):
            try:
                for item in os.listdir(DATA_DIR):
                    item_path = os.path.join(DATA_DIR, item)
                    if os.path.isfile(item_path):
                        os.remove(item_path)
                    elif os.path.isdir(item_path):
                        shutil.rmtree(item_path)
                print("Raw data directory cleared.")
            except Exception as e:
                print(f"Error clearing raw data directory: {e}")
                return jsonify({'error': f'Error clearing uploaded files: {e}'}), 500

        print(f"Clearing processed data directory: {PROCESSED_DATA_DIR}")
        if os.path.exists(PROCESSED_DATA_DIR):
            try:
                for item in os.listdir(PROCESSED_DATA_DIR):
                    item_path = os.path.join(PROCESSED_DATA_DIR, item)
                    if os.path.isfile(item_path):
                        os.remove(item_path)
                    elif os.path.isdir(item_path):
                        shutil.rmtree(item_path)
                print("Processed data directory cleared.")
            except Exception as e:
                print(f"Error clearing processed data directory: {e}")
                return jsonify({'error': f'Error clearing processed data directory: {e}'}), 500

        return jsonify({'message': 'Uploaded and processed files cleared successfully.'}), 200

    except Exception as e:
        print(f"Error during clearing uploaded files: {e}")
        return jsonify({'error': f'Error during clearing uploaded files: {e}'}), 500


@app.route('/api/process_data', methods=['POST'])
def process_uploaded_data():
    print("Starting data processing...")
    try:
        print(f"Clearing processed data directory: {PROCESSED_DATA_DIR}")
        if os.path.exists(PROCESSED_DATA_DIR):
            try:
                for item in os.listdir(PROCESSED_DATA_DIR):
                    item_path = os.path.join(PROCESSED_DATA_DIR, item)
                    if os.path.isfile(item_path):
                        os.remove(item_path)
                    elif os.path.isdir(item_path):
                        shutil.rmtree(item_path)
                print("Processed data directory cleared.")
            except Exception as e:
                print(f"Error clearing processed data directory: {e}")

        processed_years, unprocessed_files = data_processor.process_data(DATA_DIR, PROCESSED_DATA_DIR)
        available_years = data_processor.get_available_years(PROCESSED_DATA_DIR)

        print(f"Data processing finished. Available years: {sorted(list(available_years))}")
        print(f"Unprocessed files after processing: {unprocessed_files}")

        return jsonify({
            'message': 'Data processing complete.',
            'available_years': sorted(list(available_years)),
            'unprocessed_files': unprocessed_files
        }), 200

    except Exception as e:
        print(f"Error during data processing: {e}")
        return jsonify({'error': f'Error during data processing: {e}'}), 500

@app.route('/api/get_available_years', methods=['GET'])
def get_available_years():
    print("Getting available years...")
    try:
        available_years = data_processor.get_available_years(PROCESSED_DATA_DIR)
        print(f"Available years found: {sorted(list(available_years))}")
        return jsonify(sorted(list(available_years))), 200
    except Exception as e:
        print(f"Error getting available years: {e}")
        return jsonify({'error': f'Error getting available years: {e}'}), 500

@app.route('/api/get_participants/<int:year>', methods=['GET'])
def get_participants(year):
    print(f"Getting participants for year: {year}")
    try:
        year_data = data_processor.load_year_data(PROCESSED_DATA_DIR, year)

        if not year_data:
            return jsonify({'error': f'No data found for year {year}'}), 404

        sender_counts_by_source = {}
        for entry in year_data:
            sender = entry.get('sender')
            source_info = entry.get('source', 'Unknown Source')
            source_type = 'other'
            if 'whatsapp' in source_info.lower():
                source_type = 'whatsapp'
            elif 'discord' in source_info.lower():
                source_type = 'discord'
            elif 'instagram' in source_info.lower():
                source_type = 'instagram'
            elif 'facebook' in source_info.lower():
                source_type = 'facebook'

            if sender and sender not in ['System', 'Unknown']:
                if source_type not in sender_counts_by_source:
                    sender_counts_by_source[source_type] = {}
                sender_counts_by_source[source_type][sender] = sender_counts_by_source[source_type].get(sender, 0) + 1

        participants_by_source = {}
        for source_type, sender_counts in sender_counts_by_source.items():
            sorted_senders = sorted(sender_counts.items(), key=lambda item: (-item[1], item[0]))
            participants_by_source[source_type] = [name for name, count in sorted_senders]

        print(f"Found participants for year {year}: {participants_by_source}")

        return jsonify({
            'year': year,
            'participants_by_source': participants_by_source
        }), 200

    except Exception as e:
        print(f"Error getting participants for year {year}: {e}")
        return jsonify({'error': f'Error getting participants: {e}'}), 500

@app.route('/api/set_user_names', methods=['POST'])
def set_user_names():
    data = request.get_json()
    if not data or 'year' not in data or 'selected_user_names' not in data:
        return jsonify({'error': 'Invalid request data. Requires year and selected_user_names.'}), 400

    year = data.get('year')
    selected_user_names = data.get('selected_user_names')

    if not isinstance(selected_user_names, dict):
         return jsonify({'error': 'selected_user_names must be a dictionary.'}), 400

    active_chats[str(year)] = {
        'selected_user_names': selected_user_names,
        'chat_session': None
    }

    print(f"Set user names for year {year}: {selected_user_names}")

    return jsonify({'message': f'User names set for year {year}.'}), 200

@app.route('/api/start_chat', methods=['POST'])
def start_chat_session():
    data = request.get_json()
    if not data or 'year' not in data:
        return jsonify({'error': 'Invalid request data. Requires year.'}), 400

    year = str(data.get('year'))

    if year not in active_chats or not active_chats[year].get('selected_user_names'):
        return jsonify({'error': f'User names not set for year {year}. Please set user names first.'}), 400

    selected_user_names = active_chats[year]['selected_user_names']

    print(f"Starting chat for year {year} with user names: {selected_user_names}")

    try:
        year_data = data_processor.load_year_data(PROCESSED_DATA_DIR, int(year))

        if not year_data:
            return jsonify({'error': f'No data loaded for year {year}. Cannot start chat.'}), 404

        context_prompt_text = chatbot.format_truncated_data_for_prompt(
            year_data,
            int(year),
            selected_user_names,
            chatbot.MAX_CONTEXT_CHARS,
            chatbot.MAX_ENTRIES
        )

        if not context_prompt_text:
             return jsonify({'error': f'Could not generate context for year {year} with selected users. No relevant messages found.'}), 404

        user_display_names = ", ".join([f"{name} ({source.capitalize()})" for source, name in selected_user_names.items()])
        if not user_display_names:
            user_display_names = 'Unknown Name'

        context_source_description = f"the following records from my ({user_display_names}) conversations (which may be truncated). Some messages from Discord DMs might have an unknown sender within the conversation, labelled as 'Message:' instead of 'MyMessage:'."

        style_focus_instruction = f"**Crucially, analyze and replicate the specific writing style of '{user_display_names}' found in {context_source_description}.**"

        system_prompt_text = f"""
You are a simulation of me, the user ({user_display_names}) from the year {year}.
Your personality, way of speaking, interests, and knowledge must be based *strictly* on {context_source_description}.
**IMPORTANT:** The context contains messages from my conversations. Pay close attention to the `ChatPartner:` field associated with each message block to understand who I was talking to. For messages labelled `MyMessage:`, that was me speaking. For messages labelled `Message:`, the sender within that specific Discord DM is unknown, but the conversation involved me and the listed `ChatPartner`. Use this information to answer questions about specific people or conversations accurately.
Do not use any external knowledge or information beyond the end of {year}.

{style_focus_instruction} Pay close attention to the style in the messages labelled `MyMessage:`:
*   **Sentence structure and length:** Are sentences short and choppy, long and complex, or varied?
*   **Vocabulary:** Is the language formal, informal, technical? Is there slang? Are certain words or phrases used repeatedly? (e.g., abbreviations like 'Ykw', 'rn', 'ofc')
*   **Punctuation and capitalization:** Is punctuation used correctly, sparsely, or excessively? Is capitalization standard or unconventional (e.g., all lowercase)?
*   **Tone:** Is the writing style direct, sarcastic, enthusiastic, hesitant, dry, rude, friendly, etc.? Match this tone precisely.
*   **Emojis/Emoticons:** If present in the records, use them similarly.

Engage in conversation as if you are truly me from that period.
Answer questions based *only* on the provided text context (my messages and the associated ChatPartner). If the context doesn't provide information about a topic or person, state that you don't recall or it's not in your memory from that time based on the provided records.
Do not break character. Do not act as an AI assistant. **Prioritize matching the exact style and tone found in the context above all else.** Embody the persona completely.

Now, the present-day user will start talking to you. Respond as your {year} self. The generation temperature (randomness) is set to {chatbot.API_TEMPERATURE} (based on user setting {chatbot.USER_TEMP_SETTING}).

{context_prompt_text}
"""

        chat_session = chatbot.model.start_chat(history=[
            {'role': 'user', 'parts': [system_prompt_text]},
            {'role': 'model', 'parts': [f"Alright, it's {year}... what's up? Ask me anything based on the context provided."]}
        ])

        active_chats[year]['chat_session'] = chat_session

        print(f"Chat session started for year {year}.")

        return jsonify({
            'message': f'Chat session started for year {year}.',
            'initial_response': f"Alright, it's {year}... what's up? Ask me anything based on the context provided."
        }), 200

    except Exception as e:
        print(f"Error starting chat for year {year}: {e}")
        return jsonify({'error': f'Error starting chat: {e}'}), 500

@app.route('/api/chat', methods=['POST'])
def send_chat_message():
    data = request.get_json()
    if not data or 'year' not in data or 'message' not in data:
        return jsonify({'error': 'Invalid request data. Requires year and message.'}), 400

    year = str(data.get('year'))
    user_message = data.get('message')

    if year not in active_chats or not active_chats[year].get('chat_session'):
        return jsonify({'error': f'Chat session not started for year {year}. Please start a chat session first.'}), 400

    chat_session = active_chats[year]['chat_session']

    print(f"Received message for year {year}: {user_message}")

    try:
        response = chat_session.send_message(user_message)
        print(f"Received response from AI for year {year}.")
        return jsonify({
            'year': int(year),
            'response': response.text
        }), 200

    except Exception as e:
        print(f"Error sending message to chat for year {year}: {e}")
        return jsonify({'error': f'Error during chat interaction: {e}'}), 500

@app.route('/api/get_processed_files', methods=['GET'])
def get_processed_files():
    print("Getting list of processed files...")
    processed_files_info = {}

    try:
        available_years = data_processor.get_available_years(PROCESSED_DATA_DIR)

        if not available_years:
            return jsonify({'message': 'No processed data found.'}), 200

        for year in sorted(list(available_years)):
            year_data = data_processor.load_year_data(PROCESSED_DATA_DIR, year)

            for entry in year_data:
                source_info = entry.get('source', 'Unknown Source')
                source_type = 'other'
                if 'whatsapp' in source_info.lower():
                    source_type = 'whatsapp'
                elif 'discord' in source_info.lower():
                    source_type = 'discord'
                elif 'instagram' in source_info.lower():
                    source_type = 'instagram'
                elif 'facebook' in source_info.lower():
                    source_type = 'facebook'

                if source_type not in processed_files_info:
                    processed_files_info[source_type] = set()

                display_name = source_info

                if source_type == 'whatsapp':
                    match = re.search(r"WhatsApp Chat with (.*?)(?:\.zip|\.txt)", source_info, re.IGNORECASE)
                    if match:
                        display_name = f"WhatsApp Chat with {match.group(1).strip()}"
                    elif "whatsapp" in source_info.lower():
                         display_name = "WhatsApp Chat (Unknown)"

                elif source_type == 'discord':
                    match = re.search(r"Discord DM \((.*?)\)", source_info, re.IGNORECASE)
                    if match:
                        display_name = f"Discord DM ({match.group(1).strip()})"
                    elif "discord" in source_info.lower():
                         display_name = "Discord Data (Unknown)"

                elif source_type == 'instagram':
                    chat_match_json = re.search(r"Instagram Chat \((.*?)\)", source_info, re.IGNORECASE)
                    if chat_match_json:
                         display_name = f"Instagram Chat ({chat_match_json.group(1).strip()})"
                    elif "instagram" in source_info.lower():
                         path_parts = source_info.split(os.sep)
                         try:
                             inbox_index = path_parts.index('inbox')
                             if inbox_index + 1 < len(path_parts):
                                 display_name = f"Instagram Chat ({path_parts[inbox_index + 1]})"
                             else:
                                 display_name = "Instagram Data (Unknown Chat)"
                         except ValueError:
                             display_name = "Instagram Data (Unknown)"

                elif source_type == 'facebook':
                    conv_match = re.search(r"Facebook Conversation \((.*?)\)", source_info, re.IGNORECASE)
                    if conv_match:
                         display_name = f"Facebook Conversation ({conv_match.group(1).strip()})"
                    elif "facebook" in source_info.lower():
                         display_name = "Facebook Data (Unknown)"

                processed_files_info[source_type].add(display_name)

        processed_files_list = {
            source_type: sorted(list(files)) for source_type, files in processed_files_info.items()
        }

        print(f"Processed files info: {processed_files_list}")

        return jsonify(processed_files_list), 200

    except Exception as e:
        print(f"Error getting processed files: {e}")
        return jsonify({'error': f'Error getting processed files: {e}'}), 500


# --- Removed /api/update_temperature endpoint ---


if __name__ == '__main__':
    # Note: In a production environment, use a production-ready WSGI server
    # like Gunicorn or uWSGI instead of app.run(debug=True).
    app.run(debug=True, port=5000)
