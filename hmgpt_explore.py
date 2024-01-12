import openai
from openai import OpenAI
from dotenv import dotenv_values
import yaml
import random

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


def split(l, LINE_LENGTH=80):
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


# Choose the model
MODEL = "gpt-3.5-turbo-1106"

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


client = get_client(".hmgpt_env_vars")

patients = get_patients("patient-beta.yaml")

patient = choose_patient(patients)

print("Patient chosen for this encounter: ", patient['id'])


# Frame the conversation
talk_framing = [
    {"role": "system", "content": patient['framing']}
]

## Start the conversation

# `talk_hx` is the talk history, we just kick it off...
talk_hx = [
    # {"role": "user", "content": "Hello Mr. Jones, my name is Chris, I am a medic here to help you."},
    # {"role": "assistant", "content": "Hello, my name is Mr. Jones, and I do not know what is going on with me."},
]

# `talk_reminders` will be appended at the end of every human response, to keep the ai on task and prevent digressions.
talk_reminders = [
    {"role": "user", "content": patient['reminders']},
]

# display our "starter" conversation
print()
print("You are working in medical.  A patient appears in front of you.  Speak to them.")
print()
print("  (You can say \"bye\" to end the conversation.)")
# print("(You) >>> ", talk_hx[0]["content"])
# print("(Patient):", talk_hx[1]["content"])
print()
print()

# display the initial prompt
prompt = input("(You) >>> ")

# Loop until the user says "bye"
while prompt.lower().replace("\"","").replace("\'","").strip() != "bye":

    # save the user's input to talk_prompt
    talk_prompt = [{"role":"user", "content":prompt}]

    # combine existing talk_hx with the new user-entere talk_prompt
    talk_hx = talk_hx + talk_prompt
    
    # send the entire conversation to openai to get the next response
    response = client.chat.completions.create(model=MODEL,
        messages= talk_framing + talk_hx + talk_reminders, # ...adding reminders to the end
        temperature=0)
    
    # get the reply
    reply = response.choices[0].message.content

    # split it up
    reply_split = split(reply)

    # display it
    print("(Patient):", end=" ")
    [print(l) for l in reply_split]

    # save the reply in a way it can be added to the talk_hx
    talk_reply = [{"role":"assistant", "content":reply}]

    # add the reply to the end of talk_hx
    talk_hx = talk_hx + talk_reply
    
    # display the prompt
    prompt = input("\n(You) >>> ")