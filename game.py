import pygame
import os
import random
import json
import threading
from generate_map import generate_good_map
from agent import extract_code
from groq import Groq

TILE_SIZE = 32
MAP_WIDTH, MAP_HEIGHT = 50, 50
VISIBLE_COLS, VISIBLE_ROWS = 10, 8
GAME_WIDTH = TILE_SIZE * VISIBLE_COLS
GAME_HEIGHT = TILE_SIZE * VISIBLE_ROWS
CHATBOX_WIDTH = 300
SCREEN_WIDTH = GAME_WIDTH + CHATBOX_WIDTH
SCREEN_HEIGHT = GAME_HEIGHT

# Colors
def load_color_dict():
    try:
        with open('properties/color.json', 'r') as f:
            color_dict = json.load(f)
            # Convert each color to a tuple
            for key, value in color_dict.items():
                color_dict[key] = tuple(value)
            return color_dict
    except FileNotFoundError:
        print("colors.json not found, using default colors.")
        return {
            'G': (50, 200, 50),
            'B': (34, 139, 34),
            'S': (100, 100, 100),
            'R': (30, 144, 255)
        }

COLOR_DICT = load_color_dict()

PLAYER_COLOR = (255, 255, 0)
BLOCKED_TILES = ['R', 'S']

MAP_FILE = "properties/map.txt"

# Player position
player_x, player_y = 2, 2

# Map generator
def generate_random_map():
    tiles = ['G'] * 70 + ['B'] * 15 + ['S'] * 10 + ['R'] * 5  # Adjust ratios
    map_data = []
    for _ in range(MAP_HEIGHT):
        row = [random.choice(tiles) for _ in range(MAP_WIDTH)]
        map_data.append(row)
    return map_data

# Save to file
def save_map(map_data):
    with open(MAP_FILE, "w") as f:
        for row in map_data:
            f.write("".join(row) + "\n")

# Load from file
def load_map():
    with open(MAP_FILE, "r") as f:
        lines = f.read().splitlines()
    return [list(line.strip()) for line in lines]

# Load or create map
if os.path.exists(MAP_FILE):
    game_map = load_map()
else:
    game_map = generate_good_map()
    save_map(game_map)

# Init pygame
pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("World Explorer")
clock = pygame.time.Clock()

# Initialize fonts
pygame.font.init()
font = pygame.font.SysFont('Arial', 16)
title_font = pygame.font.SysFont('Arial', 20, bold=True)

# Chatbox variables
chat_input = ""
chat_history = [
    "Map Editor Chatbox!",
    "Game started with pre-existing colors from color.json",
    "Use this chatbox only if you want to make changes to the map or colors",
    "Press TAB to activate/deactivate the chatbox."
]
chat_active = False
processing = False
processing_message = "Processing..."

# Groq client initialization
client = Groq(
    api_key='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',
)

