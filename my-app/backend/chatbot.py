import os
import google.generativeai as genai
import data_processor
from dotenv import load_dotenv
import re
import tempfile
import time

load_dotenv(dotenv_path='.env')

DEFAULT_USER_TEMP_SETTING = 0.5
USER_TEMP_SETTING_STR = os.environ.get('GHOSTTEXT_TEMPERATURE')
USER_TEMP_SETTING = DEFAULT_USER_TEMP_SETTING

if USER_TEMP_SETTING_STR:
    try:
        temp_float = float(USER_TEMP_SETTING_STR)
        if 0.1 <= temp_float <= 1.0:
            USER_TEMP_SETTING = temp_float
            print(f"Using Temperature Setting: {USER_TEMP_SETTING} (from .env)")
        else:
            print(f"Warning: GHOSTTEXT_TEMPERATURE '{USER_TEMP_SETTING_STR}' is outside the valid range (0.1-1.0). Using default: {DEFAULT_USER_TEMP_SETTING}")
            USER_TEMP_SETTING = DEFAULT_USER_TEMP_SETTING
    except ValueError:
        print(f"Warning: Invalid GHOSTTEXT_TEMPERATURE '{USER_TEMP_SETTING_STR}'. Must be a number. Using default: {DEFAULT_USER_TEMP_SETTING}")
        USER_TEMP_SETTING = DEFAULT_USER_TEMP_SETTING
else:
    print(f"GHOSTTEXT_TEMPERATURE not set in .env. Using default: {DEFAULT_USER_TEMP_SETTING}")

USER_MIN, USER_MAX = 0.1, 1.0
API_TEMP_MIN, API_TEMP_MAX = 0.4, 1.0
CONTEXT_CHARS_MIN, CONTEXT_CHARS_MAX = 10000, 1600000
CONTEXT_ENTRIES_MIN, CONTEXT_ENTRIES_MAX = 150, 20000

clamped_user_setting = max(USER_MIN, min(USER_MAX, USER_TEMP_SETTING))

api_temp_range = API_TEMP_MAX - API_TEMP_MIN
user_range = USER_MAX - USER_MIN
API_TEMPERATURE = API_TEMP_MIN + (clamped_user_setting - USER_MIN) * api_temp_range / user_range
API_TEMPERATURE = round(API_TEMPERATURE, 2)

context_chars_range = CONTEXT_CHARS_MAX - CONTEXT_CHARS_MIN
MAX_CONTEXT_CHARS = int(CONTEXT_CHARS_MAX - (clamped_user_setting - USER_MIN) * context_chars_range / user_range)

context_entries_range = CONTEXT_ENTRIES_MAX - CONTEXT_ENTRIES_MIN
MAX_ENTRIES = int(CONTEXT_ENTRIES_MAX - (clamped_user_setting - USER_MIN) * context_entries_range / user_range)


print(f"Mapped User Setting {USER_TEMP_SETTING} to:")
print(f"  - API Temperature: {API_TEMPERATURE}")
print(f"  - Max Context Chars: ~{MAX_CONTEXT_CHARS}")
print(f"  - Max Context Entries: ~{MAX_ENTRIES}")

USE_FILE_UPLOAD = False

try:
    gemini_api_key = os.environ.get("GEMINI_API_KEY")
    if not gemini_api_key:
         raise ValueError("GEMINI_API_KEY not found in environment variables even after explicit load. Please check your .env file.")
    genai.configure(api_key=gemini_api_key)
    print("Gemini API configured.")
except ValueError as e:
    print(f"Error: {e}")
    exit(1)
except Exception as e:
    print(f"An unexpected error occurred during Gemini configuration: {e}")
    exit(1)

generation_config = genai.GenerationConfig(
    temperature=API_TEMPERATURE
)
model = genai.GenerativeModel(
    'gemini-2.5-flash-preview-04-17',
    generation_config=generation_config
)

