import os
import json
import re
from groq import Groq

import re

def extract_code(text: str) -> str:
    """
    Extracts the raw JSON string from a Markdown-style fenced block.
    """
    match = re.search(r"```json\s*(\{.*?\})\s*```", text, re.DOTALL)
    if match:
        return match.group(1).strip()
    else:
        print("No valid JSON code block found.")
        return ""


client = Groq(
    api_key='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',
)

with open('game.py', 'r') as f:
    print("Game code file read")
    game_code = f.read()

with open('generate_map.py', 'r') as f:
    print("Generate map code file read")
    generate_map_code = f.read()

with open('properties/map.txt', 'r') as f:
    print("Map code file read")
    map_code = f.read()

with open('properties/color.json', 'r') as f:
    print("Color code file read")
    color_code = f.read()

code_context = f'''
This the current code which I can share with you, the user can ask you to do something such as change the color scheme, or make the map
look in a certain way, you have the liberty to change the colors of the map and give the code in the same format and the same way it was 
given earlier and then I can through logic make those changes instantly, this not limited to just colors but also the map which is given in the
map.txt file

Here is the main python code running the game 

game.py:

{game_code}

Here is the generate_map.py file:

{generate_map_code}

here is the map.txt file:

{map_code}

here is the colors.json file:

{color_code}

I need you to give the code in a special block 
'''

user_input = input("what do you want: ")
chat_completion = client.chat.completions.create(


messages=[
{  "role": "user",
   "content": f"You are a helpful AI whose main job it to give out code"
              f"{code_context}"
              f"I need you to give me code changes to make only in color.json and map.txt not in any other code file."
              f"I need you to give out the code the that we want to change in a certain manner so that I can extract it and apply it"
              f"I need you to output your response in a special json format which i can extract easily"
              f"Please make any changes to the variable names and no need to add comments to the code"
              f"for now only give out the code for the color.json inside a json holder and dont give any other code for any other file"
              f"Rules for giving out the color.json file code:"
              f"1. the variable names should be wrapped in double quotations"
              f"2. dont make any changes to pre existing formats"
},
{
   "role": "user",
   "content": f"{user_input}"
}
],
    model="meta-llama/llama-4-maverick-17b-128e-instruct"
)
response = chat_completion.choices[0].message.content
extractable_output = str(response)
print(extractable_output)

extractable_output = extract_code(extractable_output)
extractable_output = str(extractable_output)

with open('properties/color.json', 'w') as f:
    f.write(extractable_output)
