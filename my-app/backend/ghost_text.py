import os
import data_processor
import chatbot
from dotenv import load_dotenv
from collections import Counter

load_dotenv(dotenv_path='.env')

def main():
    print("Welcome to GhostText - Chat with your past self!")

    data_dir = "Data"
    processed_data_dir = "processed_data"
    print(f"\nProcessing data from '{data_dir}'...")
    os.makedirs(processed_data_dir, exist_ok=True)

    processed_years = data_processor.process_data(data_dir, processed_data_dir)

    if not processed_years:
        print(f"\nNo data could be processed or found in '{data_dir}'.")
        print(f"Please make sure your data (zip, txt, etc.) is in the '{data_dir}' folder and try again.")
        return

    print("Data processing complete.")
    available_years = data_processor.get_available_years(processed_data_dir)
    if not available_years:
         print(f"\nNo processed year files found in '{processed_data_dir}'. Cannot continue.")
         return

    print(f"Available years with data: {', '.join(map(str, sorted(available_years)))}")

    selected_year = None
    while selected_year not in available_years:
        try:
            year_input = input("Enter the year you want to talk to: ")
            selected_year = int(year_input)
            if selected_year not in available_years:
                print(f"Sorry, no data found for the year {selected_year}. Please choose from the available years.")
        except ValueError:
            print("Invalid input. Please enter a year number.")

    print(f"\nLoading data for {selected_year} to identify participants...")
    year_data = data_processor.load_year_data(processed_data_dir, selected_year)

    if not year_data:
        print(f"Error: Could not load data for {selected_year} even though it was listed as available.")
        return

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
                sender_counts_by_source[source_type] = Counter()
            sender_counts_by_source[source_type][sender] += 1

    selected_user_names = {}

    print("\nIdentifying your name in each data source:")
    for source_type, sender_counts in sender_counts_by_source.items():
        print(f"\nSource: {source_type.capitalize()}")
        if not sender_counts:
            print(f"  No specific senders found in {source_type} data.")
            continue

        sorted_senders = sorted(sender_counts.items(), key=lambda item: item[1], reverse=True)
        sender_options = [name for name, count in sorted_senders]

        print(f"  Found the following primary senders in {source_type} logs:")
        for i, name in enumerate(sender_options):
            print(f"  {i + 1}. {name} ({sender_counts[name]} messages)")

        user_name_for_source = None
        while user_name_for_source not in sender_options:
            try:
                choice_input = input(f"  Enter the number corresponding to YOUR name for {source_type.capitalize()} (1-{len(sender_options)}): ")
                choice_index = int(choice_input) - 1
                if 0 <= choice_index < len(sender_options):
                    user_name_for_source = sender_options[choice_index]
                    selected_user_names[source_type] = user_name_for_source
                    print(f"  Using '{user_name_for_source}' for {source_type.capitalize()}.")
                else:
                    print("  Invalid number. Please try again.")
            except ValueError:
                    print("  Invalid input. Please enter a number.")

    if not selected_user_names:
        print("\nWarning: Could not identify your name in any data source.")
        manual_name = input("Please manually enter your primary name as it appears in the chat data (or press Enter to proceed without specific user identification): ").strip()
        if manual_name:
            for source_type in sender_counts_by_source.keys():
                 selected_user_names[source_type] = manual_name
            print(f"Using manually entered name: '{manual_name}' for all sources.")
        else:
            print("Proceeding without specific user names. Context will not be filtered to user-only messages.")
            selected_user_names = {}


    print(f"\nConnecting to your {selected_year} self (Identified names: {selected_user_names})...")

    chatbot.start_chat(selected_year, processed_data_dir, selected_user_names)

    print("\nExiting GhostText. Goodbye!")

if __name__ == "__main__":
    main()