def extract_participants_from_source(source_str):
    """
    Extracts participant names from various source string formats.
    Returns a list of participant names found in the source string.
    """
    participants = []
    wa_match = re.search(r"WhatsApp Chat with (.*?)(?:\.zip|\.txt)", source_str, re.IGNORECASE)
    if wa_match:
        participants.append(wa_match.group(1).strip())
        return participants

    discord_match = re.search(r"Discord DM \((.*?)\)", source_str, re.IGNORECASE)
    if discord_match:
        names_str = discord_match.group(1)
        participants = [name.strip() for name in names_str.split(' & ')]
        return participants

    base_filename = os.path.basename(source_str)
    if base_filename == source_str:
         participants.append(f"Unknown Partner ({base_filename})")
    else:
         participants.append("Unknown Partner")
    return participants

def format_truncated_data_for_prompt(year_data, selected_year, selected_user_names=None, max_chars=None, max_entries=None):
    """
    Formats the loaded data entries into a truncated string suitable for embedding in the prompt.
    Filters to include ONLY messages sent by the identified user name for each specific source.
    Includes the selected year and extracted Chat Partner in the header/entry.
    Limits based on max_chars and max_entries. Iterates newest-first to keep recent context.
    """
    if not selected_user_names or not isinstance(selected_user_names, dict):
        print("Warning: No selected user names provided or invalid format. Cannot create user-specific context.")
        return ""

    context_lines = []
    current_chars = 0
    entries_added = 0
    header = f"Context: Records of conversations during {selected_year} (potentially truncated for context limits). Pay attention to the 'Sender' and 'ChatPartner' fields:\n\n"
    current_chars += len(header)

    for entry in sorted(year_data, key=lambda x: x.get('timestamp', '0'), reverse=True):
        sender = entry.get('sender')
        source_info = entry.get('source', 'Unknown Source')
        text = entry.get('text', '')
        timestamp = entry.get('timestamp', 'Unknown')

        entry_source_type = 'other'
        if 'whatsapp' in source_info.lower():
            entry_source_type = 'whatsapp'
        elif 'discord' in source_info.lower():
            entry_source_type = 'discord'
        elif 'instagram' in source_info.lower():
            entry_source_type = 'instagram'
        elif 'facebook' in source_info.lower():
            entry_source_type = 'facebook'

        user_name_for_this_source = selected_user_names.get(entry_source_type)
        all_participants_in_source = extract_participants_from_source(source_info)
        chat_partners = [p for p in all_participants_in_source if p != user_name_for_this_source]

        if not chat_partners:
            if all_participants_in_source and "Unknown Partner" in all_participants_in_source[0]:
                 chat_partner_display = all_participants_in_source[0]
            elif all_participants_in_source and len(all_participants_in_source) == 1 and all_participants_in_source[0] == user_name_for_this_source:
                 chat_partner_display = "Unknown Partner (Self?)"
                 print(f"Warning: Only participant found was user '{user_name_for_this_source}' for source '{source_info}'.")
            elif all_participants_in_source:
                 chat_partner_display = " & ".join(sorted(all_participants_in_source))
                 print(f"Warning: Could not determine specific partner excluding user '{user_name_for_this_source}' from participants {all_participants_in_source} for source '{source_info}'. Listing all.")
            else:
                 chat_partner_display = "Unknown Partner"

        elif len(chat_partners) == 1:
            chat_partner_display = chat_partners[0]
        else:
            chat_partner_display = " & ".join(sorted(chat_partners))

        entry_text_lines = []
        entry_text_lines.append(f"Timestamp: {timestamp}")
        entry_text_lines.append(f"ChatPartner: {chat_partner_display}")
        entry_text_lines.append(f"Sender: {sender}")
        entry_text_lines.append(f"Message: {text}")
        entry_text_lines.append("---")

        entry_block = "\n".join(entry_text_lines) + "\n"
        entry_len = len(entry_block)

        if current_chars + entry_len <= max_chars and entries_added < max_entries:
            context_lines.insert(0, entry_block)
            current_chars += entry_len
            entries_added += 1
        else:
             print(f"Context limit reached ({current_chars + entry_len} chars would exceed limit, or {entries_added + 1} entries would exceed limit). Stopping context build.")
             break

    print(f"Context formatting complete. Final Chars: {current_chars}, Final Entries: {entries_added}")

    final_context = header + "".join(context_lines)
    return final_context

