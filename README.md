# Codepilot-teamwork
# Farming Land

**Farming Land** is a pixel-art farming simulation game inspired by Stardew Valley and Harvest Moon. Players can plant crops, chop trees, collect apples and wood, interact with a pet, and trade with an in-game AI-powered shopkeeper. The game is built with Python and Pygame, featuring a tile-based world, day/night cycle, weather, and a simple save/load system.

---

## Features

- **Plant and Grow Crops:** Till the soil, plant seeds (corn, tomato), water them, and harvest when mature.
- **Chop Trees:** Use your axe to chop trees for wood and apples.
- **Dynamic Weather:** Rain will automatically water all tilled soil.
- **Day/Night Cycle:** Time passes as you play; sleep in bed to start a new day.
- **Pet Companion:** A pet follows you and occasionally displays random dialogues.
- **Shop System:** Buy seeds and sell items at the Trader using an in-game menu.
- **AI Chat:** Press TAB to open an AI chatbox for in-game help and tips (requires a local LLM API).
- **Save/Load:** Press `X` to save your progress; load automatically on startup.
- **Custom Graphics and Sound:** Hand-drawn pixel art, custom fonts, and sound effects.

---

## Controls

| Key         | Action                                 |
|-------------|----------------------------------------|
| Arrow Keys  | Move                                  |
| SPACE       | Use tool (hoe/axe/water) Sell/Buy in shop             |
| Q           | Switch tool                           |
| E           | Switch seed                           |
| CTRL        | Plant seed                            |
| ENTER       | Interact (Trader shop, Bed sleep)     |
| M           | Open/Close shop menu                  |
| TAB         | Toggle/Close AI chat                  |
| ESC         | Back to title                         |
| X           | Save game                             |


---

## How to Play

- **Start a New Game** or **Load Game** from the title screen.
- Use your tools to till soil, plant seeds, water crops, and chop trees.
- Harvest crops and collect apples/wood from trees.
- Visit the Trader to buy seeds or sell your items for money.
- Sleep in your bed to start a new day and regrow apples on trees.
- Your pet will follow you and sometimes display random messages.
- Use the AI chat (TAB) to ask for help or tips in English.

---

## Installation

### Requirements

- Python 3.8+(best in 3.11)
- [Pygame](https://www.pygame.org/) (`pip install pygame`)
- (Optional for editing map) [Tiled](https://www.mapeditor.org/)
- (Optional for AI chat) [requests](https://pypi.org/project/requests/) (`pip install requests`)
- (Optional for AI chat) A local LLM API server (e.g., [LM Studio](https://lmstudio.ai/))
- Using model openai/gpt-oss-20b and host in http://localhost:1234

### Running the Game

1. **Clone this repository:**
    ```sh
    git clone https://github.com/yourusername/farming-land.git
    cd farming-land/code
    ```

2. **Install dependencies:**
    ```sh
    pip install pygame requests
    ```

3. **(Optional) Start your local LLM API server** if you want to use the AI chat feature.

4. **Run the game:**
    ```sh
    python main.py
    ```

---

## Project Structure

```
.vscode/           # VSCode settings
audio/             # Sound effects and music
code/              # All Python source code
data/              # Tiled map and tilesets
font/              # Custom font(s)
graphics/          # Game graphics (sprites, tiles, etc.)
```

- Main entry point: `code/main.py`
- Game logic: `code/level.py`, `code/player.py`, `code/soil.py`, etc.
- Menus and UI: `code/start.py`, `code/menu.py`, `code/overlay.py`
- AI Chat: `code/chat.py`
- Save/Load: `code/save.py`
- Save in :`data/save.json`

---

## AI Chat Feature

The in-game chatbox (TAB) connects to a local LLM API (default: `http://localhost:1234/v1/chat/completions`). You can use [LM Studio](https://lmstudio.ai/) or any compatible OpenAI API server. If not available, the chatbox will show an error message but the rest of the game works fine.

---

## Credits

- **Programming & Art:** Your Name
- **Music:** [tallbeard.itch.io/music-loop-bundle](https://tallbeard.itch.io/music-loop-bundle)
- **Character Sprites:** [httpsarks.itch.iodino-characters](https://harks.itch.io/dino-characters)
- **Font:** LycheeSoda.ttf

---

## License

This project is for educational and personal use. Please do not redistribute commercial assets.

---

## Screenshots

*(Add screenshots here if desired)*

---

Enjoy farming!
