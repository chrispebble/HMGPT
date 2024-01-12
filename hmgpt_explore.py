import openai
from openai import OpenAI
from dotenv import dotenv_values
import yaml
import random

# -----------------------------------------------------------------------------
# --- CONSTANTS
# -----------------------------------------------------------------------------
apikey_filename = ".hmgpt_env_vars"
patientdata_filename = "patient-beta.yaml"
end_keyword = "done" # word which will trigger the end to the patient encounter
gpt_model = "gpt-3.5-turbo"
our_temp = 1.0

# -----------------------------------------------------------------------------
# --- Function definitions
# -----------------------------------------------------------------------------

def get_client(env_filename):
    """
    Create and return an OpenAI client instance.

    This function initializes an OpenAI client using API key and organization information
    loaded from a specified environment file.

    Parameters:
    env_filename (str): A string specifying the path to the environment file. This file 
                         should contain the API key and organization information 
                         needed for OpenAI client authentication.

    Returns:
    OpenAI: An instance of the OpenAI client, ready to be used for subsequent OpenAI API calls.

    Raises:
    KeyError: If the required environment variables (HMGPT_API_KEY, HMGPT_ORG) are not found in the file.
    """
    hmgpt_env_vars = dotenv_values(env_filename)
    client = OpenAI(api_key=hmgpt_env_vars["HMGPT_API_KEY"], organization=hmgpt_env_vars["HMGPT_ORG"])
    return client


def split_string(l, LINE_LENGTH=80):
    """
    Splits a long string into a list of shorter strings, each not exceeding a specified length.

    This function takes a long string and divides it into a list of shorter strings,
    ensuring that each string is no longer than a given line length. It splits the string 
    at spaces to avoid breaking words. This is particularly useful for formatting text 
    for display in environments with line length limitations.

    Parameters:
    l (str): The long string to be split.
    LINE_LENGTH (int, optional): The maximum length of each line in the returned list. 
                                 Defaults to 80 characters.

    Returns:
    list: A list of strings, each not exceeding the specified LINE_LENGTH.

    Raises:
    ValueError: If LINE_LENGTH is set to a value that does not allow for practical splitting (e.g., too small).
    """
    ret_strings = list()
    remaining = l
    while len(remaining) > (LINE_LENGTH-1):
        split = remaining[:LINE_LENGTH].rfind(" ") # find space nearest the end
        if split == -1:
            # Handling case where no space is found within the limit
            raise ValueError("LINE_LENGTH too small to split the string without breaking words.")
        ret_strings.append(remaining[:split])
        remaining = remaining[split+1:]
    ret_strings.append(remaining)
    return ret_strings


def get_patients(patients_filename):
    """
    Reads patient data from a YAML file and returns it as a list of dictionaries.

    This function opens a specified YAML file, reads its contents, and loads the data into a list. 
    Each element in the list is a dictionary representing a patient's data. The YAML file should 
    be structured such that each patient's data is a separate document.

    Parameters:
    patients_filename (str): The path to the YAML file containing patient data.

    Returns:
    list: A list of dictionaries, where each dictionary contains the data of one patient.

    Note:
    - The function assumes that the YAML file is properly formatted and each patient's data 
      is separated into different documents within the file.
    - It's important to handle exceptions (like FileNotFound) outside of this function when calling it.
    """
    patients = {}
    with open(patients_filename, "r") as file:
        patients = list(yaml.safe_load_all(file))
    return patients

def choose_patient(patients):
    """
    Selects a patient from a list of patients based on weighted probabilities.

    This function takes a list of patient dictionaries. Each dictionary must have a key 'prob_wt' 
    which represents the probability weight of that patient being chosen. The function uses these 
    weights to randomly select a patient from the list.

    Parameters:
    patients (list of dict): A list of patient dictionaries. Each dictionary must contain a 
                             key 'prob_wt' representing the selection weight.

    Returns:
    dict: The selected patient dictionary.

    Example:
    >>> patients = [{'id': 'patient-1', 'prob_wt': 10}, {'id': 'patient-2', 'prob_wt': 20}]
    >>> chosen_patient = choose_patient(patients)
    >>> print(chosen_patient)
    # Output might be: {'id': 'patient-2', 'prob_wt': 20}
    """    
    prob_wts = [p['prob_wt'] for p in patients]
    pt = random.choices(range(len(patients)), weights=prob_wts, k=1)
    return patients[pt[0]]

def new_conversation(system_content):
    """
    Create a new conversation with a system message.

    This function initializes a conversation with a single message from the system. 

    Args:
    system_content (str): The content of the system message to be added to the conversation.

    Returns:
    list: A list containing a single dictionary with the role set to 'system' and the provided content.
    """
    return [{"role": "system", "content": system_content}]