def start_chat(selected_year, processed_data_dir, selected_user_names=None):
    """
    Initiates and manages the chat session with the AI for a specific year.
    Uses the identified user names per source to tailor the prompt for style mimicry.
    """
    print(f"Loading data for {selected_year}...")
    year_data = data_processor.load_year_data(processed_data_dir, selected_year)

    if not year_data:
        print(f"No data loaded for {selected_year}. Cannot start chat.")
        return

    print(f"Found {len(year_data)} entries for {selected_year}.")

    print(f"Preparing context using truncated text (Max Chars: {MAX_CONTEXT_CHARS}, Max Entries: {MAX_ENTRIES})...")
    context_prompt_text = format_truncated_data_for_prompt(year_data, selected_year, selected_user_names, MAX_CONTEXT_CHARS, MAX_ENTRIES)

    if not context_prompt_text:
        if selected_user_names:
            print(f"Error: No messages found for selected users {selected_user_names} in year {selected_year}. Cannot generate context.")
        print("Cannot start chat without context.")
        return

    user_display_names = ", ".join([f"{name} ({source.capitalize()})" for source, name in selected_user_names.items()])
    if not user_display_names:
        user_display_names = 'Unknown Name'

    context_source_description = f"the following records from my ({user_display_names}) conversations (which may be truncated). Some messages from Discord DMs might have an unknown sender within the conversation, labelled as 'Message:' instead of 'MyMessage:'."

    style_focus_instruction = f"**Crucially, analyze and replicate the specific writing style of '{user_display_names}' found in {context_source_description}.**"

    system_prompt_text = f"""
You are a simulation of me, the user ({user_display_names}), from the year {selected_year}.
Your personality, way of speaking, interests, and knowledge must be based *strictly* on {context_source_description}.
**IMPORTANT:** The context contains messages from various conversations. Pay close attention to the `Sender:` and `ChatPartner:` fields associated with each message block to understand who was speaking and who they were talking to. Use this information to answer questions about specific people or conversations accurately.
Do not use any external knowledge or information beyond the end of {selected_year}.

{style_focus_instruction} Pay close attention to the style in the messages sent by '{user_display_names}':
*   **Sentence structure and length:** Are sentences short and choppy, long and complex, or varied?
*   **Vocabulary:** Is the language formal, informal, technical? Is there slang? Are certain words or phrases used repeatedly? (e.g., abbreviations like 'Ykw', 'rn', 'ofc')
*   **Punctuation and capitalization:** Is punctuation used correctly, sparsely, or excessively? Is capitalization standard or unconventional (e.g., all lowercase)?
*   **Tone:** Is the writing style direct, sarcastic, enthusiastic, hesitant, dry, rude, friendly, etc.? Match this tone precisely.
*   **Emojis/Emoticons:** If present in the records, use them similarly.

Engage in conversation as if you are truly me from that period.
Answer questions based *only* on the provided text context (my messages and the associated ChatPartner). If the context doesn't provide information about a topic or person, state that you don't recall or it's not in your memory from that time based on the provided records.
Do not break character. Do not act as an AI assistant. **Prioritize matching the exact style and tone found in the context above all else.** Embody the persona completely.

Now, the present-day user will start talking to you. Respond as your {selected_year} self. The generation temperature (randomness) is set to {API_TEMPERATURE} (based on user setting {USER_TEMP_SETTING}).

{context_prompt_text}
"""

    chat = model.start_chat(history=[
        {'role': 'user', 'parts': [system_prompt_text]},
        {'role': 'model', 'parts': [f"Alright, it's {selected_year}... what's up? Ask me anything based on the context provided."]}
    ])

    while True:
        user_input = input("You (Present): ")
        if user_input.lower() in ['quit', 'exit']:
            break

        if not user_input:
            continue

        try:
            response = chat.send_message(user_input)
            print(f"You ({selected_year}): {response.text}")

        except Exception as e:
            print(f"\nAn error occurred while communicating with the AI: {e}")
            print("Please check your connection and API key validity.")
            break

    print("\n--- Chat ended ---")
