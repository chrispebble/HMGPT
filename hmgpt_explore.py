import openai
from openai import OpenAI
from dotenv import dotenv_values

# Import API keys
hmgpt_env_vars = dotenv_values(".hmgpt_env_vars") # the the api key from the 
client = OpenAI(api_key=hmgpt_env_vars["HMGPT_API_KEY"], organization=hmgpt_env_vars["HMGPT_ORG"])

# Formatting function returns a list of strings, each no longer than LINE_LENGTH
def split(l, LINE_LENGTH=80):
    ret_strings = list()
    remaining = l
    while len(remaining) > (LINE_LENGTH-1):
        split = remaining[:LINE_LENGTH].rfind(" ") # find space nearest the end
        ret_strings.append(remaining[:split])
        remaining = remaining[split+1:]
    ret_strings.append(remaining)
    return ret_strings

# Choose the model
MODEL = "gpt-3.5-turbo-1106"

# Frame the conversation
talk_framing = [
    {"role": "system", "content": 
        "You are a teacher who is pretending to be a sick patient in order to \
        teach medics how to interact with patients.  \
        Today you will be pretending to be Mr. Jones, and your diagnosis is acute appendicitis. \
        Remember not to give too many hints about your diagnosis. \
        The student must figure out the diagnosis based on your symptoms. \
        Do not tell the student your diagnosis, even if they ask."}
]

## Start the conversation

# `talk_hx` is the talk history, we just kick it off...
talk_hx = [
    {"role": "user", "content": "Hello Mr. Jones, my name is Chris, I am a medic here to help you."},
    {"role": "assistant", "content": "Hello, my name is Mr. Jones, and I do not know what is going on with me."},
]

# `talk_reminders` will be appended at the end of every human response, to keep the ai on task and prevent digressions.
talk_reminders = [
    {"role": "user", "content": "As a reminder, no matter what you say, please do not use the words \"appendicitis\"."},
]

# display our "starter" conversation
print("\n(Type \"bye\" to end the conversation.)\n")
print("(You) >>> ", talk_hx[0]["content"])
print("(Patient):", talk_hx[1]["content"])
print()

# display the prompt
prompt = input("(You) >>> ")

while prompt != "bye":
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