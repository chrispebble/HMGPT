# HM GPT for CSSP Project

## Build Info
Built and tested using Python version 3.10.
More comprehensive build instructions to follow.

### API Keys
The file `.hmgpt_env_vars` must exist in the local directory, with two variables in this format:
```
HMGPT_API_KEY=add_the_api_key_here"
HMGPT_ORG="org-your_org_here"
``````

## Initial Roadmap
1. Create a workable test platform to explore how to prompt ChatGPT in a way that creates a workable standardized patient
2. Create the stardardized patient prompts
   1. Start with one algorithm and go through the entire process for all versions of the patient (uncomplicated, complicated, red flag, etc...)
   2. Then expand to include all algorithms
3. Once workable patients of all types exist, convert this to a web-interface
   1. Python back-end (Google vs AWS)
   2. HTML front-end

Final product should include:
- [ ] Standardized patient encounters for all CSSP algorithms
- [ ] A front end that allows saving/sending the encounter so that it can be reviewed
- [ ] Ideally, a way to capture all encounters as these interactions may provide useful data for future projects

## Useful Links:
- https://platform.openai.com/docs/api-reference/introduction
- https://www.cloudbees.com/blog/yaml-tutorial-everything-you-need-get-started
- 