def user_line(user_line):
    """
    Generate a user message in the conversation.

    This function creates a message from the user to be added to the conversation.

    Args:
    user_line (str): The content of the user message.

    Returns:
    list: A list containing a single dictionary with the role set to 'user' and the provided content.
    """
    return [{"role": "user", "content": user_line}]


def asst_line(asst_line):
    """
    Generate an assistant message in the conversation.

    This function creates a message from the assistant to be added to the conversation.

    Args:
    asst_line (str): The content of the assistant message.

    Returns:
    list: A list containing a single dictionary with the role set to 'assistant' and the provided content.
    """
    return [{"role": "assistant", "content": asst_line}]


def get_transcript(talk_hx):
    """
    Generate a transcript from a conversation history.

    This function takes a conversation history and formats it into a readable transcript. User lines are prefixed
    with 'STUDENT:' and other lines are prefixed with 'PATIENT:'.

    Args:
    talk_hx (list): A list of dictionaries representing the conversation history. Each dictionary contains 
    'role' and 'content' keys.

    Returns:
    str: A formatted transcript of the conversation.
    """
    transcript = ""
    for line in talk_hx:
        if line['role'] == "user":
            transcript += "Student: " + line['content'] + "\n\n"
        else:
            transcript += "Patient: " + line['content'] + "\n\n"
    return transcript

# -----------------------------------------------------------------------------
# --- Initialization
# -----------------------------------------------------------------------------
client = get_client(apikey_filename)


# -----------------------------------------------------------------------------
# --- Student conversation with patient
# -----------------------------------------------------------------------------
patients = get_patients(patientdata_filename)
patient = choose_patient(patients)

print("Patient chosen for this encounter: ", patient['id'])


# Frame the conversation
talk_framing = new_conversation(patient['framing'])

## Start the conversation

# talk_hx is the talk history, we just kick it off...
talk_hx = []

# talk_reminders will be appended at the end of every human response, to keep the ai on task and prevent digressions.
talk_reminders = user_line(patient['reminders'])

# display our "starter" conversation
print()
print("You are working in medical.  A patient appears in front of you.  Speak to them.")
print()
print("  (Say \"" + end_keyword + "\" to end the conversation and have your performance reviewed.)")
print()
print()

# display the initial prompt
user_input = input("(You) >>> ")

# Loop until the user says "bye"
while user_input.lower().replace("\"","").replace("\'","").strip() != end_keyword:

    # save the user's input to next_line
    next_line = user_line(user_input)

    # combine existing talk_hx with the new user-entere next_line
    talk_hx = talk_hx + next_line
    
    # print("\n<< sending: ", talk_framing + talk_hx + talk_reminders, ">>>\n")

    # send the entire conversation to openai to get the next response
    response = client.chat.completions.create(model=gpt_model,
        messages= talk_framing + talk_hx + talk_reminders, # ...adding reminders to the end
        temperature=our_temp)

    # get the reply (only the 0th element actually exists)
    reply = response.choices[0].message.content

    # add this reply to the conversation history
    talk_hx = talk_hx + asst_line(reply)

    # print("( total tokens:", response.usage.total_tokens,")")

    # split it up
    reply_split = split_string(reply)

    # display it
    print("(Patient):", end=" ")
    [print(l) for l in reply_split]

    # display the next input prompt
    user_input = input("\n(You) >>> ")


# -----------------------------------------------------------------------------
# --- Evaluate the student's performance
# -----------------------------------------------------------------------------
transcript = get_transcript(talk_hx)

print()
print(". . . You close your eyes, and ponder the memory of this conversation...")
# print()
# print(transcript)
print()

eval_setup = new_conversation("Summarize the following interaction between a me and a standardized patient.")
eval_transcript = user_line(transcript)

response = client.chat.completions.create(model=gpt_model,
    messages= eval_setup + eval_transcript,
    temperature=our_temp)
reply = response.choices[0].message.content
gpt_summary = asst_line(reply)

print("--- SUMMARY OF THIS INTERACTION ---")
print(reply)
print()

eval_summary = user_line("The actual patient summary is as follows:  " 
                         + patient['summary'] 
                         + " How does the student interaction compare with the actual patient summary?")

response = client.chat.completions.create(model=gpt_model,
    messages= eval_setup + eval_transcript + gpt_summary + eval_summary,
    temperature=our_temp)
reply = response.choices[0].message.content

print("=== BEHIND THE CURTAIN===")
print(patient['summary'])
print()

print("--- Evaluation ---")
print(reply)
print()

compare_response = asst_line(reply)
final_question = user_line("Answer only 'yes' or 'no', was the student interaction consistent with the actual patient summary?")

response = client.chat.completions.create(model=gpt_model,
    messages= eval_setup + eval_transcript + gpt_summary + eval_summary + compare_response + final_question,
    temperature=our_temp)
reply = response.choices[0].message.content

print("--- Pass? ---")
print(reply)
print()
