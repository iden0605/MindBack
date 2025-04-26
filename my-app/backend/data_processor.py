import os
import zipfile
import json
import re
import io
from datetime import datetime
import tempfile
import shutil
from bs4 import BeautifulSoup

def detect_source(file_path):
    """
    Detects the source platform based on filename or contents (basic).
    Returns a string identifier (e.g., 'whatsapp', 'txt', 'zip', 'unknown').
    """
    filename = os.path.basename(file_path).lower()
    if filename.endswith('.zip'):
        try:
            with zipfile.ZipFile(file_path, 'r') as z:
                file_list = [f.filename.lower() for f in z.infolist()]
                if any('_chat.txt' in f for f in file_list) or any('whatsapp' in f for f in file_list) or 'whatsapp chat with' in filename:
                     return 'whatsapp_zip'

                has_fb_messages_inbox = any(f.startswith('messages/inbox/') and f != 'messages/inbox/' for f in file_list)
                has_fb_message_json = any(re.match(r'messages/inbox/.*/message_\d+\.json', f) for f in file_list)
                if has_fb_messages_inbox and has_fb_message_json:
                    return 'facebook_zip'
                if any('facebook' in f for f in file_list) or 'your_posts_1.json' in file_list:
                    return 'facebook_zip'

                has_ig_activity_path = any(f.startswith('your_instagram_activity/messages/inbox/') for f in file_list)
                if has_ig_activity_path or any('instagram' in f for f in file_list):
                    return 'instagram_zip'

                if 'messages.json' in file_list:
                     return 'instagram_zip'

                if any('reddit' in f for f in file_list):
                    return 'reddit_zip'

                has_messages_dir = any(f.startswith('messages/') and f != 'messages/' for f in file_list)
                has_channel_json = any(re.match(r'messages/c\d+/channel\.json', f) for f in file_list)
                has_messages_json = any(re.match(r'messages/c\d+/messages\.json', f) for f in file_list)

                if has_messages_dir and has_channel_json and has_messages_json:
                    return 'discord_zip'

        except zipfile.BadZipFile:
             print(f"Warning: Could not open zip file {file_path}. Skipping.")
             return 'bad_zip'
        except Exception as e:
            print(f"Warning: Error inspecting zip file {file_path}: {e}. Skipping.")
            return 'unknown_zip'
        return 'generic_zip'
    elif filename.endswith('.txt'):
         if 'whatsapp chat with' in filename:
             return 'whatsapp_txt'
         return 'txt'
    elif filename.endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp')):
        return 'image'
    elif filename.endswith(('.html', '.htm')):
        return 'html'
    else:
        return 'unknown'