def draw_world():
    top = max(0, player_y - VISIBLE_ROWS // 2)
    left = max(0, player_x - VISIBLE_COLS // 2)

    if top + VISIBLE_ROWS > MAP_HEIGHT:
        top = MAP_HEIGHT - VISIBLE_ROWS
    if left + VISIBLE_COLS > MAP_WIDTH:
        left = MAP_WIDTH - VISIBLE_COLS

    for row in range(VISIBLE_ROWS):
        for col in range(VISIBLE_COLS):
            map_x = left + col
            map_y = top + row
            tile = game_map[map_y][map_x]
            color = COLOR_DICT.get(tile, (0, 0, 0))
            pygame.draw.rect(screen, color, (col * TILE_SIZE, row * TILE_SIZE, TILE_SIZE, TILE_SIZE))

    px = (player_x - left) * TILE_SIZE + 5
    py = (player_y - top) * TILE_SIZE + 5
    pygame.draw.rect(screen, PLAYER_COLOR, (px, py, TILE_SIZE - 8, TILE_SIZE - 8))

def draw_chatbox():
    # Draw chatbox background
    chatbox_rect = pygame.Rect(GAME_WIDTH, 0, CHATBOX_WIDTH, SCREEN_HEIGHT)
    pygame.draw.rect(screen, (50, 50, 50), chatbox_rect)
    pygame.draw.line(screen, (100, 100, 100), (GAME_WIDTH, 0), (GAME_WIDTH, SCREEN_HEIGHT), 2)

    # Draw chatbox title
    title_text = title_font.render("Map Editor Chatbox", True, (255, 255, 255))
    screen.blit(title_text, (GAME_WIDTH + 10, 10))

    # Draw horizontal line under title
    pygame.draw.line(screen, (100, 100, 100), (GAME_WIDTH, 40), (SCREEN_WIDTH, 40), 1)

    # Draw chat history
    history_surface = pygame.Surface((CHATBOX_WIDTH - 20, SCREEN_HEIGHT - 100))
    history_surface.fill((70, 70, 70))
    y_offset = 10
    for message in chat_history[-8:]:  # Show last 8 messages
        text_surface = font.render(message, True, (255, 255, 255))
        text_rect = text_surface.get_rect()
        if text_rect.width > CHATBOX_WIDTH - 40:
            words = message.split(' ')
            line = ""
            for word in words:
                test_line = line + word + " "
                test_surface = font.render(test_line, True, (255, 255, 255))
                if test_surface.get_width() > CHATBOX_WIDTH - 40:
                    text_surface = font.render(line, True, (255, 255, 255))
                    history_surface.blit(text_surface, (10, y_offset))
                    y_offset += 20
                    line = word + " "
                else:
                    line = test_line
            if line:
                text_surface = font.render(line, True, (255, 255, 255))
                history_surface.blit(text_surface, (10, y_offset))
                y_offset += 20
        else:
            history_surface.blit(text_surface, (10, y_offset))
            y_offset += 20

    screen.blit(history_surface, (GAME_WIDTH + 10, 50))

    # Draw input box
    input_box = pygame.Rect(GAME_WIDTH + 10, SCREEN_HEIGHT - 40, CHATBOX_WIDTH - 20, 30)
    pygame.draw.rect(screen, (100, 100, 100), input_box)

    # Draw input text or processing message
    if processing:
        input_text = font.render(processing_message, True, (200, 200, 200))
    else:
        input_text = font.render(chat_input, True, (255, 255, 255))
    screen.blit(input_text, (input_box.x + 5, input_box.y + 5))

    # Draw cursor if chatbox is active and not processing
    if chat_active and not processing:
        cursor_pos = font.size(chat_input)[0] + input_box.x + 5
        pygame.draw.line(screen, (255, 255, 255), 
                         (cursor_pos, input_box.y + 5), 
                         (cursor_pos, input_box.y + 25), 
                         2)

def process_chat_input(input_text):
    global processing, game_map, COLOR_DICT

    processing = True
    chat_history.append(f"You: {input_text}")

    # Define a function to run in a separate thread
    def process_request():
        global processing, game_map, COLOR_DICT

        try:
            # Load current files for context
            with open('game.py', 'r') as f:
                game_code = f.read()

            with open('generate_map.py', 'r') as f:
                generate_map_code = f.read()

            with open('properties/map.txt', 'r') as f:
                map_code = f.read()

            with open('properties/color.json', 'r') as f:
                color_code = f.read()

            # Create context for the AI
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

            # Send request to Groq
            chat_completion = client.chat.completions.create(
                messages=[
                    {
                        "role": "user",
                        "content": f"You are a helpful AI whose main job it to give out code"
                                  f"{code_context}"
                                  f"I need you to give me code changes to make in color.json and/or map.txt not in any other code file."
                                  f"I need you to give out the code the that we want to change in a certain manner so that I can extract it and apply it"
                                  f"I need you to output your response in a special json format which i can extract easily"
                                  f"Please make any changes to the variable names and no need to add comments to the code"
                                  f"Give the code inside a json code block like this: ```json\n{{\"your\": \"code\"}}\n```"
                                  f"Rules for giving out the code:"
                                  f"1. the variable names should be wrapped in double quotations"
                                  f"2. dont make any changes to pre existing formats"
                                  f"3. If changing the map, provide the full map.txt content"
                    },
                    {
                        "role": "user",
                        "content": f"{input_text}"
                    }
                ],
                model="meta-llama/llama-4-maverick-17b-128e-instruct"
            )

            response = chat_completion.choices[0].message.content
            extractable_output = str(response)

            # Add AI response to chat history
            chat_history.append(f"AI: Processing your request...")

            # Extract and save the code
            extracted_code = extract_code(extractable_output)
            if extracted_code:
                # Check if it's a color change (JSON object)
                if extracted_code.strip().startswith('{') and extracted_code.strip().endswith('}'):
                    with open('properties/color.json', 'w') as f:
                        f.write(extracted_code)

                    # Reload color dictionary
                    COLOR_DICT = load_color_dict()
                    chat_history.append(f"AI: Color changes applied successfully!")

                # Check if it's a map change (multi-line text)
                elif any(terrain in extracted_code for terrain in ['G', 'B', 'S', 'R']):
                    with open('properties/map.txt', 'w') as f:
                        f.write(extracted_code)

                    # Reload map
                    game_map = load_map()
                    chat_history.append(f"AI: Map changes applied successfully!")

                else:
                    chat_history.append(f"AI: Received response but couldn't determine the type of change.")
            else:
                chat_history.append(f"AI: Sorry, I couldn't extract valid code from the response.")

        except Exception as e:
            chat_history.append(f"Error: {str(e)}")

        finally:
            processing = False
    threading.Thread(target=process_request).start()

# Game loop
running = True
while running:
    screen.fill((0, 0, 0))
    draw_world()
    draw_chatbox()  # Draw the chatbox
    pygame.display.flip()
    clock.tick(10)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        # Handle keyboard events for chatbox
        elif event.type == pygame.KEYDOWN:
            # Toggle chatbox active state with Tab key
            if event.key == pygame.K_TAB:
                chat_active = not chat_active

            # Process chatbox input when active
            elif chat_active and not processing:
                if event.key == pygame.K_RETURN:  # Enter key
                    if chat_input.strip():  # Only process non-empty input
                        process_chat_input(chat_input)
                        chat_input = ""  # Clear input after processing
                elif event.key == pygame.K_BACKSPACE:
                    chat_input = chat_input[:-1]  # Remove last character
                elif event.key == pygame.K_ESCAPE:
                    chat_active = False  # Deactivate chatbox
                elif event.unicode and len(chat_input) < 50:  # Limit input length
                    chat_input += event.unicode

        # Handle mouse clicks
        elif event.type == pygame.MOUSEBUTTONDOWN:
            # Check if click is in chatbox area
            if event.pos[0] > GAME_WIDTH:
                chat_active = True
            else:
                chat_active = False

    # Only process movement keys if chatbox is not active
    if not chat_active:
        keys = pygame.key.get_pressed()
        dx = dy = 0
        if keys[pygame.K_w] or keys[pygame.K_UP]:
            dy = -1
        elif keys[pygame.K_s] or keys[pygame.K_DOWN]:
            dy = 1
        elif keys[pygame.K_a] or keys[pygame.K_LEFT]:
            dx = -1
        elif keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            dx = 1

        new_x = player_x + dx
        new_y = player_y + dy

        if 0 <= new_x < MAP_WIDTH and 0 <= new_y < MAP_HEIGHT:
            if game_map[new_y][new_x] not in BLOCKED_TILES:
                player_x, player_y = new_x, new_y

pygame.quit()
