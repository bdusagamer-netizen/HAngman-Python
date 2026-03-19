import random, requests, sys, time, threading, re, json, os

# Color codes
GREEN = "\033[92m"
YELLOW = "\033[93m"
RESET = "\033[0m"
RESTART = "RESTART"

# Global storage
word_sets = {"Original Set": []}
current_set_id = "Original Set"
forced_word = None
cmd_output = "" # Buffer for the area below the game

def clear():
    os.system('cls' if os.name == 'nt' else 'clear')

def loading_spinner(stop_event):
    spinner = ["|", "/", "-", "\\"]
    idx = 0
    while not stop_event.is_set():
        sys.stdout.write(f"\rFetching dictionary {spinner[idx % 4]} ")
        sys.stdout.flush()
        idx += 1
        time.sleep(0.1)
    sys.stdout.write("\r" + " " * 30 + "\r")

def fetch_original_set():
    url = "https://cdn.jsdelivr.net/gh/dariusk/corpora@master/data/words/common.json"
    stop_spinner = threading.Event()
    spinner_thread = threading.Thread(target=loading_spinner, args=(stop_spinner,))
    spinner_thread.start()
    try:
        response = requests.get(url, timeout=5)
        data = response.json()
        word_sets["Original Set"] = [w.lower().strip() for w in data["commonWords"] if len(w) > 3]
    except:
        word_sets["Original Set"] = ["offline", "python", "logic", "machine"]
    finally:
        stop_spinner.set()
        spinner_thread.join()

def parse_args(cmd_str):
    pairs = re.findall(r"(\w+)\s*=\s*([^ ]*)", cmd_str)
    return {k: v for k, v in pairs}

def handle_game_commands(user_input, current_game_state):
    global forced_word, cmd_output
    args = parse_args(user_input)
    if "/game terminate" in user_input:
        sys.exit()
    elif "/game stageset" in user_input:
        val = args.get("value")
        if val and val.isdigit():
            new_tries = int(val)
            if 0 <= new_tries <= 6:
                current_game_state["tries"] = new_tries
                cmd_output = f"Set remaining tries to: {new_tries}"
    elif "/game newround" in user_input:
        return RESTART
    elif "/game setword" in user_input:
        word = args.get("word")
        if word:
            forced_word = word.lower().strip()
            cmd_output = f"Word override set for next round."
            return RESTART
    return None

def handle_set_commands(user_input):
    global current_set_id, cmd_output
    args = parse_args(user_input)
    if "/set listall" in user_input:
        sets = [f"{n} ({len(w)})" for n, w in word_sets.items()]
        cmd_output = f"Available: {', '.join(sets)}"
    elif "/set play" in user_input:
        sid = args.get("id")
        if sid in word_sets:
            current_set_id = sid
            cmd_output = f"Switched to set: {sid}"
            return RESTART
    return None

def play_game():
    global current_set_id, forced_word, cmd_output
    
    if forced_word:
        word, forced_word = forced_word, None
    elif not word_sets.get(current_set_id):
        current_set_id = "Original Set"
        word = random.choice(word_sets[current_set_id])
    else:
        word = random.choice(word_sets[current_set_id]).lower()

    guessed_letters = []
    state = {"tries": 6}
    stages = [
        "+---+\n |   |\n O   |\n/|\\  |\n/ \\  |\n     |\n=========",
        "+---+\n |   |\n O   |\n/|\\  |\n/    |\n     |\n=========",
        "+---+\n |   |\n O   |\n/|\\  |\n     |\n     |\n=========",
        "+---+\n |   |\n O   |\n/|   |\n     |\n     |\n=========",
        "+---+\n |   |\n O   |\n |   |\n     |\n     |\n=========",
        "+---+\n |   |\n O   |\n     |\n     |\n     |\n=========",
        "+---+\n |   |\n     |\n     |\n     |\n     |\n========="
    ]

    while state["tries"] > 0:
        clear()
        print(stages[state["tries"]])
        
        display_list = []
        for l in word:
            if l in guessed_letters:
                display_list.append(f"{GREEN}{l}{RESET}")
            else:
                display_list.append("_")
        
        print(f"\n{' '.join(display_list)} (Set: {current_set_id})")
        print(f"Guessed: {', '.join(guessed_letters)}")

        if "_" not in [d for d in display_list if d == "_"]:
            clear()
            print(stages[state["tries"]])
            print(f"\n{GREEN}Congrats! You won! The word was: {word}{RESET}")
            cmd_output = ""
            return True

        # Input and Command Output Area
        u_input = input(f"\n{YELLOW}[LOGS]: {cmd_output}{RESET}\nGuess or command: ").strip()
        cmd_output = "" # Reset after display

        if u_input.startswith("/set"):
            if handle_set_commands(u_input) == RESTART: return RESTART
            continue
        elif u_input.startswith("/game"):
            if handle_game_commands(u_input, state) == RESTART: return RESTART
            continue

        guess = u_input.lower()
        if len(guess) != 1 or not guess.isalpha() or guess in guessed_letters:
            if guess in guessed_letters: cmd_output = f"'{guess}' already used."
            continue
            
        guessed_letters.append(guess)
        if guess not in word:
            state["tries"] -= 1
            cmd_output = f"'{guess}' is incorrect."
        else:
            cmd_output = f"Found '{guess}'!"

    clear()
    print(stages[0])
    print(f"Game Over! The word was: {word}")
    return False

def main():
    fetch_original_set()
    streak = 0
    while True:
        result = play_game()
        if result == RESTART: continue
        streak = streak + 1 if result else 0
        print(f"Current Streak: {streak}")
        if input("\nPlay again? (y/n): ").lower() != 'y': break

if __name__ == "__main__":
    main()