def extract_text_from_html(file_path):
    """Extracts text content from an HTML file using BeautifulSoup."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            html_content = f.read()

        soup = BeautifulSoup(html_content, 'html.parser')

        for script_or_style in soup(["script", "style"]):
            script_or_style.extract()

        text = soup.get_text()

        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = '\n'.join(chunk for chunk in chunks if chunk)

        timestamp = datetime.fromtimestamp(os.path.getmtime(file_path)).strftime('%Y-%m-%d %H:%M:%S')
        return [{"timestamp": timestamp, "sender": "System", "text": text, "source": f"html:{os.path.basename(file_path)}"}]

    except Exception as e:
        print(f"Error extracting text from HTML file {file_path}: {e}")
        return []

def parse_whatsapp_content_string(content_string, source_context=""):
    """
    Parses WhatsApp chat messages from a string.
    Handles multiple known WhatsApp export formats.
    """
    entries = []
    pattern = re.compile(
        r"^(?:"
        r"(?P<date1>\d{1,2}/\d{1,2}/\d{2,4}), (?P<time1>\d{1,2}:\d{2}(?:\s|\u202F)(?:AM|PM))\s*-\s*(?P<sender1>.*?):\s*(?P<msg1>.*)"
        r"|"
        r"\[(?P<date2>\d{1,2}/\d{1,2}/\d{2,4}), (?P<time2>\d{1,2}:\d{2}:\d{2})\]\s*(?P<sender2>.*?):\s*(?P<msg2>.*)"
        r")",
        re.IGNORECASE | re.DOTALL
    )
    date_time_pattern = re.compile(
        r"^(?:"
        r"\d{1,2}/\d{1,2}/\d{2,4}, \d{1,2}:\d{2}(?:\s|\u202F)(?:AM|PM)"
        r"|"
        r"\[\d{1,2}/\d{1,2}/\d{2,4}, \d{1,2}:\d{2}:\d{2}\]"
        r")"
    )
    current_date_str = None
    source_label = "whatsapp_zip" if "zip" in str(source_context).lower() else "whatsapp_txt"

    try:
        string_io = io.StringIO(content_string)
        current_entry = None
        parsed_count = 0

        for line in string_io:
            line = line.strip()
            if not line: continue

            match = pattern.match(line)
            if match:
                dt_obj = None
                sender = None
                message = None
                date_str = None
                time_str = None

                if match.group("date1"):
                    date_str = match.group("date1")
                    time_str = match.group("time1")
                    sender = match.group("sender1")
                    message = match.group("msg1")
                    datetime_str_combined = f"{date_str} {time_str}".replace('\u202f', ' ')
                    date_formats_to_try = [
                        '%d/%m/%Y %I:%M %p', '%d/%m/%y %I:%M %p',
                        '%m/%d/%Y %I:%M %p', '%m/%d/%y %I:%M %p',
                        '%Y/%m/%d %I:%M %p', '%Y/%d/%m %I:%M %p',
                        '%d-%m-%Y %I:%M %p', '%d-%m-%y %I:%M %p',
                        '%m-%d-%Y %I:%M %p', '%m-%d-%y %I:%M %p',
                        '%Y-%m-%d %I:%M %p', '%Y-%d-%m %I:%M %p',
                        '%d.%m.%Y %I:%M %p', '%d.%m.%y %I:%M %p',
                        '%m.%d.%Y %I:%M %p', '%m.%d.%y %I:%M %p',
                        '%Y.%m.%d %I:%M %p', '%Y.%d.%m %I:%M %p',
                        '%d/%m/%Y %H:%M', '%d/%m/%y %H:%M',
                        '%m/%d/%Y %H:%M', '%m/%d/%y %H:%M',
                        '%Y/%m/%d %H:%M', '%Y/%d/%m %H:%M',
                        '%d-%m-%Y %H:%M', '%d-%m-%y %H:%M',
                        '%m-%d-%Y %H:%M', '%m-%d-%y %H:%M',
                        '%Y-%m-%d %H:%M', '%Y-%d-%m %H:%M',
                        '%d.%m.%Y %H:%M', '%d.%m.%y %H:%M',
                        '%m.%d.%Y %H:%M', '%m.%d.%y %H:%M',
                        '%Y.%m.%d %H:%M', '%Y.%d.%m %H:%M',
                    ]
                    for fmt in date_formats_to_try:
                        try:
                            dt_obj = datetime.strptime(datetime_str_combined, fmt)
                            break
                        except ValueError:
                            continue

                elif match.group("date2"):
                    date_str = match.group("date2")
                    time_str = match.group("time2")
                    sender = match.group("sender2")
                    message = match.group("msg2")
                    datetime_str_combined = f"{date_str} {time_str}"
                    date_formats_to_try = [
                        '%d/%m/%Y %H:%M:%S', '%d/%m/%y %H:%M:%S',
                        '%m/%d/%Y %H:%M:%S', '%m/%d/%y %H:%M:%S',
                        '%Y/%m/%d %H:%M:%S', '%Y/%d/%m %H:%M:%S',
                        '%d-%m-%Y %H:%M:%S', '%d-%m-%y %H:%M:%S',
                        '%m-%d-%Y %H:%M:%S', '%m-%d-%y %H:%M:%S',
                        '%Y-%m-%d %H:%M:%S', '%Y-%d-%m %H:%M:%S',
                        '%d.%m.%Y %H:%M:%S', '%d.%m.%y %H:%M:%S',
                        '%m.%d.%Y %H:%M:%S', '%m.%d.%y %H:%M:%S',
                        '%Y.%m.%d %H:%M:%S', '%Y.%d.%m %H:%M:%S',
                    ]
                    for fmt in date_formats_to_try:
                        try:
                            dt_obj = datetime.strptime(datetime_str_combined, fmt)
                            break
                        except ValueError:
                            continue

                if dt_obj:
                    current_date_str = dt_obj.strftime('%Y-%m-%d %H:%M:%S')
                    current_entry = {"timestamp": current_date_str, "sender": sender.strip(), "text": message.strip(), "source": source_context}
                    entries.append(current_entry)
                    parsed_count += 1
                else:
                    if date_str and time_str:
                        print(f"Warning: Could not parse date/time: '{date_str} {time_str}' from line: '{line.strip()[:100]}...' in {source_context}")
                    if current_entry:
                         if not date_time_pattern.match(line):
                              current_entry["text"] += "\n" + line
                         else:
                              print(f"Warning: Line looks like a new message start but didn't match full pattern: '{line.strip()[:100]}...' in {source_context}")
                              current_entry = None
                    else:
                         if line.strip():
                             print(f"Warning: Skipping line (no match and no current entry): '{line.strip()[:100]}...' in {source_context}")
                         current_entry = None

            elif current_entry:
                if not date_time_pattern.match(line):
                     current_entry["text"] += "\n" + line
                else:
                    current_entry = None

    except Exception as e:
        print(f"Error parsing WhatsApp content string from {source_context}: {e}")
        import traceback
        print("Traceback:")
        traceback.print_exc()

    print(f"  parse_whatsapp_content_string finished. Parsed {parsed_count} entries.")
    return entries

def extract_text_from_whatsapp_txt(file_path):
    """Extracts messages and attempts to find dates from WhatsApp txt export file."""
    try:
        encodings_to_try = ['utf-8', 'latin-1', 'cp1252']
        content = None
        for enc in encodings_to_try:
            try:
                with open(file_path, 'r', encoding=enc) as f:
                    content = f.read()
                print(f"Successfully read {file_path} with encoding {enc}")
                break
            except UnicodeDecodeError:
                print(f"Failed to read {file_path} with encoding {enc}")
                continue
            except Exception as read_err:
                 print(f"Error reading file {file_path} with encoding {enc}: {read_err}")
                 return []

        if content is None:
             print(f"Error: Could not read file {file_path} with any attempted encoding.")
             return []

        return parse_whatsapp_content_string(content, file_path)
    except Exception as e:
        print(f"Error processing WhatsApp txt file {file_path}: {e}")
        return []

def parse_discord_zip(file_path):
    """
    Parses Discord data package zip file, extracting messages only from DMs (2 participants).
    Assumes the standard Discord package structure with messages.json.
    """
    entries = []
    temp_dir = None
    channel_index = {}
    own_user_name = "YourDiscordUsername#0000"

    try:
        temp_dir = tempfile.mkdtemp()
        print(f"  Extracting Discord package to temporary directory: {temp_dir}")
        with zipfile.ZipFile(file_path, 'r') as z:
            z.extractall(temp_dir)

        user_json_path = os.path.join(temp_dir, 'account', 'user.json')
        if os.path.exists(user_json_path):
            try:
                with open(user_json_path, 'r', encoding='utf-8') as f:
                    user_data = json.load(f)
                own_user_id = user_data.get('id')
                if own_user_id:
                    username = user_data.get('username', f"User_{own_user_id}")
                    discriminator = user_data.get('discriminator', '0000')
                    own_user_name = f"{username}#{discriminator}"
                    print(f"  Loaded own user info: {own_user_name} (ID: {own_user_id})")
                else:
                    print("  Warning: Could not find 'id' in account/user.json. Using default username.")
            except Exception as e:
                print(f"  Warning: Could not load or parse account/user.json: {e}. Using default username.")
        else:
            print("  Warning: account/user.json not found. Using default username.")

        index_json_path = os.path.join(temp_dir, 'messages', 'index.json')
        if not os.path.exists(index_json_path):
            print(f"  Error: messages/index.json not found at {index_json_path}. Cannot process Discord DMs.")
            return entries
        try:
            with open(index_json_path, 'r', encoding='utf-8') as f:
                channel_index = json.load(f)
            print(f"  Successfully loaded messages/index.json (found {len(channel_index)} entries)")
        except Exception as e:
            print(f"  Error: Could not load or parse messages/index.json: {e}")
            return entries

        messages_base_path = os.path.join(temp_dir, 'messages')
        dm_pattern = re.compile(r"Direct Message with (.*)")

        for channel_id, description in channel_index.items():
            dm_match = dm_pattern.match(description)
            if dm_match:
                partner_name = dm_match.group(1).strip()
                if partner_name != "Unknown Participant":
                    channel_dir_name = f"c{channel_id}"
                    channel_path = os.path.join(messages_base_path, channel_dir_name)
                    messages_json_path = os.path.join(channel_path, 'messages.json')

                    if not os.path.isdir(channel_path):
                         print(f"      Warning: Directory {channel_dir_name} not found for channel ID {channel_id}. Skipping.")
                         continue
                    if not os.path.exists(messages_json_path):
                        print(f"      Warning: messages.json not found in {channel_dir_name}. Skipping DM.")
                        continue

                    dm_participants_list = sorted([own_user_name, partner_name])
                    dm_participants_str = " & ".join(dm_participants_list)

                    messages_data = None
                    try:
                        try:
                            with open(messages_json_path, 'r', encoding='utf-8') as f:
                                messages_data = json.load(f)
                        except (json.JSONDecodeError, UnicodeDecodeError):
                            print(f"        Warning: Failed loading messages.json for {channel_dir_name} with utf-8. Trying latin-1...")
                            try:
                                with open(messages_json_path, 'r', encoding='latin-1') as f:
                                    messages_data = json.load(f)
                            except Exception as fallback_err:
                                print(f"        Error: Failed loading messages.json for {channel_dir_name} with fallback encoding: {fallback_err}")
                                continue

                        if not isinstance(messages_data, list):
                            print(f"        Error: Expected messages_data to be a list, but got {type(messages_data)} for {channel_dir_name}. Skipping.")
                            continue

                        msg_parsed_count = 0
                        for msg_index, msg in enumerate(messages_data):
                            if not isinstance(msg, dict):
                                print(f"        Warning: Skipping message at index {msg_index} as it's not a dictionary.")
                                continue

                            msg_id = msg.get('ID')
                            timestamp_str = msg.get('Timestamp')
                            content = msg.get('Contents')
                            sender_name = msg.get('Author', 'Unknown')

                            if not timestamp_str or not content:
                                continue

                            try:
                                timestamp_str_clean = timestamp_str.split('+')[0].replace('T', ' ')
                                if '.' in timestamp_str_clean:
                                    dt_obj = datetime.strptime(timestamp_str_clean, '%Y-%m-%d %H:%M:%S.%f')
                                else:
                                    dt_obj = datetime.strptime(timestamp_str_clean, '%Y-%m-%d %H:%M:%S')
                                formatted_timestamp = dt_obj.strftime('%Y-%m-%d %H:%M:%S')
                            except ValueError:
                                continue

                            msg_parsed_count += 1
                            entries.append({
                                "timestamp": formatted_timestamp,
                                "sender": sender_name,
                                "text": content.strip(),
                                "source": f"{os.path.basename(file_path)} -> Discord DM ({dm_participants_str})"
                            })

                    except Exception as e:
                        print(f"      Error processing messages file {messages_json_path}: {e}")

    except zipfile.BadZipFile:
        print(f"Error: Bad zip file: {file_path}")
    except Exception as e:
        print(f"Error processing Discord zip file {file_path}: {e}")
    finally:
        if temp_dir and os.path.isdir(temp_dir):
            try:
                shutil.rmtree(temp_dir)
            except Exception as e:
                print(f"  Error cleaning up temporary directory {temp_dir}: {e}")

    print(f"  Finished processing Discord zip. Found {len(entries)} DM entries.")
    return entries

def parse_instagram_html(file_path, source_context=""):
    """
    Parses Instagram messages from an HTML file.
    """
    entries = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f, 'html.parser')

        message_blocks = soup.find_all('div', class_='pam _3-95 _2ph- _a6-g uiBoxWhite noborder')

        for block in message_blocks:
            sender_tag = block.find('div', class_='_3-95 _2pim _a6-h _a6-i')
            content_tag = block.find('div', class_='_3-95 _a6-p')
            timestamp_tag = block.find('div', class_='_3-94 _a6-o')

            sender = sender_tag.get_text(strip=True) if sender_tag else "Unknown"
            text_content = ""
            if content_tag:
                for child in content_tag.children:
                    if isinstance(child, str):
                        text_content += child.strip() + "\n"
                    elif child.name == 'div':
                        child_text = child.get_text(strip=True)
                        if child_text:
                            text_content += child_text + "\n"
                    elif child.name == 'a' and child.find('img'):
                         text_content += f"[Image: {child.get('href', 'N/A')}]\n"
                    elif child.name == 'ul':
                         text_content += child.get_text(strip=True) + "\n"

                text_content = text_content.strip()

            timestamp_str = timestamp_tag.get_text(strip=True) if timestamp_tag else None

            if sender and text_content and timestamp_str:
                try:
                    dt_obj = datetime.strptime(timestamp_str, '%b %d, %Y %I:%M %p')
                    formatted_timestamp = dt_obj.strftime('%Y-%m-%d %H:%M:%S')
                except ValueError:
                    print(f"Warning: Could not parse timestamp '{timestamp_str}' in {file_path}. Skipping entry.")
                    continue

                entries.append({
                    "timestamp": formatted_timestamp,
                    "sender": sender,
                    "text": text_content,
                    "source": source_context
                })

    except FileNotFoundError:
        print(f"Error: HTML file not found at {file_path}")
    except Exception as e:
        print(f"Error parsing Instagram HTML file {file_path}: {e}")
    return entries

def parse_instagram_json(file_path, source_context=""):
    """
    Parses Instagram messages from a JSON file.
    """
    entries = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        messages = data.get('messages', [])
        participants = data.get('participants', [])
        chat_title = data.get('title', 'Unknown Chat')

        participant_names = [p.get('name', 'Unknown') for p in participants]
        source_detail = f"Instagram Chat ({chat_title} with {', '.join(participant_names)})"

        for msg in messages:
            sender_name = msg.get('sender_name')
            timestamp_ms = msg.get('timestamp_ms')
            content = msg.get('content')
            media_uri = msg.get('uri')
            media_share = msg.get('media_share')
            sticker = msg.get('sticker')
            photos = msg.get('photos')
            videos = msg.get('videos')
            audio_files = msg.get('audio_files')
            gifs = msg.get('gifs')
            reactions = msg.get('reactions')

            text_content = content if content is not None else ""

            if media_uri:
                 text_content += f"[Media: {media_uri}]"
            if media_share:
                 text_content += f"[Media Share: {media_share.get('uri', 'N/A')}]"
            if sticker:
                 text_content += f"[Sticker: {sticker.get('uri', 'N/A')}]"
            if photos:
                 photo_uris = [p.get('uri', 'N/A') for p in photos]
                 text_content += f"[Photos: {', '.join(photo_uris)}]"
            if videos:
                 video_uris = [v.get('uri', 'N/A') for v in videos]
                 text_content += f"[Videos: {', '.join(video_uris)}]"
            if audio_files:
                 audio_uris = [a.get('uri', 'N/A') for a in audio_files]
                 text_content += f"[Audio Files: {', '.join(audio_uris)}]"
            if gifs:
                 gif_uris = [g.get('uri', 'N/A') for g in gifs]
                 text_content += f"[GIFs: {', '.join(gif_uris)}]"
            if reactions:
                 reaction_details = []
                 for reaction in reactions:
                      actor = reaction.get('actor')
                      reaction_text = reaction.get('reaction')
                      reaction_details.append(f"{actor} reacted with {reaction_text}")
                 text_content += f" ({'; '.join(reaction_details)})"


            if sender_name and timestamp_ms is not None:
                try:
                    dt_obj = datetime.fromtimestamp(timestamp_ms / 1000)
                    formatted_timestamp = dt_obj.strftime('%Y-%m-%d %H:%M:%S')
                except (ValueError, TypeError):
                    print(f"Warning: Could not parse timestamp '{timestamp_ms}' in {file_path}. Skipping entry.")
                    continue

                entries.append({
                    "timestamp": formatted_timestamp,
                    "sender": sender_name.strip(),
                    "text": text_content.strip(),
                    "source": f"{source_context} -> {source_detail}"
                })

    except FileNotFoundError:
        print(f"Error: JSON file not found at {file_path}")
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from file {file_path}")
    except Exception as e:
        print(f"Error parsing Instagram JSON file {file_path}: {e}")
    return entries

def parse_instagram_zip(file_path):
    """
    Parses Instagram data package zip file, extracting messages from HTML and JSON files.
    Assumes the standard Instagram package structure.
    """
    entries = []
    temp_dir = None

    try:
        temp_dir = tempfile.mkdtemp()
        print(f"  Extracting Instagram package to temporary directory: {temp_dir}")
        with zipfile.ZipFile(file_path, 'r') as z:
            z.extractall(temp_dir)

        messages_inbox_path = os.path.join(temp_dir, 'your_instagram_activity', 'messages', 'inbox')
        if not os.path.isdir(messages_inbox_path):
            print(f"  Warning: Messages inbox directory not found at {messages_inbox_path}. Skipping message extraction.")
            return entries

        print(f"  Scanning messages inbox directory: {messages_inbox_path}")
        for root, _, files in os.walk(messages_inbox_path):
            for file in files:
                file_path_abs = os.path.join(root, file)
                relative_file_path = os.path.relpath(file_path_abs, temp_dir)

                if file.lower().endswith('.html'):
                    print(f"    Found HTML message file: {relative_file_path}")
                    parsed_entries = parse_instagram_html(file_path_abs, f"{os.path.basename(file_path)} -> {relative_file_path}")
                    entries.extend(parsed_entries)
                    print(f"    Parsed {len(parsed_entries)} entries from {relative_file_path}")

                elif file.lower().endswith('.json'):
                    print(f"    Found JSON message file: {relative_file_path}")
                    parsed_entries = parse_instagram_json(file_path_abs, f"{os.path.basename(file_path)} -> {relative_file_path}")
                    entries.extend(parsed_entries)
                    print(f"    Parsed {len(parsed_entries)} entries from {relative_file_path}")

        print(f"  Finished scanning Instagram messages. Total entries found: {len(entries)}")

    except zipfile.BadZipFile:
        print(f"Error: Bad zip file: {file_path}")
    except Exception as e:
        print(f"Error processing Instagram zip file {file_path}: {e}")
    finally:
        if temp_dir and os.path.isdir(temp_dir):
            try:
                shutil.rmtree(temp_dir)
                print(f"  Cleaned up temporary directory: {temp_dir}")
            except Exception as e:
                print(f"  Error cleaning up temporary directory {temp_dir}: {e}")

    print(f"  Finished processing Instagram zip. Found {len(entries)} entries.")
    return entries

def parse_facebook_zip(file_path):
    """
    Parses Facebook data package zip file, extracting messages from message_1.json files.
    Assumes the standard Facebook package structure with messages/inbox/<conversation_name>/message_1.json.
    """
    entries = []
    temp_dir = None

    try:
        temp_dir = tempfile.mkdtemp()
        print(f"  Extracting Facebook package to temporary directory: {temp_dir}")
        with zipfile.ZipFile(file_path, 'r') as z:
            z.extractall(temp_dir)

        for root, dirs, files in os.walk(temp_dir):
            for file in files:
                file_lower = file.lower()
                file_path_abs = os.path.join(root, file)

                if file_lower == 'message_1.json':
                    print(f"    Found message file: {file_path_abs}")

                    messages_inbox_path = os.path.join(temp_dir, 'messages', 'inbox')
                    conversation_name = "Unknown Conversation"

                    if os.path.commonpath([messages_inbox_path, root]) == messages_inbox_path:
                         relative_path = os.path.relpath(root, messages_inbox_path)
                         if relative_path != '.':
                            conversation_name = os.path.basename(relative_path)
                         else:
                            conversation_name = "Inbox"

                    messages_data = None
                    try:
                        try:
                            with open(file_path_abs, 'r', encoding='utf-8') as f:
                                messages_data = json.load(f)
                        except (json.JSONDecodeError, UnicodeDecodeError):
                            print(f"      Warning: Failed loading {file} with utf-8. Trying latin-1...")
                            try:
                                with open(file_path_abs, 'r', encoding='latin-1') as f:
                                    messages_data = json.load(f)
                            except Exception as fallback_err:
                                print(f"      Error: Failed loading {file} with fallback encoding: {fallback_err}")
                                continue

                        if not isinstance(messages_data, dict):
                            print(f"      Error: Expected messages_data to be a dictionary, but got {type(messages_data)} for {file_path_abs}. Skipping.")
                            continue

                        if 'messages' in messages_data and isinstance(messages_data['messages'], list):
                            print(f"      Parsing {len(messages_data['messages'])} messages from conversation '{conversation_name}'...")
                            msg_parsed_count = 0
                            for msg in messages_data['messages']:
                                if not isinstance(msg, dict):
                                    continue

                                timestamp_ms = msg.get('timestamp_ms')
                                sender_name = msg.get('sender_name')
                                content = msg.get('content')

                                if not sender_name:
                                    sender_name = "Participant"

                                if timestamp_ms is None or content is None:
                                    continue

                                try:
                                    timestamp_sec = timestamp_ms / 1000
                                    dt_obj = datetime.fromtimestamp(timestamp_sec)
                                    formatted_timestamp = dt_obj.strftime('%Y-%m-%d %H:%M:%S')
                                except (ValueError, TypeError):
                                    continue

                                msg_parsed_count += 1
                                entries.append({
                                    "timestamp": formatted_timestamp,
                                    "sender": sender_name.strip(),
                                    "text": content.strip(),
                                    "source": f"{os.path.basename(file_path)} -> Facebook Conversation ({conversation_name})"
                                })
                            print(f"      Finished parsing. Successfully parsed {msg_parsed_count}/{len(messages_data['messages'])} messages.")
                        else:
                            print(f"      Warning: 'messages' key not found or is not a list in {file_path_abs}. Skipping.")

                    except Exception as e:
                        print(f"    Error processing message file {file_path_abs}: {e}")

                elif file_lower.endswith(('.html', '.htm')):
                    print(f"    Found HTML file: {file_path_abs}")
                    html_entries = extract_text_from_html(file_path_abs)
                    if html_entries:
                        for entry in html_entries:
                            entry["source"] = f"{os.path.basename(file_path)} -> Facebook HTML ({os.path.basename(file_path_abs)})"
                        entries.extend(html_entries)
                        print(f"      Successfully extracted {len(html_entries)} entries from HTML file.")
                    else:
                        print(f"      Warning: Could not extract any entries from HTML file {file_path_abs}.")


    except zipfile.BadZipFile:
        print(f"Error: Bad zip file: {file_path}")
    except Exception as e:
        print(f"Error processing Facebook zip file {file_path}: {e}")
    finally:
        if temp_dir and os.path.isdir(temp_dir):
            try:
                shutil.rmtree(temp_dir)
                print(f"  Cleaned up temporary directory: {temp_dir}")
            except Exception as e:
                print(f"  Error cleaning up temporary directory {temp_dir}: {e}")

    print(f"  Finished processing Facebook zip. Found {len(entries)} entries (messages and HTML).")
    return entries

def extract_from_zip(file_path, source_type):
    """Extracts relevant data from zip files based on detected source type."""
    entries = []
    print(f"Processing zip file: {file_path} (detected as: {source_type})")
    try:
        if source_type == 'whatsapp_zip':
            with zipfile.ZipFile(file_path, 'r') as z:
                chat_file = next((f for f in z.namelist() if f.lower().endswith('.txt')), None)
                if chat_file:
                    print(f"  Found potential chat file: {chat_file} inside zip.")
                    try:
                        with z.open(chat_file) as f:
                            content = None
                            encodings_to_try = ['utf-8', 'latin-1', 'cp1252']
                            last_decode_error = None
                            for enc in encodings_to_try:
                                try:
                                    f.seek(0)
                                    content = f.read().decode(enc)
                                    print(f"  Successfully decoded {chat_file} with encoding {enc}")
                                    break
                                except UnicodeDecodeError as decode_err:
                                    last_decode_error = decode_err
                                    print(f"  Failed decoding {chat_file} with {enc}")
                                    continue
                                except Exception as inner_read_err:
                                    print(f"  Error reading {chat_file} with {enc}: {inner_read_err}")
                                    last_decode_error = inner_read_err
                                    break

                            if content is not None:
                                parsed_entries = parse_whatsapp_content_string(content, f"{file_path} -> {chat_file}")
                                if parsed_entries:
                                     entries.extend(parsed_entries)
                                     print(f"  Successfully parsed {len(parsed_entries)} entries from {chat_file}.")
                                else:
                                     print(f"  Warning: Could not parse any entries from {chat_file} content. Adding placeholder.")
                                     try:
                                         timestamp = datetime.fromtimestamp(os.path.getmtime(file_path)).strftime('%Y-%m-%d %H:%M:%S')
                                     except Exception:
                                         timestamp = "0000-00-00 00:00:00"
                                     entries.append({"timestamp": timestamp, "sender": "System", "text": f"Placeholder (parsing failed) for {chat_file}", "source": file_path})
                            else:
                                print(f"  Error: Could not decode {chat_file} with any attempted encoding. Last error: {last_decode_error}")
                    except Exception as read_err:
                         print(f"  Error opening or processing {chat_file} from zip {file_path}: {read_err}")
                else:
                    print(f"  Warning: Could not find any '.txt' chat file in WhatsApp zip: {file_path}")

        elif source_type == 'discord_zip':
            entries = parse_discord_zip(file_path)

        elif source_type == 'instagram_zip':
             entries = parse_instagram_zip(file_path)

        elif source_type == 'facebook_zip':
             entries = parse_facebook_zip(file_path)

        elif source_type in ['reddit_zip', 'generic_zip']:
             print(f"  Extraction logic for {source_type} is not implemented yet.")
             try:
                 timestamp = datetime.fromtimestamp(os.path.getmtime(file_path)).strftime('%Y-%m-%d %H:%M:%S')
             except Exception:
                 timestamp = "0000-00-00 00:00:00"
             entries.append({"timestamp": timestamp, "sender": "System", "text": f"Placeholder for {source_type} data from {os.path.basename(file_path)}", "source": source_type})

    except zipfile.BadZipFile:
        print(f"Error: Bad zip file: {file_path}")
    except Exception as e:
        print(f"Error processing zip file {file_path}: {e}")
    return entries

def process_data(data_dir, processed_data_dir):
    """
    Scans the data directory, processes each file, and saves structured data by year.
    Returns a tuple: (set of years with data, list of unprocessed filenames).
    """
    all_data = {}
    processed_files_set = set()
    unprocessed_files = []

    print(f"Scanning directory: {data_dir}")
    if not os.path.isdir(data_dir):
        print(f"Error: Data directory '{data_dir}' not found.")
        return set(), []

    files_in_data_dir = [f for f in os.listdir(data_dir) if os.path.isfile(os.path.join(data_dir, f))]
    print(f"  Files found in {data_dir}: {files_in_data_dir}")

    for filename in files_in_data_dir:
        file_path = os.path.join(data_dir, filename)
        if os.path.isfile(file_path):
            print(f"\nProcessing file: {filename}")
            source_type = detect_source(file_path)
            print(f"  Detected source: {source_type}")

            extracted_entries = []
            if source_type == 'whatsapp_txt':
                print(f"  Calling extract_text_from_whatsapp_txt for {filename}")
                extracted_entries = extract_text_from_whatsapp_txt(file_path)
            elif source_type.endswith('_zip'):
                 print(f"  Calling extract_from_zip for {filename} with source type {source_type}")
                 extracted_entries = extract_from_zip(file_path, source_type)
            elif source_type == 'html':
                print(f"  Calling extract_text_from_html for {filename}")
                extracted_entries = extract_text_from_html(file_path)
            elif source_type == 'txt':
                print(f"  Processing generic txt file: {filename}")
                try:
                    encodings_to_try = ['utf-8', 'latin-1', 'cp1252']
                    content = None
                    for enc in encodings_to_try:
                        try:
                            with open(file_path, 'r', encoding=enc) as f:
                                content = f.read()
                            break
                        except UnicodeDecodeError:
                            continue
                        except Exception as read_err:
                             print(f"  Error reading text file {filename} with {enc}: {read_err}")
                             content = None
                             break

                    if content is not None:
                        timestamp = datetime.fromtimestamp(os.path.getmtime(file_path)).strftime('%Y-%m-%d %H:%M:%S')
                        extracted_entries.append({"timestamp": timestamp, "sender": "Unknown", "text": content, "source": "txt"})
                    else:
                        print(f"  Error: Could not read text file {filename} with any attempted encoding.")

                except Exception as e:
                    print(f"  Error processing text file {filename}: {e}")
            elif source_type == 'image':
                print(f"  Image file detected: {filename}. Processing not yet implemented.")
                timestamp = datetime.fromtimestamp(os.path.getmtime(file_path)).strftime('%Y-%m-%d %H:%M:%S')
                extracted_entries.append({"timestamp": timestamp, "sender": "System", "text": f"[Image File: {filename}]", "source": "image"})
            elif source_type != 'bad_zip' and source_type != 'unknown_zip':
                print(f"  Skipping unsupported or unknown file type: {filename} ({source_type})")

            print(f"  Extracted {len(extracted_entries)} entries from {filename}.")
            if extracted_entries:
                processed_files_set.add(filename)
                for entry in extracted_entries:
                    try:
                        year = int(entry.get("timestamp", "0000")[:4])
                        if year > 0:
                            if year not in all_data:
                                all_data[year] = []
                            all_data[year].append(entry)
                        else:
                             print(f"Warning: Invalid year '0000' or less found for entry in {filename}. Attempting fallback.")
                             raise ValueError("Invalid year")
                    except (ValueError, TypeError, IndexError):
                         try:
                             mod_time = os.path.getmtime(file_path)
                             year = datetime.fromtimestamp(mod_time).year
                             if year > 0:
                                 print(f"  Fallback: Using file modification year {year} for an entry from {filename} due to invalid timestamp: {entry.get('timestamp')}")
                                 if year not in all_data:
                                     all_data[year] = []
                                 all_data[year].append(entry)
                             else:
                                  print(f"Warning: Could not determine fallback year for an entry from {filename}. Entry: {entry}")
                         except Exception as mod_err:
                              print(f"Warning: Could not determine fallback year for an entry from {filename} (mod time error: {mod_err}). Entry: {entry}")
            else:
                unprocessed_files.append(filename)

    os.makedirs(processed_data_dir, exist_ok=True)
    processed_years = set()
    if not all_data:
        print("\nNo data entries were successfully extracted to save.")
        return processed_years, files_in_data_dir

    print("\nSaving processed data by year...")
    for year, entries in all_data.items():
        entries.sort(key=lambda x: x.get('timestamp', '0'))

        filtered_entries = []
        last_added_entry = None
        for entry in entries:
            is_duplicate = False
            if last_added_entry:
                if (entry.get('timestamp') == last_added_entry.get('timestamp') and
                    entry.get('sender') == last_added_entry.get('sender') and
                    entry.get('text') == last_added_entry.get('text') and
                    entry.get('source') == last_added_entry.get('source')):
                    is_duplicate = True

            if not is_duplicate:
                filtered_entries.append(entry)
                last_added_entry = entry

        if not filtered_entries:
             print(f"Skipping year {year} as no entries remained after filtering duplicates.")
             continue

        output_path = os.path.join(processed_data_dir, f"{year}.json")
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(filtered_entries, f, indent=2, ensure_ascii=False)
            print(f"Saved {len(filtered_entries)} entries for {year} to {output_path} (Original: {len(entries)})")
            processed_years.add(year)
        except Exception as e:
            print(f"Error saving data for year {year} to {output_path}: {e}")

    print(f"Finished saving processed data. Processed years: {processed_years}")
    return processed_years, unprocessed_files

def get_available_years(processed_data_dir):
    """Scans the processed data directory for available year files (YYYY.json)."""
    available_years = set()
    if not os.path.exists(processed_data_dir):
        return available_years

    for filename in os.listdir(processed_data_dir):
        if filename.endswith('.json'):
            file_path = os.path.join(processed_data_dir, filename)
            if os.path.isfile(file_path):
                match = re.match(r"(\d{4})\.json", filename)
                if match:
                    try:
                        year = int(match.group(1))
                        available_years.add(year)
                    except ValueError:
                        continue
    return available_years

def load_year_data(processed_data_dir, year):
    """Loads the processed data for a specific year."""
    file_path = os.path.join(processed_data_dir, f"{year}.json")
    if not os.path.exists(file_path):
        print(f"Error: Processed data file not found for year {year} at {file_path}")
        return []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from file {file_path}")
        return []
    except Exception as e:
        print(f"Error loading data for year {year} from {file_path}: {e}")
        return []
